from datetime import datetime

from pydantic import BaseModel


class PriceSnapshot(BaseModel):
    product_key: str
    title: str
    store: str
    price: float
    created_at: datetime
    source: str  # "click" | "seed"


class PriceHistoryView(BaseModel):
    title: str
    brand: str
    store: str
    price: float


class PriceHistorySummary(BaseModel):
    sufficient: bool
    current: float | None = None
    low: float | None = None
    high: float | None = None
    # (current - low) / low * 100. Never a projected future price/date —
    # positioning against what's actually been observed, nothing more.
    pct_above_low: float | None = None
    trend: str | None = None  # "up" | "down" | "flat"
