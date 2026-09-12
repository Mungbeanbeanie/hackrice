from datetime import datetime

from pydantic import BaseModel


class CouponOffer(BaseModel):
    code: str | None
    discount_description: str
    store: str
    expires_at: datetime | None
    verified_at: datetime | None
