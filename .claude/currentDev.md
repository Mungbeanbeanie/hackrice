## Status: Staged — Phase 6 manual end-to-end smoke test

## Task
- Run the *compiled `peacode` binary's own* `/stage` then `/apply` commands against a trivial scratch file, exercising the real pipeline end-to-end.
- Confirmed prereq NOT met yet: `llama-server` not reachable at `127.0.0.1:8080` (checked 2026-07-15, `curl :8080/health` → connection refused). User starts this manually — harness/session never auto-launches it.
- `.peacode/architecture.json` does not exist yet in this repo (only `.peacode/cache/` present) — first `/stage` call against it will hit the "no entry for target-file" warning path in Target Responsibility Lookup. Expected, not a bug — confirm the warning fires visibly rather than silently.

## Plan
1. User starts `llama-server` (System Launch Config in `overview.md`), confirms up.
2. `./target/debug/peacode /stage scratch/hello.rs "create pub fn hello() -> &'static str returning \"phase 6 smoke test\""`
   - Verify: `.peacode/current_task.json` written, validates against `TaskBlueprint` schema.
   - Verify: rendered instruction/plan view is correct (peacode's own render target `.peacode/currentDev.md` for whatever project it's pointed at — distinct from this session's `.claude/currentDev.md`).
   - Verify: visible warning for missing `architecture.json` entry, no crash.
   - Verify: import graph / AST snip / LRU tracker run cleanly even with an empty/near-empty dependency graph.
3. `./target/debug/peacode /apply scratch/hello.rs`
   - Verify: backup circuit breaker handles "file doesn't exist yet" case (no bytes to snapshot) without erroring.
   - Verify: `EditPlan` returned is create-with-content (`old_string: null`), single op.
   - Verify: `Pre-Write Path Guard` passes `scratch/hello.rs` (not on protected blocklist, resolves inside project root).
   - Verify: post-write compiler check (`cargo check`) runs and passes.
   - Verify: on pass, backup discarded.
   - Verify: `plan.json`/`plan.md` auto-check-off logic — `scratch/hello.rs` has no matching entry in `plan.json`; confirm `plan_tracker::mark_done` no-ops gracefully rather than erroring (edge case not explicitly speced — flag if it breaks).
4. Decide + confirm with user: keep `scratch/hello.rs` as a permanent fixture or delete after test — not yet in `.gitignore` or `architecture.json`.

## Next-session notes
- If Phase 6 surfaces a real bug, fix it as a normal one-file stage/apply cycle (see memory: `feedback-discipline-drives-quality`).
- Once Phase 6 passes, PeaCode is feature-complete per its own build plan — next decision is what to point it at long-term and whether `overview.md` needs new commands/components.
