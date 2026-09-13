from datetime import datetime

from pydantic import BaseModel


class SavedProductCreate(BaseModel):
    title: str
    brand: str
    store: str
    price: float | None = None
    image_url: str | None = None
    product_url: str | None = None


class SavedProduct(BaseModel):
    id: int
    title: str
    brand: str
    store: str
    price: float | None
    image_url: str | None
    product_url: str | None
    created_at: datetime
