from fastapi import APIRouter

from app.price_history import store
from app.price_history.key import normalize_product_key
from app.price_history.models import PriceHistorySummary, PriceHistoryView

router = APIRouter()


@router.post("/api/price-history/view")
def view_price_history(body: PriceHistoryView) -> PriceHistorySummary:
    """Called once per candidate selection, never on search — records this
    view as a snapshot, then returns whatever history exists for the exact
    listing in one round trip.
    """
    key = normalize_product_key(body.title, body.brand, body.store)
    store.record_snapshot(key, body.title, body.store, body.price)
    history = store.get_history(key)
    return PriceHistorySummary(**store.summarize(history))
