# Architecture

File structure, component ownership, and dependency graph. Responsibility text for each file lives in `plan.md` — not duplicated here.

## Tree

Everything below exists. Phase numbers refer to `plan.md`.

```
backend/                   FastAPI service, uv-managed, Python 3.14
  app/
    __init__.py
    main.py                app instance, /api/health, reads DATABASE_URL   [Phase 0]
  tests/
    test_smoke.py
  Dockerfile               uv sync --locked --no-dev, runs uvicorn as nobody
  pyproject.toml           deps + ruff / mypy / pytest config
  uv.lock

frontend/                  Vite + React + TypeScript
  src/
    main.tsx               React root
    App.tsx                placeholder shell, fetches /api/health          [Phase 0]
    App.test.tsx
  Caddyfile                binds {$SITE_ADDRESS::80}, /api/* → api:8000, SPA fallback
  Dockerfile               node build stage → caddy:2-alpine serving /srv
  vite.config.ts, tsconfig.json, eslint.config.js

deploy/
  docker-compose.yml       api + web services, runs on each Vultr box      [Phase 0]
  README.md                provisioning runbook + current infra status     [Phase 0]

.github/workflows/
  ci.yml                   check → build → push GHCR → ssh deploy → smoke test

.claude/                   project memory — see CLAUDE.md for which file owns what
```

## Runtime graph

```
                    browser
                       │ :80 (:443 once a domain exists)
                       ▼
              web  (Caddy, frontend/Dockerfile)
                       │
        ┌──────────────┴──────────────┐
        │ /api/*                      │ everything else
        ▼                             ▼
  api (uvicorn :8000)            /srv static SPA
        │
        │ DATABASE_URL  (plumbed, unread — no data model yet)
        ▼
  Vultr Managed Postgres  ← NOT CREATED YET
```

Only `web` publishes ports. `api` is reachable solely over the compose network,
which is why the firewall group has no rule for 8000 and does not need one.

## Deploy graph

```
push dev  ──▶ ci.yml ──▶ ghcr.io/mungbeanbeanie/hackrice-{api,web}:<sha> ──▶ staging box
push main ──▶ ci.yml ──▶ same images ────────────────────────────────────▶ production box
```

Images are tagged with the commit SHA, so the `IMAGE_TAG` line in the box's
`.env` is the single thing deciding which version runs. `.env` is rewritten from
GitHub Environment secrets on every deploy, so the server is never the only
place a setting lives.

## Not yet built

Phases 1–7 of `plan.md` add `config.py`, `models.py`, `ingestion/`, `features/`,
`scoring/` and `routes/` under `backend/app/`, plus `api/` and `components/`
under `frontend/src/`. Nothing in the tree above depends on them, so they can
land in any order the phase dependencies allow.

Two structural decisions are still open and will change this file when made:

- **Cache layer** (`backend/app/cache.py`, Phase 2) — a Vultr Managed Caching
  (Valkey) instance, or a table in the Postgres cluster already being created.
- **Auth** — if Google sign-in lands it adds a user table and a token-verify
  dependency in `backend/app/`, and is blocked on a domain + TLS first, since
  Google rejects bare-IP OAuth origins.
