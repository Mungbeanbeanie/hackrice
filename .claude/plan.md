# Build Plan

Checklist, worked top-to-bottom. Each item is exactly one file with a single responsibility — `stage`/`apply` should be able to touch one checklist item without needing to also change any other file. Phases are ordered by dependency (later phases consume earlier ones).

Mission: implement the financial optimization product comparison pipeline described in `overview.md` on top of the existing FastAPI + Vite/React skeleton.

## Phase 0: Foundation (done)
- [x] `backend/app/main.py` — FastAPI app instance, `/api/health` route
- [x] `frontend/src/App.tsx` — placeholder shell, pings `/api/health`
- [x] `deploy/docker-compose.yml` — api/web services, Caddy TLS, healthcheck
- [x] `deploy/README.md` — deploy env/secrets documentation

## Phase 1: Config & Models
- [x] `backend/app/config.py` — env-driven settings (SerpAPI key, Vultr cache connection, `m=25`, `C=4.0` defaults, category weight defaults)
- [x] `backend/app/models.py` — Pydantic schemas: `SearchMode` enum (`url` / `exact_product` / `description`), `Product`, `SearchQuery` (carries `mode` + raw input), `SpecAttribute`, `ComparisonResult`, `Tier`

## Phase 2: Data Ingestion
- [x] `backend/app/ingestion/serpapi_client.py` — SerpAPI Google Shopping request wrapper, raw JSON → `Product` parsing (used for candidate search in all modes, and target lookup in `exact_product`/`url` modes)
- [x] `backend/app/ingestion/target_resolver.py` — resolves the target reference product per `SearchQuery.mode`: `url` and `exact_product` modes both route through `serpapi_client.search_products()` (`url` mode extracts identifying text from the pasted URL first — **temporary**: no direct-scrape/product-page lookup yet, revisit if time permits since it's less precise than matching the exact listing), `description` mode returns `None`. Depends on `serpapi_client.py` — build that first.
- [x] `backend/app/cache.py` — Vultr-backed cache layer (get/set search responses and embeddings by query hash)

## Phase 3: Feature Engineering
- [x] `backend/app/features/embeddings.py` — `text-embedding-3-small` wrapper for title/spec text and raw query text (`description` mode)
- [x] `backend/app/features/attribute_matrix.py` — builds the product-attribute matrix $A$ from raw specs + embeddings
- [x] `backend/app/features/svd.py` — Layer 1: SVD decomposition of $A$, latent projection, cosine similarity between reference vector (target product, or embedded query in `description` mode) and each candidate
- [x] `backend/app/features/standardize.py` — Layer 2: per-category z-score standardization + diagonal weight matrix $\mathbf{W}$

## Phase 4: Scoring
- [x] `backend/app/scoring/quality.py` — Layer 3: Bayesian quality estimator $Q$
- [x] `backend/app/scoring/value.py` — Layer 4: value optimization score $V$, tier assignment (1/2/3)

## Phase 5: API
- [x] `backend/app/routes/search.py` — `POST /api/search`, **infers** the mode from the raw input (the UI is a single search box and sends no `mode`; `SearchQuery.mode` is backend-derived), then branches on it (resolve target or skip), orchestrates ingestion → features → scoring, returns tiered results (target product omitted from response in `description` mode). Response shape must match `frontend/src/api/client.ts`'s `SearchResponse` (`{ query, targetProduct, tiers: { tier1, tier2, tier3 } }`) or add the adapter there.
- [x] `backend/app/routes/compare.py` — `GET /api/compare/{id}`, stub only (`501`) — `SpecBreakdownModal.tsx` computes spec comparison client-side, nothing calls this endpoint
- [x] `backend/app/main.py` — wire `search`/`compare` routers into the existing app (extends Phase 0 file)

## Phase 6: Frontend
Ported from the Figma draft (`frontend/Design nectarly web app/`, since deleted). Live fetch only — no mock data; searches show an error panel until Phase 5 lands.
- [x] `frontend/src/index.css` — Tailwind v4 entrypoint, honey palette `@theme`, keyframes, `.glass-card` / `.honey-shadow` / `.tier-N-glow`
- [x] `frontend/src/api/client.ts` — typed fetch wrapper for `/api/search` and `/api/compare/{id}`. Sends `{ query }` only — no `mode`, the backend infers it. Response types are provisional and UI-shaped; Phase 5 settles the contract.
- [x] `frontend/src/components/HoneyDrop.tsx` — pixel-art mascot/logo mark
- [x] `frontend/src/components/SearchBar.tsx` — single query input + submit; any non-empty string is valid
- [x] `frontend/src/components/TargetProductCard.tsx` — target reference product header; rendered only when the response carries a `targetProduct`
- [x] `frontend/src/components/AlternativeTierList.tsx` — renders Tier 1/2/3 result sections
- [x] `frontend/src/components/SpecBreakdownModal.tsx` — "Compare Spec Breakdown" detail view
- [x] `frontend/src/App.tsx` — wires the search flow + components, idle/loading/results/error states; gates `TargetProductCard` on `targetProduct !== null` (extends Phase 0 file)
- ~~`frontend/src/components/SearchModeSelector.tsx`~~ — dropped: one search box, backend infers url / exact_product / description

## Phase 7: Tests
- [x] `backend/tests/test_ingestion.py` — edge-case/runtime-safety tests for `serpapi_client.py` (missing key, wrapped network-timeout error, malformed response parsing) — not originally scoped, added to cover the timeout/error-wrapping fix
- [x] `backend/tests/test_scoring.py` — edge-case/runtime-safety tests for `quality.py`/`value.py` (zero reviews, zero-denominator division, zero price, empty input, below-quality-threshold filtering, mismatched score dicts) — not $Q$/$V$ formula correctness, per instruction to test runtime safety, not efficacy. Two real crash bugs found and fixed alongside: `compute_quality` could `ZeroDivisionError` if `BAYESIAN_M=0`; `rank_candidates` could `KeyError` if a product were missing from any score dict.
- [x] `backend/tests/test_pipeline.py` — integration test of `/api/search` via `TestClient`, with `serpapi_client`/`target_resolver`/`embeddings` mocked — no-candidates branch, target-not-found 404, full pipeline run without raising on mocked realistic input 
- [x] `backend/tests/test_accounts.py` — edge-case/runtime-safety tests for `session.py`/`mailer.py`/`db.py` (missing-config `RuntimeError`s, malformed/tampered/expired session tokens, wrapped Resend network failure) — `store.py` not unit-tested directly (needs a real Postgres connection), exercised instead via the route-level mocks below
- [x] `backend/tests/test_auth_routes.py` — integration tests for all three `/api/auth/*` routes via `TestClient`, with `verification`/`mailer`/`store`/`session` mocked — success + 401/502 paths for `request-code`, `verify`, `me`

## Phase 8: Accounts
Email-based account creation (overview.md §6.1) — verification code, not password. No frontend UI yet (backend API only); login form is a separate later stage. Blocked on the Vultr Managed Postgres cluster actually being provisioned (deploy/README.md §1 "Remaining") — code is written against DATABASE_URL regardless, but cannot run until then.
- [x] `backend/app/config.py` — add `DATABASE_URL` (moved here from `main.py`, where it's currently unused dead code), `RESEND_API_KEY`, `SESSION_SECRET` (HMAC signing key for session cookies)
- [x] `backend/app/models.py` — add `Account` schema: `id`, `email`, `created_at`
- [x] `backend/app/db.py` — Postgres connection pool (`psycopg` + `psycopg_pool.ConnectionPool`, sync — matches the rest of the codebase's sync style, no async elsewhere; a bare shared connection isn't thread-safe under FastAPI's threadpool-per-request model) + idempotent schema bootstrap (`CREATE TABLE IF NOT EXISTS accounts`/`verification_codes` on startup) — no migration framework yet, per `deploy/README.md` §6's "wire it in when the first table lands" note; this *is* that first table
- [x] `backend/app/accounts/store.py` — DB access: get-or-create account by email (atomic, race-safe), get account by id, store/consume verification codes (raw SQL via `db.py`'s pool)
- [x] `backend/app/accounts/verification.py` — generate a random numeric code + expiry, hashed (SHA-256) before ever reaching storage, verify a submitted code against what's stored (via `store.py`)
- [x] `backend/app/accounts/session.py` — sign/verify a session token (HMAC-SHA256 over account id + expiry, using `config.SESSION_SECRET`, constant-time signature compare); issue/read the httponly cookie (`SESSION_COOKIE_SECURE` defaults false — no domain/TLS on either deploy box yet)
- [x] `backend/app/accounts/mailer.py` — Resend API wrapper (plain REST via `httpx`, no new SDK dependency), sends the verification code by email
- [x] `backend/app/routes/auth.py` — `POST /api/auth/request-code` (email → generates+emails a code, always 200 regardless of whether the account exists yet, to avoid leaking which emails are registered), `POST /api/auth/verify` (email+code → verifies, creates the account row on first success, issues the session cookie), `GET /api/auth/me` (reads the session cookie → current account or 401) — `RuntimeError`s (missing config/upstream failure) map to 502, matching `routes/search.py`'s convention
- [x] `backend/app/main.py` — wire `auth.router` in, run `db.py`'s schema bootstrap on startup (extends Phase 0 file) — bootstrap failure (e.g. `DATABASE_URL` unset) is caught and logged, not crashed on, so `/api/health`/`/api/search` stay up even if accounts aren't ready

## Phase 9: Coupons
Best-active-coupon lookup by retailer, via CouponAPI.org (no retailer status required — confirmed directly against their site; $49-66/mo, 7-day free trial). Frontend display trigger/UI is out of scope for this phase (handled separately later) — backend lookup capability only.

**Open question to resolve first:** is this a live per-request API or a bulk feed synced into our own DB on a schedule? Their pricing language ("daily syncs," "store changes") suggests the latter, which would need a scheduled sync job + local Postgres table instead of a live client call — a different shape than the checklist below assumes. Confirm via real docs (blocked — see below) before treating `client.py`'s design as settled.

- [ ] `backend/app/config.py` — add `COUPON_API_KEY` (exact env var name, and whether additional credentials like a publisher/affiliate ID are also required, pending real docs)
- [ ] `backend/app/coupons/models.py` — normalized internal `CouponOffer` model (code, discount description, store, expires_at, verified_at) — insulates the rest of the app from CouponAPI.org's actual raw schema
- [ ] `backend/app/coupons/client.py` — CouponAPI.org integration, shape TBD pending the live-vs-feed-sync question above; maps raw data to `CouponOffer`. **Blocked** — endpoint URL/auth/response field names are not publicly documented (checked; behind a signed-in knowledgebase); cannot be implemented until the user has real API access and shares the actual spec. Store-name matching between `Product.vendor` and CouponAPI.org's store taxonomy also needs solving here.
- [ ] `backend/app/coupons/selector.py` — given a store's `CouponOffer`s, return the single best currently-active one: filter `expires_at` in the past; ranking the rest is not a simple discount-amount sort (see flagged gap above) — likely "most recently verified" as primary signal, discount-magnitude parsing as a secondary refinement if it proves reliable enough. Depends only on the normalized model, buildable regardless of the `client.py` blocker.
- [ ] `backend/app/routes/coupons.py` — `GET /api/coupons?store={name}`, looks up the best active coupon for a retailer on demand. Should cache per-store results (via `cache.py`) regardless of whether the underlying model is live-API or local-DB, to avoid redundant paid lookups/queries for popular retailers.
- [ ] `backend/app/main.py` — wire `coupons.router` in (extends Phase 0 file)
