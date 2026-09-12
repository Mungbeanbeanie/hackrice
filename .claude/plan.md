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

- [x] `backend/app/config.py` — `COUPON_API` added (renamed from the originally-planned `COUPON_API_KEY` to match the real GitHub secret/`.env` name). Its actual use is now uncertain — no live call needs it; may end up used only if CouponAPI.org exposes an authenticated feed-download URL. Kept, not removed, pending that answer.
- [x] `backend/app/coupons/models.py` — revised: dropped `verified_at` (no feed equivalent), added `start_date: datetime | None` and `rating: int` to `CouponOffer`, matching the real feed's available ranking signals.
- [x] `backend/app/coupons/loader.py` — **replaces the originally-planned `client.py`**. Parses the CSV feed (stdlib `csv.DictReader`) from a local file path, upserts each row into a `coupon_offers` Postgres table via `db.py`'s pool, keyed by `offer_id` so re-running the loader on a newer feed is idempotent (replace-on-conflict, not insert-only). Skips rows missing `offer_id`/`store`/`title` (added `offer_id` to the originally-planned store/title check — it's the upsert key). `if __name__ == "__main__"` entrypoint for manual invocation (`python -m app.coupons.loader <path>`), since automated feed retrieval is still unconfirmed. **Depends on `db.py`'s next item creating the `coupon_offers` table** — not yet runnable until that lands.
- [x] `backend/app/db.py` — extended schema bootstrap: added `CREATE TABLE IF NOT EXISTS coupon_offers` (extends Phase 8's file further). `loader.py` is now runnable.
- [x] `backend/app/coupons/selector.py` — `best_offer(store)` queries `coupon_offers` directly for that store; filters `expires_at` in the past; ranks by `rating` desc, then `start_date` desc (`NULLS LAST`) as a recency tiebreak (replaces the abandoned verified_at-based design); returns the single best `CouponOffer` or `None`. Normalizes `store` (lowercase, strip scheme/`www.`) to match the feed's bare-domain format. Turning a `Product.vendor` display name into that domain form is explicitly not solved here — deferred to the caller.
- [x] `backend/app/routes/coupons.py` — `GET /api/coupons?store={name}`. Checks `cache.py`'s `get_cached_coupon` first; on miss, queries `selector.best_offer(store)`, caches the result via `set_cached_coupon` (positive-caching only — no-coupon misses aren't cached, a cheap DB query), returns `CouponOffer | None`. `backend/app/cache.py` extended alongside it with `get_cached_coupon`/`set_cached_coupon` (key `coupon:{store}`, 3600s TTL, same shape as the existing `get_cached_embedding`/`set_cached_embedding` pair).
- [x] `backend/app/main.py` — wire `coupons.router` in (extends Phase 0 file)

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

## Phase 11: Data Contract Backend Catch-up
What Phase 10's client-side stub (`api/client.ts`'s `adaptSearchResponse`) is standing in for. Blocks removing that adapter. Also fixes a latent problem the redesign exposed: extracted spec vocabulary is almost entirely commerce numerics (price/rating/review_count), so a spec-by-spec comparison has had nothing meaningful to compare — spec extraction is extended first so the Compare overlay has real physical specs to show.

This revises the draft above on two points, decided via Q&A: **no** `direction` field on `SpecAttribute` (cache-safety — `cache.py:69-73` calls `Product.model_validate` with no `try`/`except` on Redis payloads with a 3600s TTL; a new required field would 500 every cached query for an hour) and **no** `group` on the wire (nothing reads it — verified against `AlternativeGroups.tsx`/`App.tsx`, which bucket off the `groups` record and `GROUP_ORDER` respectively; it would be the deleted `tier: int` under a new name). Verdict union is 5 values (`same`/`better`/`close`/`different`/`lower`), not 6 — drops `equivalent`; no unreachable values, per-value test coverage required.

