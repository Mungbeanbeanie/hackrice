# hackrice

## Layout

```
backend/     Python 3.14 — uv, ruff, mypy, pytest
frontend/    TypeScript  — npm, eslint, vitest, tsc
.github/workflows/ci.yml
```

## Running the checks locally

CI runs exactly these commands and nothing else. If they pass here, they pass there.

```sh
# backend
cd backend
uv sync --locked --all-extras --dev
uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run pytest

# frontend
cd frontend
npm ci
npm run lint && npm run typecheck && npm run test && npm run build
```

The frontend CI job calls `package.json` script names, never tools directly — so
swapping in Vite/Next or a different test runner means editing `package.json`,
not the workflow.

## Branches

`feature/* → dev → main`. `main` is what deploys.

Nothing is enforced yet: CI reports on every PR but does not block merges. To turn
that on, add a ruleset under **Settings → Rules** targeting `main` and `dev` that
requires a PR and requires the `backend` and `frontend` checks to pass.

## Not set up yet

- **Deploy.** No target chosen, so there is no deploy workflow. The frontend is a
  placeholder (`tsc` stands in for a real bundler build) until a framework is picked.
- The `health()` function on each side exists only so CI has something real to
  check. Delete both once actual code lands.
