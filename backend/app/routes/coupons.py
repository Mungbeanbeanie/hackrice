from fastapi import APIRouter, Query

from app import cache
from app.coupons import selector
from app.coupons.models import CouponOffer

router = APIRouter()


@router.get("/api/coupons")
def get_coupon(store: str = Query(..., min_length=1)) -> CouponOffer | None:
    cached = cache.get_cached_coupon(store)
    if cached is not None:
        return cached

    offer = selector.best_offer(store)
    if offer is not None:
        cache.set_cached_coupon(store, offer)
    return offer