- [x] `backend/app/ingestion/serpapi_client.py` — added `_MATERIAL` regex (same shape as `_SIZE`), closed cross-category vocabulary (`memory foam, latex, down, foam, gel, cotton, polyester, wool, leather, aluminum, aluminium, stainless steel, steel, plastic, silicone, bamboo, linen`, multi-word terms before the single-word terms they contain). `_extract_specs` appends a `material` spec (`weight_tier="hard"`) on match, nothing else — no `feature_*` booleans.
- [x] `backend/app/models.py` — `Tier` → `Group` StrEnum (`SAME_SPEC`/`SAME_JOB`/`CLEARS_FLOOR`); `ComparisonResult.tier` → `.group`. No `direction` field (see cache-safety note above). Breaks `value.py`/`routes/search.py`/`test_scoring.py` until those land (next items) — expected, not a regression.
- [x] `backend/app/scoring/value.py` — `_assign_tier` → `_assign_group` (same thresholds/logic, `Tier.*` → `Group.*`); added explicit `_GROUP_RANK` dict (`SAME_SPEC:0, SAME_JOB:1, CLEARS_FLOOR:2`) and fixed the sort key to use it instead of `r.tier.value` lexicographic order — the sort-bug this phase's intro calls out. Regression test still pending (`test_scoring.py`, later item). Prose comments still say "Tier 1/2/3" (preserve-comments rule) — flagged as stale terminology, not edited.
- [x] `backend/app/config.py` — rename `SPEC_MATCH_TIER1`/`SPEC_MATCH_TIER2` → `SPEC_MATCH_SAME_SPEC`/`SPEC_MATCH_SAME_JOB` (confirmed safe — no compose/CI/`.env` override exists anywhere in the repo)
- [ ] `backend/app/scoring/explain.py` (new) — `verdict(name, target_value, value) -> Verdict | None` (unit-suffix-keyed sign table for `measure_*` specs — `gb`/`tb`/`mah`=+1, `lb`/`kg`=-1, else neutral; strings: casefold-equal→same else different; numerics: equal→same, ratio in [0.95,1.05]→close, else sign-based better/lower/different; `None` when the target lacks the spec) + `rationale(result, verdicts) -> str` (group-keyed opening clause, spec-match count, savings clause, rating/reviews — never emits `quality_score`/`value_score`). One file, ~60 lines — both functions share their one caller (`_to_wire_product`).
- [ ] `backend/app/routes/search.py` — `Tiers` → explicit `Groups` model (`same_spec`/`same_job`/`clears_floor` fields, not a dict); `WireProductSpec` gains `verdict`; `WireProduct` gains `short`/`rationale`, loses `tier`, gains **no** `group` (dead field, corrected from the original draft above); `_to_wire_product` filters `COMMERCE_SPECS` (price/discount_pct/rating/review_count) out of emitted specs and calls `explain.verdict`/`explain.rationale`; add `_short(title)` helper; delete `_tier_to_int`
- [ ] `frontend/src/api/client.ts` — delete `adaptSearchResponse` and all legacy wire types/stub helpers wholesale; `searchProducts` becomes a direct `apiFetch<SearchResponse>`; `Verdict` drops `equivalent` (5 values); `ProductSpec.verdict` optional; `Product` drops `group`, gains `rationale?: string`
- [ ] `frontend/src/components/SpecBreakdownModal.tsx` — remove `equivalent` from `VERDICT_STYLE`; `SpecRow.verdict` becomes `Verdict | null` throughout; render the verdict chip only when non-null; guard optional `rationale`
- [ ] `backend/tests/test_explain.py` (new) — same/close/better/lower/different cases, `None` when the target lacks the spec, union-coverage test asserting all 5 verdict values are reachable, rationale savings-clause present/absent, assert no Q/V figures leak into rationale text
- [ ] `backend/tests/test_scoring.py` — fix the stale `Tier` import and its 3 assert sites; convert `test_tiers_spread_across_a_realistic_similarity_range` from a set-assert to an ordered-list assert and rename it — this is the regression guard for the sort bug above
- [ ] `backend/tests/test_ingestion.py` — extend spec-extraction tests with `specs["material"] == "memory foam"` (proves alternation order) and a two-materials-one-title case
- [ ] `backend/tests/test_pipeline.py` — `body["tiers"]` → `body["groups"]`; empty case becomes `{"same_spec": [], "same_job": [], "clears_floor": []}`; give the `_product` fixture a `specs` param (currently hardcodes `specs=[]`, so nothing exercises the wire spec path); add cases for commerce-specs-absent-from-wire, target has `short`/no `rationale`, and description-mode all-`None`-verdicts

Optional, not required by this phase: wrap `cache.get_cached_search` in `except ValidationError: return None` (+ one `test_cache.py` case) — 3 lines that close the "next model change 500s prod for an hour" risk permanently.

