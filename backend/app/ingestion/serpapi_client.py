import logging
import re

import httpx

from app import config
from app.models import Product

logger = logging.getLogger(__name__)

SERPAPI_URL = "https://serpapi.com/search"
REQUEST_TIMEOUT = 10.0


def search_products(query: str) -> list[Product]:
    if not config.SERPAPI_API_KEY:
        raise RuntimeError("SERPAPI_API_KEY is not set")

    try:
        response = httpx.get(
            SERPAPI_URL,
            params={
                "engine": "google_shopping",
                "q": query,
                "api_key": config.SERPAPI_API_KEY,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception("SerpAPI request failed for query=%r", query)
        raise RuntimeError(f"SerpAPI request failed: {exc}") from exc

    return [_parse_product(raw) for raw in response.json().get("shopping_results", [])]


def _parse_product(raw: dict) -> Product:
    price = raw.get("extracted_price")
    if price is None:
        price = _parse_price_string(raw.get("price", ""))

    return Product(
        id=str(raw.get("product_id", raw.get("position", ""))),
        title=raw.get("title", ""),
        brand=raw.get("source"),
        price=price,
        rating=raw.get("rating", 0.0),
        review_count=raw.get("reviews", 0),
        vendor=raw.get("source", ""),
        image_url=raw.get("thumbnail"),
        product_url=raw.get("product_link", ""),
        specs=[],
    )


def _parse_price_string(price: str) -> float:
    match = re.search(r"[\d,]+\.?\d*", price)
    return float(match.group().replace(",", "")) if match else 0.0
