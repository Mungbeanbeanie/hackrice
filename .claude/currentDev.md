## Status: Staged
Task: Phase 9 Coupons — `backend/app/coupons/selector.py` (new)

- `best_offer(store: str) -> CouponOffer | None` — the single best currently-active offer for a store, or `None` if there isn't one
- Query `coupon_offers` directly (not an in-memory list, matches plan.md): filter `expires_at IS NULL OR expires_at > now()`; order by `rating DESC, start_date DESC NULLS LAST`; `LIMIT 1`
- `_normalize_store(store)` helper: lowercase, strip `https://`/`http://`/`www.` prefix, strip trailing `/` — matches the feed's bare-domain format (e.g. `1800petmeds.com`)
- Explicitly NOT solved here (flagged in a docstring, not attempted): turning a `Product.vendor` display name ("1800 Pet Meds") into the feed's domain form. Caller (`routes/coupons.py`) must supply something already in that shape — this stays an open problem, out of scope for this file per plan.md's item boundary
- Matches `accounts/store.py`'s convention: raw SQL via `db.get_pool().connection()`, `%s` placeholders, manual tuple→model unpacking
- Importers: none yet — `routes/coupons.py` (next item) will call `best_offer`
- No dependency changes
