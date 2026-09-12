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
Best-active-coupon lookup by retailer, backed by CouponAPI.org's periodic full CSV feed sync (confirmed via a real sample: `full_5647_20260912175001.csv`, 661 rows — filename pattern `full_<id>_<timestamp>.csv` is a scheduled snapshot dump, not a live per-request API). Architecture: an ingest step loads the feed into a local Postgres table; lookups query that table, never CouponAPI.org directly. Frontend display trigger/UI is out of scope for this phase — backend lookup capability only.

Feed columns (confirmed from the real sample): offer_id, title, description, label, code, featured, source, deeplink, affiliate_link, cashback_link, url, image_url, brand_logo, type, store, merchant_home_page, categories, standard_categories, start_date, end_date, status, primary_location, locations, language, rating. Notably: `status` is always empty (unusable), there is no `verified_at`-equivalent field, and `rating` is a small int (0-2 observed).

Open question, not blocking: how daily feed delivery gets automated (authenticated download URL vs. manual re-upload) is unconfirmed. Ingestion is built against a local CSV path; automating retrieval is follow-up work.

- [x] `backend/app/config.py` — `COUPON_API_KEY` added. Its actual use is now uncertain — no live call needs it; may end up used only if CouponAPI.org exposes an authenticated feed-download URL. Kept, not removed, pending that answer.
- [ ] `backend/app/coupons/models.py` — **needs revision**: drop `verified_at` (no feed equivalent), add `start_date: datetime | None` and `rating: int` to `CouponOffer`, matching the real feed's available ranking signals.
- [ ] `backend/app/coupons/loader.py` — **replaces the originally-planned `client.py`**. Parses the CSV feed (stdlib `csv.DictReader`) from a local file path, maps each row to `CouponOffer` (skip rows missing `store`/`title`), upserts into a `coupon_offers` Postgres table via `db.py`'s pool, keyed by `offer_id` so re-running the loader on a newer feed is idempotent (replace-on-conflict, not insert-only).
- [ ] `backend/app/db.py` — extend schema bootstrap: add `CREATE TABLE IF NOT EXISTS coupon_offers` (extends Phase 8's file further).
- [ ] `backend/app/coupons/selector.py` — given a store name, query `coupon_offers` (not an in-memory list) for that store; filter `end_date` in the past; rank by `rating` desc, then `start_date` desc as a recency tiebreak (replaces the abandoned verified_at-based design); return the single best `CouponOffer` or `None`.
- [ ] `backend/app/routes/coupons.py` — `GET /api/coupons?store={name}`, looks up via `selector.py`. Cache per-store results via `cache.py` to avoid redundant DB queries for popular retailers.
- [ ] `backend/app/main.py` — wire `coupons.router` in (extends Phase 0 file)

## Phase 10: Organic Design System (Frontend Redesign)
Ported from `frontend/design_handoff_nectarly_production/` (design reference bundle — HTML prototypes + token sheet, not production code; kept in the repo as reference, excluded from lint/typecheck/build via `eslint.config.js`/`tsconfig.json` scoping). Replaces the honey-gradient placeholder UI with the Organic design system (cream ground, terracotta + sage accents, Caprasimo/Figtree) and adds three new marketing/account surfaces. **Frontend-only pass** — see Phase 11 for the backend data-contract catch-up this depends on.
- [x] `frontend/src/index.css` — Organic `@theme` tokens (color ramps, radius, shadow, fonts), keyframes (`riseIn`/`softIn`/`bob`/`sweep`/`hopSpin`/`hopShadow`); deleted all honey-theme tokens/classes
- [x] `frontend/package.json` — `+ lucide-react` (icon set, stroke-width 2.75 per design guide)
- [x] `frontend/src/api/client.ts` — new `Product`/`SearchResponse` types (`group`/`verdict`/`rationale`/`short` fields per the handoff's data-contract section) plus a client-side adapter (`adaptSearchResponse`) that stubs those fields over the *existing* `/api/search` response (`tiers` → `groups` 1:1 mapping, `direction`-less verdict heuristic, templated rationale). Also added `requestSignInCode`/`verifySignInCode` against the existing Phase 8 `/api/auth/*` routes.
- [x] `frontend/src/components/SearchBar.tsx` — restyled; `hero`/`compact` variants for the landing page vs. app header; dropped the clear-x button (not in the design)
- [x] `frontend/src/components/TargetProductCard.tsx` — restyled to the "reference product card" spec
- [x] `frontend/src/components/ResultCard.tsx` — new; single candidate row (savings bar, match/rating chips, Compare/Buy), replaces the per-item render logic that lived in `AlternativeTierList.tsx`
- [x] `frontend/src/components/AlternativeGroups.tsx` — new; renders the three semantic groups (`same_spec`/`same_job`/`clears_floor`) in fixed equivalence order, ranked by value within each. Replaces and deletes `AlternativeTierList.tsx`.
- [x] `frontend/src/components/ComparisonTable.tsx` — new; side-by-side spec table across target + all candidates
- [x] `frontend/src/components/SpecBreakdownModal.tsx` — rewritten; verdict chips (6-value) + `rationale` paragraph, replacing the old dead-verdict-logic version
- [x] `frontend/src/components/LandingPage.tsx` — new; marketing surface (hero, three-things, extension teaser, footer)
- [x] `frontend/src/components/SignInPage.tsx` — new; wired to the real Phase 8 `/api/auth/request-code` + `/api/auth/verify` routes. **Deviation from the design handoff**, flagged to user: the mockup's copy assumes a magic-link flow ("Email me a sign-in link"), but the backend is verification-code-based — added a second code-entry step and adjusted copy accordingly.
- [x] `frontend/src/components/ExtensionPanel.tsx` — new; standalone panel only (surrounding browser-chrome mock is scaffolding, built inline in `App.tsx`'s `extension` screen)
- [x] `frontend/src/App.tsx` — rewritten; `screen` (`landing`/`app`/`signin`/`extension`) × `appState` (`idle`/`loading`/`results`/`error`) × `view` (`ranked`/`table`) state machine (extends Phase 0 file)
- [x] `frontend/eslint.config.js` — ignore `design_handoff_nectarly_production/**` (reference HTML/JS, not app code — was failing `npm run lint`)
- ~~`frontend/src/components/AlternativeTierList.tsx`~~ — deleted, replaced by `AlternativeGroups.tsx` + `ResultCard.tsx`

## Phase 11: Data Contract Backend Catch-up (not started)
What Phase 10's client-side stub (`api/client.ts`'s `adaptSearchResponse`) is standing in for. Blocks removing that adapter.
- [ ] `backend/app/models.py` — add `direction: Literal["higher_is_better", "lower_is_better", "neutral"]` to `SpecAttribute` (authored per-category like `weight_tier`); add `Group` enum (`same_spec`/`same_job`/`clears_floor`) replacing `Tier`
- [ ] `backend/app/scoring/value.py` — tier assignment logic becomes group assignment (same thresholds, new labels); compute per-spec verdicts from numeric delta + `direction` (text specs: same/different via string match)
- [ ] rationale generation — decided approach (asked user): deterministic template built from `spec_match`/`savings`/`quality`, not an LLM call. Location TBD — likely `scoring/value.py` alongside tier/group assignment, or a new `scoring/rationale.py` if the template grows non-trivial.
- [ ] `backend/app/routes/search.py` — response shape changes from `tiers: {tier1,tier2,tier3}` to `groups: {same_spec,same_job,clears_floor}`; `WireProduct` gains `group`/`verdict`/`rationale`/`short`
- [ ] `frontend/src/api/client.ts` — delete `adaptSearchResponse` and the legacy wire types once the backend ships the real shape