Out of scope per locked decision: unrelated doc staleness (`architecture.md`'s phantom `routes/compare.py`, stale test list) — only what this phase changes gets documented.

## Phase 12: Terms & Conditions (done)
Consent gate on sign-up + a subtle link at the bottom of the landing page. Decided with the user: **UI gate only** — acceptance is not sent to or stored by the backend, so no `accounts` schema / `auth.py` / `store.py` / `client.ts` change. Landing footer only; the app screen has no footer and isn't getting one.
- [x] `frontend/src/components/TermsLink.tsx` — new; inline text button + native `<dialog>` holding the terms copy (what we store, why, who else sees it, deletion, third-party price disclaimer, changes). `showModal()` gives Escape/focus-trap/inertness for free instead of re-hand-rolling `SpecBreakdownModal.tsx`'s overlay; backdrop styled via Tailwind's `backdrop:` variant, so no `index.css` change. Self-contained `useRef` — no state in `App.tsx`, no props, `font`/`color: inherit` so one component fits both consumers.
- [x] `frontend/src/components/SignInPage.tsx` — required checkbox in the `step === "email"` form only. Native `required` is the entire gate (browser blocks the submit event, `handleRequestCode` never fires) — no new `useState`.
- [x] `frontend/src/components/LandingPage.tsx` — muted `<TermsLink />` after the "Send feedback" anchor in the footer.
- [x] `frontend/src/components/TermsLink.test.tsx` — first frontend test; vitest+jsdom+@testing-library were already wired (`test: vitest run --passWithNoTests`, zero new deps). Asserts the checkbox is `required` and that opening the terms doesn't tick it — the link renders inside the checkbox's `<label>`, so without `preventDefault` the label forwards the click through.

## Phase 13: Search Tracking & Admin Dashboard (done)
Know how many users and searches we actually have, without SSH + `psql`. Decided with the user: dashboard at **`/api/admin`** (Caddy already routes `/api/*` to the backend and `vite.config.ts` already proxies it in dev — zero routing files touched), **HTTP Basic** auth, search **stays anonymous** (no sign-in gate), and the missing deploy secrets fixed in the same pass. No dependency changes — `HTTPBasic` ships with FastAPI — so no `branchDep.md` row.
- [x] `backend/app/db.py` — third `CREATE TABLE IF NOT EXISTS searches` in `init_schema()` (`id`, `account_id UUID REFERENCES accounts(id)` **nullable**, `query`, `mode`, `result_count`, `created_at`). Nullable `account_id` *is* the anonymous case, which is most rows.
- [x] `backend/app/analytics.py` — new; the only SQL for this feature, module-fns-over-`db.get_pool()` like `accounts/store.py`. `record_search(request, query, mode, result_count)` reads the account via `accounts/session.py` and **never raises** — it swallows and logs, because no-DATABASE_URL / Postgres-down / no-SESSION_SECRET (which makes `_sign` raise) / stale-account FK violation must not fail a user's search. Swallowing inside the function rather than at the call site means a future caller can't forget to. `admin_stats()` returns everything the dashboard renders in one connection.
- [x] `backend/app/routes/search.py` — `search()` gains `request: Request`; one `analytics.record_search(...)` call immediately after the SerpAPI call, before the mode branch. One call site instead of one per return path, and it still counts searches that die on the `404 Target product not found` branch — those were real attempts. `result_count` is therefore candidates-returned-upstream.
- [x] `backend/app/routes/admin.py` — new; `HTTPBasic` + `hmac.compare_digest` (same constant-time convention as `accounts/session.py`), username ignored. **Fails closed**: unset `ADMIN_PASSWORD` → 503, never an open page. Server-rendered `<table>`s in an f-string — no React screen, no chart library. Every interpolated value goes through `html.escape` via `_cell`, because `query` is raw user input and the admin page is exactly where stored XSS would land.
- [x] `backend/app/config.py` — add `ADMIN_PASSWORD`
- [x] `backend/app/main.py` — wire `admin.router` in
- [x] `backend/tests/test_admin.py` — `TestClient` + mocked `analytics` (no live Postgres in CI): 401 no-creds / 401 wrong-password / 503 unset-password / 200 correct / 502 when the stats query fails / `<script>` in a query comes back escaped / `record_search` returns normally when the DB and when `read_session_cookie` raise.
- [x] `.github/workflows/ci.yml`, `deploy/docker-compose.yml`, `deploy/README.md` — `RESEND_API_KEY`, `SESSION_SECRET`, `ADMIN_PASSWORD` through to the box. The first two were **never plumbed**, so Phase 8 accounts had been dead on the deployed site since it shipped: sign-in 502'd and the `accounts` table could never fill. Needed in both the deploy step's `env:` block and the `.env` `printf`, or the value silently arrives empty.

Pending, on the user: add those three as GitHub Environment secrets in both environments — code alone does not fix the live site.

Flagged, not changed (per `instructions.md`): the `DATABASE_URL` comments in `config.py` and `docker-compose.yml` still say nothing reads it; `overview.md` §6.1 said the same. Also the local `.env` sets `DATABASE_URL` to Vultr's pasted `psql "postgres://..."` command rather than a bare URI — `psycopg` rejects the literal `psql`, so accounts/analytics silently no-op wherever that form is used. User believes the wrapper is needed and declined the edit.
