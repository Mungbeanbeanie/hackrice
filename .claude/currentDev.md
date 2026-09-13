## Status: Active
## Task: Price History feature (click-triggered, self-collected, product-keyed — not account-tied)

### Researched, rejected (checked before writing this plan)
- Google Shopping/Product API (SerpAPI, already our provider): confirmed via docs — no `price_history`/`typical_prices` field. Google's own price-history chart is a browser-only UI feature, not in the API response.
- Keepa API: real, has genuine multi-year price history — but Amazon-only, paid (~€49/mo min), needs ASIN matching. Flag as possible FUTURE enhancement for Amazon-origin candidates only. Not built now (new paid dep + secret).
- Wayback Machine CDX API: free, no key — but coverage of arbitrary retail product pages is sparse (most pages never/rarely crawled), and modern retail prices are usually JS-rendered, not in static archived HTML. Not pursued.
- ShopSavvy/PricesAPI/Apify multi-retailer scrapers: surfaced by search, unverified pricing/coverage/reliability. Not pursued without further vetting — same paid-third-party-dependency tradeoff as Keepa.
- Conclusion: no external source gives us general multi-retailer price history. Self-collected snapshots is the only viable MVP path.

### Design decisions locked in this thread
- NOT account-tied. Shared table keyed by product identity, benefits every user (signed in or not).
- NOT triggered by search. Triggered only when a user clicks/selects a specific candidate — same signal that already drives `CouponPanel` (`AlternativeGroups`'s `onSelect`).
- Product identity key: normalized (title, brand, store) — reuse `coupons/selector.py`'s store-domain normalization convention. Flag: cross-retailer fuzzy-matching is approximate, not solved (same caveat as coupons store-matching).
- No forecast/future price claim. Advisory is percentile-of-own-history + trend direction only ("X% below recorded low" / "trending up/down"), never a predicted date/price.
- Threshold: need >=3 snapshots for that exact listing before showing any advisory; below that, show "not enough history yet."
- Cyclical/seasonal detection: explicitly deferred, needs real historical depth we won't have at launch.
- No cache layer for v1 (read is a cheap aggregate query over a small per-listing row set) — revisit only if read volume becomes a real problem.

### Backend — new `backend/app/price_history/` dir (parallels `coupons/` structure)
- `models.py` — `PriceSnapshot` pydantic model: `product_key`, `title`, `store`, `price`, `created_at`, `source` (`click` | `seed`).
- `key.py` — `normalize_product_key(title, brand, store) -> str`; reuse/extend coupons' store normalization.
- `store.py` — `record_snapshot(product_key, title, store, price, created_at=None, source="click")` (insert; `created_at` defaults to now for real clicks, explicit/backdated for seed rows); `get_history(product_key) -> list[PriceSnapshot]` (ordered by created_at); `summarize(history) -> {min, max, current_percentile, trend, sufficient: bool}` (pure function, no DB) — sufficient=False when len(history) < 3, counting seed rows the same as click rows.
- `backend/app/db.py` (edit) — add `CREATE TABLE IF NOT EXISTS price_snapshots` to `init_schema()` (id, product_key indexed, title, store, price, created_at, source) — same idempotent-bootstrap pattern as `coupon_offers`/`searches`.
- `backend/app/price_history/loader.py` (new) — manual seed CLI, mirrors `coupons/loader.py`'s pattern exactly: `python -m app.price_history.loader <csv>`, CSV columns `title,brand,store,price,date`; normalizes key via `key.py`, calls `record_snapshot(..., created_at=<parsed date>, source="seed")`. Not automated, not scheduled — user-run only, for bootstrapping real observed historical prices (own records, or manually read off a public chart like Keepa/CamelCamelCamel for Amazon-origin products) so production isn't empty on day one. Never used to fabricate numbers.
- `backend/app/routes/price_history.py` (new) — `POST /api/price-history/view` — body: {title, brand, store, price}; server normalizes key, calls `record_snapshot`, then `get_history`+`summarize`, returns summary in one round trip (one call from frontend on select, not two).
- `backend/app/main.py` (edit) — wire `price_history.router` in.

### Frontend
- `frontend/src/api/client.ts` (edit) — add `viewPriceHistory(title, brand, store, price)` typed fetch wrapper hitting the new route.
- `frontend/src/components/PriceHistoryPanel.tsx` (new) + `.test.tsx` — sidebar card, selection-driven like `CouponPanel.tsx`; states: idle (nothing selected) / loading / insufficient-history / done. Done state: hand-rolled inline SVG sparkline (no charting lib — keep bundle small, matches extension's no-bundled-assets precedent) + "$current — X% above/below recorded low of $Y" line + trend arrow.
- `frontend/src/App.tsx` (edit) — extend the existing `onSelect` handler (the one that sets `couponProduct`) to also call `viewPriceHistory` and store the result in new state; render `PriceHistoryPanel` in the sidebar alongside the existing Possible Savings / Cheapest option / Coupons cards.

No dependency changes (no new npm/pip packages) — no `branchDep.md` row needed.

### Not doing now (flag, don't build)
- Keepa integration (Amazon-only, paid, future maybe)
- Wayback Machine scraping (unreliable coverage/JS-rendered prices)
- Cyclical/seasonal pattern detection (needs depth we won't have)
- Cross-retailer product-identity matching beyond simple normalization (approximate, same caveat as coupons)
