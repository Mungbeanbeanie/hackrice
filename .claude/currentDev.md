## Status: Active — provision Vultr Managed Postgres

## Task
- Last remaining infra item; everything else in `deploy/README.md` is done.
- Verified 2026-09-11 via `gh`: `DEPLOY_ENABLED=true`; `production` + `staging` environments hold only `SSH_HOST`/`SSH_USER`/`SSH_KEY` — no `DATABASE_URL` in either.
- Staging box deployed and serving (`deploy` job green, smoke test passes). Production box provisioned, never deployed to — `DEPLOY_ENABLED` was set after the last `main` push.

## Plan
1. Vultr → Databases → Managed Postgres. Same region as the two compute instances.
2. Create `hackrice_prod` + `hackrice_staging` databases. Per-env users, `REVOKE CONNECT ... FROM PUBLIC`, staging capped at 5 connections — SQL is written out in `deploy/README.md` §1.
3. Add both instance IPs to the cluster's Trusted Sources, or connections hang rather than error.
4. Add `DATABASE_URL` secret (that env's user, not cluster admin) to each GitHub Environment.
5. Push a throwaway commit to `main` — production's first deploy. Do it before it matters.

## Open decisions
- Cache (`plan.md` Phase 2 `cache.py`): Vultr Managed Caching (Valkey) vs a table in the Postgres cluster. Postgres = zero new infra, one secret; Valkey = second service, second trusted-sources list, `CACHE_URL` plumbed through `ci.yml` + `docker-compose.yml`.
- Google sign-in: ~30 lines + `google-auth`, verify ID token, key user rows on `sub`. Blocked on domain + TLS — `SITE_ADDRESS` unset in both envs, Google rejects bare-IP origins.
- Email capture for traction evidence: gate behind a post-search action, not a signup wall.

## Next-session notes
- No ORM, no migration tool, no data model yet. First table = add Alembic, and `docker compose run --rm api alembic upgrade head` goes between `pull` and `up -d` in the deploy job (`deploy/README.md` §6).
- `backend/app/main.py` reads `DATABASE_URL` but nothing consumes it — that is where the engine gets built.
