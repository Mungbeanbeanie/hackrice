from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel


class SearchMode(StrEnum):
    URL = "url"
    EXACT_PRODUCT = "exact_product"
    DESCRIPTION = "description"


class SpecAttribute(BaseModel):
    name: str
    value: float | str
    weight_tier: Literal["hard", "secondary", "soft"]


class Product(BaseModel):
    id: str
    title: str
    # Snippet and feature tags from the listing, when the payload carries them.
    # Sparse, and the only spec-bearing prose available for Layer 1 matching.
    description: str | None
    brand: str | None
    price: float
    original_price: float | None
    rating: float
    review_count: int
    vendor: str
    vendor_logo: str | None
    image_url: str | None
    product_url: str
    specs: list[SpecAttribute]


class Group(StrEnum):
    SAME_SPEC = "same_spec"
    SAME_JOB = "same_job"
    CLEARS_FLOOR = "clears_floor"


class ComparisonResult(BaseModel):
    candidate: Product
    similarity: float
    quality_score: float
    value_score: float
    group: Group
    savings_amount: float | None
    savings_percent: float | None


class Account(BaseModel):
    id: str
    email: str
    created_at: datetime
