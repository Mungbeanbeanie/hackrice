## Status: Staged
## Task: Phase 15, item 10 (last, optional) — CI extension packaging job

### `.github/workflows/ci.yml`
- add a new top-level job `extension`, parallel to `backend`/`frontend` (not added to `deploy`'s `needs: [backend, frontend]` — does not touch deploy gating)
- `runs-on: ubuntu-latest`, `defaults.run.working-directory: extension`
- steps, mirroring the `frontend` job's shape:
  - `actions/checkout@v7`
  - `actions/setup-node@v7` (`node-version: 24`, `cache: npm`, `cache-dependency-path: extension/package-lock.json`)
  - `npm ci`
  - Typecheck: `npm run typecheck`
  - Test: `npm run test`
  - Build: `npm run build` (uses localhost defaults in CI — no `EXTENSION_API_BASE_URL`/`EXTENSION_WEBAPP_URL` secrets exist or are needed for a packaging check)
  - Package: zip the built extension dir (manifest.json, content.js, background.js, icons/) into `extension.zip`, excluding source/dev files (`node_modules`, `src/`, `*.ts`, `build.mjs`, `manifest.template.json`, `package*.json`, `tsconfig.json`, `vitest.config.ts`)
  - `actions/upload-artifact@v4` — `name: nectarly-extension`, `path: extension/extension.zip`
- runs on every push/PR to `dev`/`main` (same `on:` trigger as the rest of the workflow — no new trigger block needed)
- no `branchDep.md` row — no dependency change, CI-only

### Verification
- workflow YAML is valid (`actions/setup-node`, `actions/upload-artifact` versions exist)
- job is independent of `deploy` — a failing `extension` job does not block `deploy` unless explicitly added to its `needs` (deliberately not added, per plan.md's "does not touch the deploy job's gating logic")
