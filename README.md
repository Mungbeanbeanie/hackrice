# hackrice

Hosted at: https://nectarly.us/

FastAPI backend, React frontend, deployed to Vultr.

## Layout

```
backend/     Python 3.14 — FastAPI, uvicorn, uv, ruff, mypy, pytest
frontend/    TypeScript  — React, Vite, eslint, vitest
deploy/      docker-compose.yml + provisioning runbook
.github/workflows/ci.yml
```

## Running locally

```sh
# backend — http://localhost:8000
cd backend && uv sync && uv run uvicorn app.main:app --reload

# frontend — http://localhost:5173, proxies /api to the backend
cd frontend && npm install && npm run dev
```

Nothing reads `.env` automatically — `app/config.py` is plain `os.getenv`, and
there is no `python-dotenv`. Export it into the shell yourself:

```sh
set -a; source .env; set +a   # from the repo root, before `uv run uvicorn`
```

The Vite dev proxy mirrors the Caddy routing used in production, so `/api` paths
behave the same in both.

This runs **without a cache**: `CACHE_URL` is unset, so every lookup in
`app/cache.py` misses and every write is dropped. Correct, just slower and it
re-pays for every embedding. To cache locally, run Valkey alongside it:

```sh
docker run -d -p 6379:6379 valkey/valkey:alpine
CACHE_URL=redis://localhost:6379 uv run uvicorn app.main:app --reload
```

To run the production stack locally instead:

```sh
docker build -t ghcr.io/mungbeanbeanie/hackrice-api:local backend
docker build -t ghcr.io/mungbeanbeanie/hackrice-web:local frontend
IMAGE_TAG=local DATABASE_URL=postgres://unused \
  docker compose -f deploy/docker-compose.yml up
```

`--env-file .env` is needed to pick the repo-root `.env` up — without it compose
resolves `.env` next to the compose file (`deploy/`), not the repo root, and
every `${VAR}` silently falls back to its default:

```sh
docker compose --env-file .env -f deploy/docker-compose.yml up
```

With the placeholder `DATABASE_URL` above, the startup schema bootstrap fails,
gets logged, and `/api/auth/*` 502s — `/api/health` and `/api/search` still work.

## Checks

CI runs exactly these. If they pass here, they pass there.

```sh
cd backend
uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run pytest

cd frontend
npm run lint && npm run typecheck && npm run test && npm run build
```

The frontend CI job calls `package.json` script names, never tools directly — so
swapping the bundler or test runner means editing `package.json`, not the workflow.

## Branches and deploys

`feature/* → dev → main`.

| Branch | Deploys to |
|--------|-----------|
| `dev` | staging instance |
| `main` | production instance |

Setup, secrets, rollback and the migration story: [deploy/README.md](deploy/README.md).

  ```sh
  docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:17-alpine
  export DATABASE_URL=postgres://postgres:dev@localhost:5432/postgres
  ```
- **The `/api/health` endpoint and the `App` shell are placeholders** that exist
  so CI and the deploy smoke test assert something real. Replace them.
