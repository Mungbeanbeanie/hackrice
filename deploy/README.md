# Deploy runbook

Two Vultr Cloud Compute instances (production + staging) running Docker Compose,
fronted by Caddy, with a Vultr Managed Postgres cluster behind them.

`main` deploys to production, `dev` deploys to staging. Both go through the
`deploy` job in [`../.github/workflows/ci.yml`](../.github/workflows/ci.yml),
which only runs after the `backend` and `frontend` check jobs pass.

Nothing below is automated. It is a one-time setup per box, done by hand — a
Terraform module to manage two VPSes would be more code to maintain than the
thing it manages.

---

## Status

Done:

- Both Cloud Compute instances, with the firewall group attached (step 1)
- Docker, the `deploy` user and SSH hardening on each box (step 2)
- Both GitHub Environments, each holding `SSH_HOST` / `SSH_USER` / `SSH_KEY` /
  `DATABASE_URL` (step 3)
- `DEPLOY_ENABLED=true` — deploys are live, and staging has taken several
- The `cache` service (Valkey) in [`docker-compose.yml`](docker-compose.yml) —
  no provisioning, no secret, no firewall rule: it runs on the box beside `api`
  and is reachable only over the compose network. Nothing to do per-environment:
  `CACHE_URL` defaults to `redis://cache:6379` in the compose file.

Remaining:

- `SERPAPI_API_KEY` and `OPENAI_API_KEY` in each GitHub Environment (step 3).
  Neither is set, so every deploy writes them into `.env` as empty strings and
  search fails on the box until they exist.
- The per-environment Postgres users and the staging connection limit (step 1) —
  the cluster and a `DATABASE_URL` per environment exist, but whether that URL
  uses a per-environment user or the cluster admin has not been checked.
- A domain — `SITE_ADDRESS` is unset in both environments, so both boxes serve
  plain HTTP on their bare IP (step 4)

**Production has never received a deploy.** `DEPLOY_ENABLED` was turned on after
the most recent push to `main`, so only the staging box has containers on it.
The first merge to `main` will be production's first deploy — worth triggering
deliberately rather than discovering it under time pressure.

---

## 1. Provision

**Two Cloud Compute instances**, one per environment:

- Current Ubuntu LTS, smallest plan that fits (the $6–12/mo tier is plenty to start)
- Same region as the database, so traffic stays on Vultr's internal network
- Note each instance's public IP

**One Managed Postgres cluster.** You can point both environments at one cluster
with two separate databases (`hackrice_prod`, `hackrice_staging`) to halve the
cost, or run two clusters for real isolation. Two databases on one cluster is
fine early; split them before staging traffic can plausibly affect production.

One cluster shares CPU, RAM, disk, the connection limit, the maintenance window
and the backup schedule. The data is isolated; the resources are not. Two
consequences worth knowing before you rely on it:

- A runaway staging query can starve production of connections. This is the
  failure you will actually hit, not data leakage.
- Version upgrades and restarts hit both environments at once, so you cannot
  test a Postgres upgrade on staging first.

Give each environment its own user rather than sharing the cluster admin, and
cap staging so it cannot exhaust the pool. Run this once as the admin user:

```sql
-- PUBLIC holds CONNECT on every database by default, so revoking from PUBLIC
-- is the control that actually does something. Revoking from a named user
-- while PUBLIC still grants it accomplishes nothing.
REVOKE CONNECT ON DATABASE hackrice_prod    FROM PUBLIC;
REVOKE CONNECT ON DATABASE hackrice_staging FROM PUBLIC;

CREATE USER hackrice_prod_app    WITH PASSWORD '<generate one>';
CREATE USER hackrice_staging_app WITH PASSWORD '<generate one>';

GRANT CONNECT ON DATABASE hackrice_prod    TO hackrice_prod_app;
GRANT CONNECT ON DATABASE hackrice_staging TO hackrice_staging_app;

-- Staging cannot take more than 5 of the cluster's connections.
ALTER USER hackrice_staging_app CONNECTION LIMIT 5;
```

