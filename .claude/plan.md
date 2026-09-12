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
- [x] `backend/tests/test_scoring.py` — edge-case/runtime-safety tests for `quality.py`/`value.py` (zero reviews, zero price, empty input, below-quality-threshold filtering) — not $Q$/$V$ formula correctness, per instruction to test runtime safety, not efficacy
- [x] `backend/tests/test_pipeline.py` — integration test of `/api/search` via `TestClient`, with `serpapi_client`/`target_resolver`/`embeddings` mocked — no-candidates branch, target-not-found 404, full pipeline run without raising on mocked realistic input 
