## Code Editing Rules
- Preserve all existing comments exactly (no edits/removals) unless explicitly instructed.
- Keep comments in place when modifying/rewriting code.
- If comments become inaccurate, flag and defer updates to the user.

## Memory Rules
- All project memory lives in `.claude/` only. No new `.md` files without user approval. Use `overview.md` for source of truth, `plan.md` for build status and checklist, `architecture.md` for file structure, `currentDev.md` for active tasks, `branchDep.md` for pending dependency changes.

## Dependency Rules
- CI/CD pipeline is sensitive to dependency changes on a branch before it merges to test/prod. Any add/remove/bump to `backend/pyproject.toml`/`uv.lock` or `frontend/package.json`/`package-lock.json` must be logged as a row in `branchDep.md` (date, file, change, reason) in the same `stage` that makes the change — not after the fact.

## Keyword Rules
-  `stage` is keyword for the plan for the next change (either code or file diff) to be written to currentDev.md
- `apply` is keyword for the plan written in currentDev.md to be implemented as stated, can still ask questions if you think implementation needs to be altered

## currentDev.md Rules
- Use terse bullets only; no prose or explanations.
- Include only task-critical info; no redundancy or extra context. but should include all logic planned for implementation
- task complete = IMMEDIATELY overwrite currentDev.md with: "## Status: Clear\nNo active task." do not wait. do not ask. overwrite on completion regardless of test status.