Then, connected to each database in turn, give its own user rights inside it:

```sql
GRANT ALL ON SCHEMA public TO hackrice_prod_app;     -- while in hackrice_prod
GRANT ALL ON SCHEMA public TO hackrice_staging_app;  -- while in hackrice_staging
```

The `DATABASE_URL` for each environment should use that environment's user, not
the cluster admin. Connecting to the wrong database then fails outright instead
of quietly succeeding against production.

**Firewall group** (Vultr → Network → Firewall), attached to both instances.
Add all three rules to **both** the IPv4 and IPv6 tabs — Vultr evaluates the two
families separately and default-denies anything unmatched, so v6-only rules
going missing is a silent failure later when AAAA records appear.

| Port | Source | Why |
|------|--------|-----|
| 22 | `0.0.0.0/0` and `::/0` | SSH, including the deploy job |
| 80 | `0.0.0.0/0` and `::/0` | HTTP, and Let's Encrypt's HTTP-01 challenge later |
| 443 | `0.0.0.0/0` and `::/0` | HTTPS once a domain exists |

**Why port 22 is open to the world:** the deploy job SSHes in from a
GitHub-hosted runner, whose egress addresses are ~7000 rotating CIDRs
(`https://api.github.com/meta`). Allowlisting them is not practical, and
restricting 22 to your own IP breaks every deploy.

Open SSH is safe *only because the box accepts keys and nothing else* — the
hardening in step 2 is what makes this acceptable, not optional garnish. If you
later want 22 closed to the internet entirely, the move is a private network
between runner and box (Tailscale has a GitHub Action and an ephemeral-auth-key
flow), not an IP allowlist.

**Database trusted sources:** add both instance IPs to the Postgres cluster's
allowed list, or it will refuse connections.

## 2. Set up each box

SSH in as root, then:

```sh
# Docker
curl -fsSL https://get.docker.com | sh

# Unprivileged deploy user, in the docker group so compose works without sudo
adduser --disabled-password --gecos "" deploy
usermod -aG docker deploy
install -d -o deploy -g deploy -m 700 /home/deploy/.ssh
install -d -o deploy -g deploy /srv/hackrice

# Unattended security updates — this is the patching tax of not using a PaaS
apt-get update && apt-get install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

**Harden SSH.** Port 22 is open to the internet (see above), so key-only auth is
what stands between you and the background noise of the internet guessing
passwords:

```sh
# Refuse passwords and keyboard-interactive entirely; keys only.
cat > /etc/ssh/sshd_config.d/99-hackrice.conf <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
EOF
sshd -t && systemctl restart ssh

# Rate-limit what's left
apt-get install -y fail2ban
systemctl enable --now fail2ban
```

Run `sshd -t` before restarting, as above — it validates the config, and a typo
that takes sshd down on a box you can only reach by SSH is a bad afternoon.
Vultr's browser console is the way back in if that happens.

Confirm key-only auth actually took effect before moving on:

```sh
ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no deploy@<ip>
# expected: "Permission denied (publickey)."
```

Generate a **dedicated deploy keypair** locally (not your personal SSH key):

```sh
ssh-keygen -t ed25519 -f ~/.ssh/hackrice_deploy -C "github-actions-deploy" -N ""
```

Put the **public** half on each box:

```sh
ssh-copy-id -i ~/.ssh/hackrice_deploy.pub deploy@<instance-ip>
```

The **private** half goes into GitHub secrets below and nowhere else.

## 3. GitHub Environments

Settings → Environments → create **`production`** and **`staging`**. The workflow
picks between them by branch, so the job body is identical for both.

Per environment, add these **secrets**:

| Secret | Value |
|--------|-------|
| `SSH_HOST` | that environment's instance IP |
| `SSH_USER` | `deploy` |
| `SSH_KEY` | full contents of `~/.ssh/hackrice_deploy` (the private key) |
| `DATABASE_URL` | the Vultr Postgres connection string for that environment's database |
| `SERPAPI_API_KEY` | SerpAPI key. Unset writes an empty line to `.env` and every search fails with `SERPAPI_API_KEY is not set` |
| `OPENAI_API_KEY` | OpenAI key for `text-embedding-3-small` |
| `COUPON_API` | CouponAPI.org key (Phase 9, unused until `coupons/client.py` lands). Unset is harmless for now — nothing reads it yet. |

Every one of these is written into `.env` by the deploy job on each run, so a
value that exists only in a hand-edited `.env` on the box is overwritten by the
next deploy. The box is never the source of truth for config.

`CACHE_URL` is deliberately **not** in that table. It defaults to
`redis://cache:6379` in [`docker-compose.yml`](docker-compose.yml) — the `cache`
service on the compose network, the same string in every environment and not
sensitive. The deploy job still passes a `CACHE_URL` secret through if one
exists, so pointing an environment at an external Redis stays a one-secret
change; leave it unset otherwise.

