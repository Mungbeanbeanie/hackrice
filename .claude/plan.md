# Build Plan

Checklist, worked top-to-bottom. Each item is exactly one file with a single responsibility — `stage`/`apply` should be able to touch one checklist item without needing to also change any other file. Phases are ordered by dependency (later phases consume earlier ones).

Mission: implement the financial optimization product comparison pipeline described in `overview.md` on top of the existing FastAPI + Vite/React skeleton.

## Phase 0: Foundation (done)
- [x] `backend/app/main.py` — FastAPI app instance, `/api/health` route
- [x] `frontend/src/App.tsx` — placeholder shell, pings `/api/health`
- [x] `deploy/docker-compose.yml` — api/web services, Caddy TLS, healthcheck
- [x] `deploy/README.md` — deploy env/secrets documentation

## Phase 1: Config & Models
- [ ] `backend/app/config.py` — env-driven settings (SerpAPI key, cache connection, `m=25`, `C=4.0` defaults, category weight defaults)
- [ ] `backend/app/models.py` — Pydantic schemas: `Product`, `SearchQuery`, `SpecAttribute`, `ComparisonResult`, `Tier`

## Phase 2: Data Ingestion
- [ ] `backend/app/ingestion/serpapi_client.py` — SerpAPI Google Shopping request wrapper, raw JSON → `Product` parsing
- [ ] `backend/app/cache.py` — Vultr-backed cache layer (get/set search responses and embeddings by query hash)

## Phase 3: Feature Engineering
- [ ] `backend/app/features/embeddings.py` — `text-embedding-3-small` wrapper for title/spec text
- [ ] `backend/app/features/attribute_matrix.py` — builds the product-attribute matrix $A$ from raw specs + embeddings
- [ ] `backend/app/features/svd.py` — Layer 1: SVD decomposition of $A$, latent projection, cosine similarity between target/candidate
- [ ] `backend/app/features/standardize.py` — Layer 2: per-category z-score standardization + diagonal weight matrix $\mathbf{W}$

## Phase 4: Scoring
- [ ] `backend/app/scoring/quality.py` — Layer 3: Bayesian quality estimator $Q$
- [ ] `backend/app/scoring/value.py` — Layer 4: value optimization score $V$, tier assignment (1/2/3)

## Phase 5: API
- [ ] `backend/app/routes/search.py` — `POST /api/search`, orchestrates ingestion → features → scoring, returns tiered results
- [ ] `backend/app/routes/compare.py` — `GET /api/compare/{id}`, spec breakdown detail for one candidate
- [ ] `backend/app/main.py` — wire `search`/`compare` routers into the existing app (extends Phase 0 file)

## Phase 6: Frontend
- [ ] `frontend/src/api/client.ts` — typed fetch wrapper for `/api/search` and `/api/compare/{id}`
- [ ] `frontend/src/components/SearchBar.tsx` — query/URL input + submit
- [ ] `frontend/src/components/TargetProductCard.tsx` — target reference product header
- [ ] `frontend/src/components/AlternativeTierList.tsx` — renders Tier 1/2/3 result sections
- [ ] `frontend/src/components/SpecBreakdownModal.tsx` — "Compare Spec Breakdown" detail view
- [ ] `frontend/src/App.tsx` — wire search flow + components together (extends Phase 0 file)

## Phase 7: Tests
- [ ] `backend/tests/test_scoring.py` — unit tests for $Q$ and $V$ formula correctness
- [ ] `backend/tests/test_pipeline.py` — integration test of full pipeline against a mocked SerpAPI response
