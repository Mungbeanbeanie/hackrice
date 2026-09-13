import csv
import sys
from datetime import datetime

from app.price_history.key import normalize_product_key
from app.price_history.store import record_snapshot


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def load_csv(csv_path: str) -> int:
    """Manually-run seed loader — mirrors coupons/loader.py's pattern.

    Not automated, not scheduled. For bootstrapping real observed historical
    prices (own records, or a public price-history chart read by hand — e.g.
    Keepa/CamelCamelCamel for Amazon-origin listings) so production isn't
    empty on day one. Every row lands with source="seed", distinct from the
    "click" rows recorded by real user activity — never used to fabricate an
    observation that wasn't actually seen somewhere.
    """
    loaded = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get("title")
            store = row.get("store")
            price_raw = row.get("price")
            date_raw = row.get("date")
            if not title or not store or not price_raw or not date_raw:
                continue
            brand = row.get("brand") or ""
            key = normalize_product_key(title, brand, store)
            record_snapshot(
                key,
                title,
                store,
                float(price_raw),
                created_at=_parse_date(date_raw),
                source="seed",
            )
            loaded += 1
    return loaded


if __name__ == "__main__":
    print(f"Loaded {load_csv(sys.argv[1])} seed price snapshots")
