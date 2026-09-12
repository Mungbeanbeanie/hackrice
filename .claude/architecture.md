# Architecture

File structure, component ownership, and dependency graph. Responsibility text for each file lives in `plan.md` — not duplicated here.

## File Structure

```
backend/
  app/
    main.py
    config.py
    models.py
    cache.py
    ingestion/
      target_resolver.py
      serpapi_client.py
    features/
      embeddings.py
      attribute_matrix.py
      svd.py
      standardize.py
    scoring/
      quality.py
      value.py
    routes/
      search.py
      compare.py
  tests/
    test_smoke.py
    test_scoring.py
    test_pipeline.py

frontend/
  src/
    main.tsx
    App.tsx
    index.css
    api/
      client.ts
    components/
      SearchBar.tsx
      HoneyDrop.tsx
      TargetProductCard.tsx
      AlternativeTierList.tsx
      SpecBreakdownModal.tsx

deploy/
  docker-compose.yml
  README.md
```

## Component Ownership

| Group | Files | Owns |
| :--- | :--- | :--- |
| Config & Models | `config.py`, `models.py` | Env settings, `SearchMode` enum, shared Pydantic schemas. No internal deps — foundation for every other backend file. |
| Ingestion | `ingestion/target_resolver.py`, `ingestion/serpapi_client.py`, `cache.py` | Resolving/fetching raw product data per search mode; caching responses and embeddings. |
| Feature Engineering | `features/embeddings.py`, `features/attribute_matrix.py`, `features/svd.py`, `features/standardize.py` | Turning raw ingested data into the latent-space similarity score (Layers 1–2 of `overview.md` §3). |
| Scoring | `scoring/quality.py`, `scoring/value.py` | Bayesian quality ($Q$) and value optimization ($V$) computation, tier assignment (Layers 3–4). |
| API | `routes/search.py`, `routes/compare.py`, `main.py` | HTTP surface; orchestrates ingestion → features → scoring per request; wires routers into the app. |
| Frontend data | `api/client.ts` | Typed fetch layer against the API surface above. Sends the raw query only — the backend infers the search mode. |
| Frontend input | `components/SearchBar.tsx` | Single query/URL entry field + submit. |
| Frontend output | `components/TargetProductCard.tsx`, `components/AlternativeTierList.tsx`, `components/SpecBreakdownModal.tsx` | Rendering the resolved target (when present) and tiered results. |
| Frontend styling | `index.css`, `components/HoneyDrop.tsx` | Tailwind v4 entrypoint, honey theme tokens, shared animation/card classes, and the logo mark. No internal deps. |
| App composition | `App.tsx`, `main.tsx` | Wires input + output components around `api/client.ts`; owns the idle/loading/results/error states. |
| Deploy | `docker-compose.yml`, `README.md` | Runs built backend/frontend images; no dependency on internal file structure. |

## Dependency Graph

```
config.py ─┬─▶ models.py
           │
           ▼
target_resolver.py ──▶ serpapi_client.py ──▶ cache.py
           │
           ▼
embeddings.py ──▶ attribute_matrix.py ─┬─▶ svd.py
                                        └─▶ standardize.py
           │
           ▼
quality.py ──▶ value.py
           │
           ▼
routes/search.py ──▶ routes/compare.py
           │
           ▼
main.py  (wires routers into the FastAPI app)
           │
           ▼
frontend/src/api/client.ts
           │
           ▼
                          SearchBar.tsx ─┐
                                          ▼
TargetProductCard.tsx ──────────────▶ App.tsx ◀── AlternativeTierList.tsx ◀── SpecBreakdownModal.tsx
                                          ▲
                       index.css, HoneyDrop.tsx (leaf, no deps)
```

Notes:
* `target_resolver.py` calls into `serpapi_client.py` for `exact_product` mode lookups; it is a no-op passthrough for `description` mode (see `plan.md` Phase 2).
* `svd.py` and `standardize.py` both consume `attribute_matrix.py`'s output independently — `svd.py` for Layer 1 similarity, `standardize.py` for Layer 2 scaling — and their outputs both feed `value.py` alongside `quality.py`.
* `TargetProductCard.tsx` is conditionally omitted at the `App.tsx` composition level, not deleted from the tree, when the response carries no `targetProduct` — which is exactly the description-mode case (see `plan.md` Phase 6).
* There is no `SearchModeSelector.tsx`: the UI is a single search box and the backend infers url / exact_product / description from the raw string, so `SearchQuery.mode` is backend-derived rather than client-supplied.
