import csv
import sys
from datetime import datetime

from app import db


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def load_feed(csv_path: str) -> int:
    """Load a CouponAPI.org full-feed CSV into the coupon_offers table.

    Upserts keyed by offer_id, so re-running this on a newer feed dump is
    idempotent rather than duplicating or accumulating stale rows.
    """
    loaded = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        with db.get_pool().connection() as conn:
            for row in reader:
                offer_id = row.get("offer_id")
                store = row.get("store")
                title = row.get("title")
                if not offer_id or not store or not title:
                    continue

                rating_raw = (row.get("rating") or "").strip()
                rating = int(rating_raw) if rating_raw.isdigit() else 0

                conn.execute(
                    """
                    INSERT INTO coupon_offers
                        (offer_id, store, code, discount_description,
                         expires_at, start_date, rating)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (offer_id) DO UPDATE SET
                        store = EXCLUDED.store,
                        code = EXCLUDED.code,
                        discount_description = EXCLUDED.discount_description,
                        expires_at = EXCLUDED.expires_at,
                        start_date = EXCLUDED.start_date,
                        rating = EXCLUDED.rating
                    """,
                    (
                        offer_id,
                        store,
                        row.get("code") or None,
                        title,
                        _parse_date(row.get("end_date") or ""),
                        _parse_date(row.get("start_date") or ""),
                        rating,
                    ),
                )
                loaded += 1
    return loaded


if __name__ == "__main__":
    print(f"Loaded {load_feed(sys.argv[1])} coupon offers")
