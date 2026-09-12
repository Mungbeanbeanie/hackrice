# Branch Dependency Changes

Tracks every dependency add/remove/bump made on the current branch that hasn't
gone through CI/CD to `dev`/`main` yet. Update this in the same `stage` as any
change to `backend/pyproject.toml`, `backend/uv.lock`, `frontend/package.json`,
or `frontend/package-lock.json` — so it's easy to spot what's new before this
branch merges into a tested/prod pipeline.

## Pending (not yet merged)

| Date | File | Change | Reason |
|------|------|--------|--------|
| 2026-09-12 | backend/pyproject.toml | + `psycopg[binary]>=3.1` | Phase 8 accounts — Postgres connection (`db.py`) |
| 2026-09-12 | backend/pyproject.toml | + `psycopg-pool>=3.2` | Phase 8 accounts — connection pooling (`db.py`) |
| 2026-09-12 | frontend/package.json | + `lucide-react@^1.45.0` | Organic redesign — icon set mandated by design handoff (stroke-width 2.75) |
| 2026-09-12 | extension/package.json (new file) | + `esbuild@^0.28.0`, `typescript@^5.0.0`, `vitest@^5.0.0`, `@types/chrome@^0.0.280` | Phase 14 browser extension — build/typecheck/test tooling for the new `extension/` package. Not yet covered by `instructions.md`'s Dependency Rule (which names only backend/frontend files) — logged here anyway in the rule's spirit; pending user decision on whether to extend the rule's file list. |

## Merged

(move a row here once its branch has landed in `dev`/`main`, or clear the table after a merge — whichever the user prefers going forward)
