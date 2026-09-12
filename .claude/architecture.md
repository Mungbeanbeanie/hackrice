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
      ResultCard.tsx
      AlternativeGroups.tsx
      ComparisonTable.tsx
      SpecBreakdownModal.tsx
      LandingPage.tsx
      SignInPage.tsx
      ExtensionPanel.tsx

deploy/
  docker-compose.yml
  README.md
```

`frontend/design_handoff_nectarly_production/` (not shown above) is the Organic
design reference bundle — HTML prototypes + token sheet, not app code. Excluded
from lint/typecheck/build; see `plan.md` Phase 10.

## Component Ownership

| Group | Files | Owns |
| :--- | :--- | :--- |
| Config & Models | `config.py`, `models.py` | Env settings, `SearchMode` enum, shared Pydantic schemas. No internal deps — foundation for every other backend file. |
| Ingestion | `ingestion/target_resolver.py`, `ingestion/serpapi_client.py`, `cache.py` | Resolving/fetching raw product data per search mode; caching responses and embeddings. |
| Feature Engineering | `features/embeddings.py`, `features/attribute_matrix.py`, `features/svd.py`, `features/standardize.py` | Turning raw ingested data into the latent-space similarity score (Layers 1–2 of `overview.md` §3). |
| Scoring | `scoring/quality.py`, `scoring/value.py` | Bayesian quality ($Q$) and value optimization ($V$) computation, tier assignment (Layers 3–4). |
| API | `routes/search.py`, `routes/compare.py`, `main.py` | HTTP surface; orchestrates ingestion → features → scoring per request; wires routers into the app. |
| Frontend data | `api/client.ts` | Typed fetch layer against the API surface above. Sends the raw query only — the backend infers the search mode. Also client-side stubs `group`/`verdict`/`rationale`/`short` over the current (pre-Phase-11) backend response — see `plan.md` Phase 10/11. |
| Frontend input | `components/SearchBar.tsx` | Single query/URL entry field + submit; `hero`/`compact` variants. |
| Frontend output | `components/TargetProductCard.tsx`, `components/ResultCard.tsx`, `components/AlternativeGroups.tsx`, `components/ComparisonTable.tsx`, `components/SpecBreakdownModal.tsx` | Rendering the resolved target (when present) and grouped results, ranked or side-by-side. `ResultCard.tsx` renders one candidate; `AlternativeGroups.tsx` orders the three groups and lays out `ResultCard`s within each. |
| Frontend screens | `components/LandingPage.tsx`, `components/SignInPage.tsx`, `components/ExtensionPanel.tsx` | Marketing/account surfaces composed directly by `App.tsx`'s screen state machine (`landing`/`signin`/`extension`), not nested inside the results flow. |
| Frontend styling | `index.css`, `components/HoneyDrop.tsx` | Tailwind v4 entrypoint, Organic design-system tokens (color ramps, radius, shadow, fonts), shared keyframes, and the logo mark. No internal deps. |
| App composition | `App.tsx`, `main.tsx` | Wires every screen/output component around `api/client.ts`; owns the `screen` × `appState` × `view` state machine. |
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
ResultCard.tsx ──▶ AlternativeGroups.tsx ─┐
                                            │
SearchBar.tsx, TargetProductCard.tsx,      ▼
ComparisonTable.tsx, SpecBreakdownModal.tsx ──▶ App.tsx ◀── LandingPage.tsx, SignInPage.tsx, ExtensionPanel.tsx
                                            ▲
                       index.css, HoneyDrop.tsx (leaf, no deps)
```

Notes:
* `target_resolver.py` calls into `serpapi_client.py` for `exact_product` mode lookups; it is a no-op passthrough for `description` mode (see `plan.md` Phase 2).
* `svd.py` and `standardize.py` both consume `attribute_matrix.py`'s output independently — `svd.py` for Layer 1 similarity, `standardize.py` for Layer 2 scaling — and their outputs both feed `value.py` alongside `quality.py`.
* `TargetProductCard.tsx` is conditionally omitted at the `App.tsx` composition level, not deleted from the tree, when the response carries no `targetProduct` — which is exactly the description-mode case (see `plan.md` Phase 6).
* There is no `SearchModeSelector.tsx`: the UI is a single search box and the backend infers url / exact_product / description from the raw string, so `SearchQuery.mode` is backend-derived rather than client-supplied.
* `HoneyDrop.tsx` is a shared leaf with more consumers than the diagram shows arrows for: `App.tsx` (header, empty state, loading animation), `LandingPage.tsx`, `SignInPage.tsx`, and `ExtensionPanel.tsx` all render it directly.
* `AlternativeTierList.tsx` (Phase 6) was deleted in Phase 10 — replaced by `ResultCard.tsx` (one candidate) + `AlternativeGroups.tsx` (group ordering/layout), matching the Organic design handoff's `same_spec`/`same_job`/`clears_floor` groups. See `plan.md` Phase 10/11 for the backend data-contract catch-up this still depends on.
