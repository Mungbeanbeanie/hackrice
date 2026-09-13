from datetime import datetime

from app import db
from app.price_history.models import PriceSnapshot


def record_snapshot(
    product_key: str,
    title: str,
    store: str,
    price: float,
    created_at: datetime | None = None,
    source: str = "click",
) -> None:
    """Insert one price observation. `created_at` defaults to now() for a
    real click; callers pass an explicit (backdated) value only when seeding
    (see loader.py) — never used to fabricate an observation that didn't
    happen.
    """
    with db.get_pool().connection() as conn:
        conn.execute(
            """
            INSERT INTO price_snapshots
                (product_key, title, store, price, created_at, source)
            VALUES (%s, %s, %s, %s, COALESCE(%s, now()), %s)
            """,
            (product_key, title, store, price, created_at, source),
        )


def get_history(product_key: str) -> list[PriceSnapshot]:
    with db.get_pool().connection() as conn:
        rows = conn.execute(
            """
            SELECT product_key, title, store, price, created_at, source
            FROM price_snapshots
            WHERE product_key = %s
            ORDER BY created_at ASC, id ASC
            """,
            (product_key,),
        ).fetchall()
    return [
        PriceSnapshot(
            product_key=r[0],
            title=r[1],
            store=r[2],
            price=float(r[3]),
            created_at=r[4],
            source=r[5],
        )
        for r in rows
    ]


def summarize(history: list[PriceSnapshot]) -> dict:
    """Percentile-of-history + trend direction — never a forecast.

    Below 3 snapshots there isn't enough signal to say anything honest; seed
    rows count the same as click rows toward that threshold.
    """
    if len(history) < 3:
        return {"sufficient": False}

    prices = [s.price for s in history]
    current = prices[-1]
    low = min(prices)
    high = max(prices)
    pct_above_low = 0.0 if low <= 0 else round((current - low) / low * 100, 1)

    # Direction from the last 3 points only — a plain observed slope, not a
    # projected future price/date.
    recent = prices[-3:]
    if recent[-1] < recent[0]:
        trend = "down"
    elif recent[-1] > recent[0]:
        trend = "up"
    else:
        trend = "flat"

    return {
        "sufficient": True,
        "current": current,
        "low": low,
        "high": high,
        "pct_above_low": pct_above_low,
        "trend": trend,
    }
