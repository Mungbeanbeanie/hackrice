import re

from app import db
from app.coupons.models import CouponOffer


def _normalize_store(store: str) -> str:
    normalized = store.strip().lower()
    for prefix in ("https://", "http://", "www."):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
    return normalized.rstrip("/")


def store_slug(store: str) -> str:
    """A display name reduced to the shape a bare domain's first label takes.

    SerpAPI gives the merchant as a display name ("Dick's Sporting Goods") while
    the feed keys on bare domains ("dickssportinggoods.com"), so nothing matched.
    Dropping everything but letters and digits bridges the two for the retailers
    whose domain is just their name run together, which is most of them.
    """
    return re.sub(r"[^a-z0-9]", "", _normalize_store(store))


def best_offer(store: str) -> CouponOffer | None:
    """The single best currently-active coupon for a store, or None.

    `store` matches the feed's bare-domain values (e.g. "1800petmeds.com") after
    light normalization (scheme/www stripped, lowercased), or — so that callers
    can pass a Product.vendor display name straight through — against the
    domain's first label with punctuation and spaces removed.
    """
    normalized = _normalize_store(store)
    with db.get_pool().connection() as conn:
        row = conn.execute(
            """
            SELECT code, discount_description, store, expires_at, start_date, rating
            FROM coupon_offers
            WHERE (store = %s OR split_part(store, '.', 1) = %s)
              AND (expires_at IS NULL OR expires_at > now())
            ORDER BY rating DESC, start_date DESC NULLS LAST
            LIMIT 1
            """,
            (normalized, store_slug(store)),
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
