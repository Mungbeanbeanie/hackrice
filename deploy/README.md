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

## 1. Provision

**Two Cloud Compute instances**, one per environment:

- Current Ubuntu LTS, smallest plan that fits (the $6–12/mo tier is plenty to start)
- Same region as the database, so traffic stays on Vultr's internal network
- Note each instance's public IP

**One Managed Postgres cluster.** You can point both environments at one cluster
with two separate databases (`hackrice_prod`, `hackrice_staging`) to halve the
cost, or run two clusters for real isolation. Two databases on one cluster is
fine early; split them before staging traffic can plausibly affect production.

**Firewall group** (Vultr → Network → Firewall), attached to both instances:

| Port | Source | Why |
|------|--------|-----|
| 22 | your IP, ideally | SSH. Leaving this world-open is the single most common way these boxes get owned. |
| 80 | anywhere | HTTP, and Let's Encrypt's HTTP-01 challenge later |
| 443 | anywhere | HTTPS once a domain exists |

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
