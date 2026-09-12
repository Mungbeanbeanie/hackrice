from app import db
from app.coupons.models import CouponOffer


def _normalize_store(store: str) -> str:
    normalized = store.strip().lower()
    for prefix in ("https://", "http://", "www."):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
    return normalized.rstrip("/")


def best_offer(store: str) -> CouponOffer | None:
    """The single best currently-active coupon for a store, or None.

    `store` is matched against the feed's bare-domain values (e.g.
    "1800petmeds.com") after light normalization (scheme/www stripped,
    lowercased). Turning a Product.vendor display name ("1800 Pet Meds")
    into that domain form is not solved here — callers must supply
    something already in that shape.
    """
    normalized = _normalize_store(store)
    with db.get_pool().connection() as conn:
        row = conn.execute(
            """
            SELECT code, discount_description, store, expires_at, start_date, rating
            FROM coupon_offers
            WHERE store = %s AND (expires_at IS NULL OR expires_at > now())
            ORDER BY rating DESC, start_date DESC NULLS LAST
            LIMIT 1
            """,
            (normalized,),
        ).fetchone()
    if row is None:
        return None
    return CouponOffer(
        code=row[0],
        discount_description=row[1],
        store=row[2],
        expires_at=row[3],
        start_date=row[4],
        rating=row[5],
    )
