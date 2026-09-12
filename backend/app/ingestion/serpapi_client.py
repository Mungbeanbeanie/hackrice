import logging
import re

import httpx

from app import cache, config
from app.models import Product

logger = logging.getLogger(__name__)

SERPAPI_URL = "https://serpapi.com/search"
REQUEST_TIMEOUT = httpx.Timeout(connect=5.0, read=25.0, write=5.0, pool=5.0)


def search_products(query: str) -> list[Product]:
    if not config.SERPAPI_API_KEY:
        raise RuntimeError("SERPAPI_API_KEY is not set")

    # Cached here rather than in the route so that both call sites benefit —
    # candidate search and target resolution, which is twice per url-mode
    # request — and so scoring still re-runs fresh on cached raw data.
    key = cache.hash_key(query)
    cached = cache.get_cached_search(key)
    if cached is not None:
        return cached

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

    products = [
        _parse_product(raw) for raw in response.json().get("shopping_results", [])
    ]
    # A 200 with no results shouldn't poison the query for the full TTL; a
    # re-fetch on a genuinely empty query costs one call.
    if products:
        cache.set_cached_search(key, products)
    return products


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
