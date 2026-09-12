from enum import StrEnum
from typing import Literal

from pydantic import BaseModel


class SearchMode(StrEnum):
    URL = "url"
    EXACT_PRODUCT = "exact_product"
    DESCRIPTION = "description"


class SearchQuery(BaseModel):
    mode: SearchMode
    raw_input: str


class SpecAttribute(BaseModel):
    name: str
    value: float | str
    weight_tier: Literal["hard", "secondary", "soft"]


class Product(BaseModel):
    id: str
    title: str
    brand: str | None
    price: float
    rating: float
    review_count: int
    vendor: str
    image_url: str | None
    product_url: str
    specs: list[SpecAttribute]


class Tier(StrEnum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"


class ComparisonResult(BaseModel):
    candidate: Product
    similarity: float
    quality_score: float
    value_score: float
    tier: Tier
    savings_amount: float | None
    savings_percent: float | None
