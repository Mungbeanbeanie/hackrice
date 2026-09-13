## Status: Done, pending your review
## Task: Fix duplicate product_id collapsing distinct listings' scores

### Applied
- `backend/app/ingestion/serpapi_client.py` `_parse_product`: id is now `f"{product_id or position or index}-{index}"` — always suffixed with the per-response loop index (unique within one `search_products` call), so two listings sharing a SerpAPI product_id (e.g. same product, different retailer) no longer collapse onto one shared score. Comment above it rewritten to explain why (was previously wrong: claimed uniqueness that product_id alone doesn't guarantee).
- `backend/tests/test_ingestion.py`: updated two exact-id assertions to the new format (`"1"`→`"1-0"`, `"3"`→`"3-3"`); added `test_parse_products_get_unique_ids_even_with_shared_product_id` — two listings with the same explicit product_id at different indices now get distinct ids.

### Verified
- ruff check + format check: clean.
- mypy: clean.
- pytest: 122 passed (was 121 — +1 for the new regression test).
- Grep-confirmed no other code depends on the old id format: `.id` is only used as a dict key / equality-compared / passed through opaquely to the frontend (`routes/search.py:210`, `value.py`, `quality.py`, `attribute_matrix.py`) — never re-parsed or matched against a raw SerpAPI field.

### Not touched
- The two reclassified non-bugs (relative group thresholds, SVD skip threshold) — left alone, confirmed not defects.