And one **variable** (not a secret):

| Variable | Value |
|----------|-------|
| `SITE_ADDRESS` | leave unset for now — it defaults to `:80`, plain HTTP on the bare IP |

On `production`, also consider turning on **required reviewers** so a merge to
`main` pauses for a human before it touches the production box.

### Turning deploys on

The `deploy` job is gated on a **repository variable** (Settings → Secrets and
variables → Actions → Variables):

| Variable | Value |
|----------|-------|
| `DEPLOY_ENABLED` | `true` |

Until it is set, the job skips instead of failing against infrastructure that
does not exist. Set it only after both environments have their secrets and both
boxes are reachable over SSH. It also doubles as a kill switch: set it to
anything else to stop deploys without reverting code.

## 4. Adding the domain later

This is the only step needed to get HTTPS:

1. Point an A record at the production instance IP (and e.g. `staging.` at the staging IP).
2. Set the `SITE_ADDRESS` variable to that hostname in the matching environment.
3. Re-run the deploy.

Caddy requests and renews the certificate on its own. The `caddy_data` volume in
[`docker-compose.yml`](docker-compose.yml) persists it across restarts — without
that volume you would re-request on every deploy and hit Let's Encrypt's rate
limit within a day.

## 5. Rolling back

Every image is tagged with its commit SHA, so rollback is not a rebuild:

```sh
ssh deploy@<ip>
cd /srv/hackrice
sed -i 's/^IMAGE_TAG=.*/IMAGE_TAG=<known-good-sha>/' .env
docker compose up -d
```

Re-running an older commit's workflow from the Actions tab works too, and is
easier to audit.

## 6. Database migrations — not wired up yet

There is no ORM and no migration tool, because there is no data model. When the
first table lands, the migration step belongs in the deploy job **between**
`docker compose pull` and `docker compose up -d`:

```sh
docker compose run --rm api alembic upgrade head
```

Doing it before `up -d` means the new schema is in place before new code serves
traffic. It also means a failed migration aborts the deploy instead of leaving
containers running against a schema they do not understand.

## Known ceilings

Deliberate simplifications. Each is fine now and has an obvious upgrade when it
stops being fine:

- **`docker compose up -d` drops requests for a few seconds** while containers
  restart. Acceptable for a small app. Fix when it matters: run two `api`
  replicas and let Caddy round-robin while they restart one at a time.
- **The host key is trusted on first use** by `ssh-keyscan` in the deploy job.
  Pin it via an `SSH_KNOWN_HOSTS` secret if that path ever needs to be MITM-proof.
- **No monitoring or alerting.** Nothing tells you the box is down except a user.
  Vultr has basic instance alerts; a free Better Stack or Uptime Robot check on
  `/api/health` is ten minutes of setup.
- **No backups beyond the managed database's own.** The instances hold no state
  worth keeping — that is on purpose, and worth keeping true.
- **The API image is ~395MB.** Fine over a Vultr link. If pulls get slow, a
  multi-stage build copying only `/app/.venv` roughly halves it.
