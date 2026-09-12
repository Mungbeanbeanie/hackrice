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
- [ ] `backend/app/features/embeddings.py` — `text-embedding-3-small` wrapper for title/spec text and raw query text (`description` mode)
- [ ] `backend/app/features/attribute_matrix.py` — builds the product-attribute matrix $A$ from raw specs + embeddings
- [ ] `backend/app/features/svd.py` — Layer 1: SVD decomposition of $A$, latent projection, cosine similarity between reference vector (target product, or embedded query in `description` mode) and each candidate
- [ ] `backend/app/features/standardize.py` — Layer 2: per-category z-score standardization + diagonal weight matrix $\mathbf{W}$

## Phase 4: Scoring
- [ ] `backend/app/scoring/quality.py` — Layer 3: Bayesian quality estimator $Q$
- [ ] `backend/app/scoring/value.py` — Layer 4: value optimization score $V$, tier assignment (1/2/3)

## Phase 5: API
- [ ] `backend/app/routes/search.py` — `POST /api/search`, branches on `SearchQuery.mode` (resolve target or skip), orchestrates ingestion → features → scoring, returns tiered results (target product omitted from response in `description` mode)
- [ ] `backend/app/routes/compare.py` — `GET /api/compare/{id}`, spec breakdown detail for one candidate
- [ ] `backend/app/main.py` — wire `search`/`compare` routers into the existing app (extends Phase 0 file)

## Phase 6: Frontend
- [ ] `frontend/src/api/client.ts` — typed fetch wrapper for `/api/search` (includes `mode`) and `/api/compare/{id}`
- [ ] `frontend/src/components/SearchModeSelector.tsx` — URL / Exact Product / Description mode toggle, adapts input field placeholder + validation
- [ ] `frontend/src/components/SearchBar.tsx` — query/URL input + submit, reads active mode from `SearchModeSelector`
- [ ] `frontend/src/components/TargetProductCard.tsx` — target reference product header; not rendered when `mode === "description"`
- [ ] `frontend/src/components/AlternativeTierList.tsx` — renders Tier 1/2/3 result sections
- [ ] `frontend/src/components/SpecBreakdownModal.tsx` — "Compare Spec Breakdown" detail view
- [ ] `frontend/src/App.tsx` — wire search flow + components together, conditionally render `TargetProductCard` by mode (extends Phase 0 file)

## Phase 7: Tests
- [ ] `backend/tests/test_scoring.py` — unit tests for $Q$ and $V$ formula correctness
- [ ] `backend/tests/test_pipeline.py` — integration test of full pipeline against a mocked SerpAPI response
