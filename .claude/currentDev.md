## Status: Staged
Target: three new test files — edge-case/runtime-safety only, no correctness/efficacy assertions on the math

### 1. `backend/tests/test_ingestion.py` (new — not in plan.md's checklist; covers the serpapi_client fix just made)
- `test_raises_when_key_unset`: `monkeypatch.setattr(config, "SERPAPI_API_KEY", None)` → `pytest.raises(RuntimeError, match="SERPAPI_API_KEY is not set")`
- `test_wraps_network_failure_as_runtime_error`: set a fake key, `monkeypatch.setattr(httpx, "get", <raises httpx.ReadTimeout>)` → `pytest.raises(RuntimeError, match="SerpAPI request failed")` — exercises the exact fix just applied
- `test_parse_product_handles_missing_fields`: call `serpapi_client._parse_product({"position": 1})` (minimal/malformed raw dict, as SerpAPI could plausibly return) → asserts it returns a `Product` without raising (`id == "1"`, `price == 0.0`, `specs == []`) — a malformed upstream response shouldn't crash the whole request

### 2. `backend/tests/test_scoring.py` (plan.md Phase 7 item — retargeted to edge cases per this stage's instructions, not "$Q$/$V$ formula correctness" as originally worded)
- Local helper `_product(id="p1", price=10.0, rating=4.0, review_count=5)` building a minimal `Product`
- `test_compute_quality_handles_zero_reviews`: `review_count=0, rating=0.0` → just asserts no exception / returns a `float` (division-by-zero guard via `config.BAYESIAN_M` in the denominator)
- `test_compute_quality_scores_handles_empty_list`: `quality.compute_quality_scores([]) == {}`
- `test_rank_candidates_skips_zero_price_products`: a product with `price=0.0` → `value.rank_candidates(...)` returns `[]` (exercises the existing `product.price <= 0: continue` guard, which prevents a division-by-zero in the $V$ calculation)
- `test_rank_candidates_filters_below_quality_threshold`: quality score below `config.MIN_QUALITY_THRESHOLD` → returns `[]`
- `test_rank_candidates_handles_empty_input`: `value.rank_candidates([], {}, {}, {}) == []`

### 3. `backend/tests/test_pipeline.py` (plan.md Phase 7 item — integration test via `fastapi.testclient.TestClient`, everything external mocked so it never makes a real network call)
- `client = TestClient(app)` from `app.main`
- Local helper `_product(id, title="Widget", price=10.0)` (same shape as above)
- `test_search_returns_empty_tiers_when_no_candidates`: patch `app.routes.search.target_resolver.resolve_target` → `None`, `app.routes.search.serpapi_client.search_products` → `[]`; description-mode query (multi-word) → `200`, `tiers == {"tier1": [], "tier2": [], "tier3": []}` — exercises the early-return branch in `search.py`
- `test_search_404s_when_target_not_found`: patch `resolve_target` → `None`; short query (infers `EXACT_PRODUCT`) → `404`
- `test_search_does_not_crash_with_mocked_candidates`: patch `resolve_target` → a target `Product`, `serpapi_client.search_products` → 2 candidate `Product`s, and `app.features.embeddings.embed_text`/`embed_texts` → a fixed fake vector (avoids real OpenAI calls) → asserts `200` only — no assertion on tier placement/scores, just that the full attribute-matrix → SVD → standardize → quality → value pipeline runs end-to-end without raising on realistic-shaped input

### plan.md
- Check off `backend/tests/test_scoring.py` and `backend/tests/test_pipeline.py` (existing Phase 7 items)
- Add a new line for `backend/tests/test_ingestion.py`, marked `[x]`, noting it covers `serpapi_client.py`'s timeout/error-wrapping edge cases — not originally on the checklist
