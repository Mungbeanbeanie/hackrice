# hackrice

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

Deploy runs in the same workflow as CI and `needs` both check jobs, so a failing
test blocks the deploy. Images are tagged with the commit SHA — rollback is
editing one line in `.env` on the box, not a rebuild.

Setup, secrets, rollback and the migration story: [deploy/README.md](deploy/README.md).

Branch protection is **not** enabled yet — CI reports but does not block merges.
To turn it on, add a ruleset under **Settings → Rules** targeting `main` and `dev`
requiring a PR and the `backend` and `frontend` checks.

## Not set up yet

- **No domain**, so the app serves plain HTTP on the instance IP. One variable
  and a DNS record gets HTTPS; see the runbook.
- **No database usage.** A Managed Postgres cluster is provisioned and
  `DATABASE_URL` reaches the container, but nothing reads it — there is no data
  model yet, so there is no ORM and no migration tool either.
- **The `/api/health` endpoint and the `App` shell are placeholders** that exist
  so CI and the deploy smoke test assert something real. Replace them.
