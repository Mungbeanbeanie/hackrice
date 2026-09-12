import logging
import re

import httpx

from app import cache, config
from app.models import Product

logger = logging.getLogger(__name__)

SERPAPI_URL = "https://serpapi.com/search"
# A synchronous google_shopping search holds the connection open for the whole
# scrape, so TTFB is the search duration, not network latency. Measured cold:
# 17s and 52s on two sample queries. A repeat of the same query returns in
# 0.06s — SerpAPI replays its own cached copy — so this budget is paid once per
# distinct query, then absorbed by that cache and ours.
#
# 90s is deliberately well above the 52s worst case observed. The old 25s was
# below it, and every search died on the read.
#
# ponytail: retry 5xx once, never timeouts. SerpAPI 503s when its own scrape
# fails — observed intermittent, the same query succeeding on the next call, so
# the "add one only if stalls prove intermittent" note above is now settled. A
# 5xx comes back fast, so the retry costs little; retrying a timeout would stack
# two 90s reads into 180s, which no browser waits through.
REQUEST_TIMEOUT = httpx.Timeout(connect=5.0, read=90.0, write=5.0, pool=5.0)


def _upstream_error(query: str, exc: httpx.HTTPError) -> RuntimeError:
    # httpx puts the full request URL in its exception message, and our api_key
    # rides in that URL's query string. Interpolating the exception leaked the
    # key into the 502 body the browser renders and into the logged traceback,
    # so report the status or the exception class and never the URL itself.
    reason = (
        f"HTTP {exc.response.status_code}"
        if isinstance(exc, httpx.HTTPStatusError)
        else type(exc).__name__
    )
    logger.error("SerpAPI request failed for query=%r: %s", query, reason)
    return RuntimeError(f"SerpAPI request failed: {reason}")


def _fetch(query: str) -> httpx.Response:
    for attempt in range(2):
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
            return response
        except httpx.HTTPError as exc:
            server_error = (
                isinstance(exc, httpx.HTTPStatusError)
                and exc.response.status_code >= 500
            )
            if attempt == 1 or not server_error:
                raise _upstream_error(query, exc) from None

    raise AssertionError("unreachable")  # the loop either returns or raises


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

    response = _fetch(query)

    products = [
        _parse_product(raw, i)
        for i, raw in enumerate(response.json().get("shopping_results", []))
    ]
    # A 200 with no results shouldn't poison the query for the full TTL; a
    # re-fetch on a genuinely empty query costs one call.
    if products:
        cache.set_cached_search(key, products)
    return products


def _parse_product(raw: dict, index: int) -> Product:
    price = raw.get("extracted_price")
    if price is None:
        price = _parse_price_string(raw.get("price") or "")

    # `or` rather than a .get() default throughout: SerpAPI sends explicit nulls
    # as well as omitting keys, and .get(k, default) only covers the omission.
    # A null rating would fail Product's non-optional float and 500 the request.
    #
    # The index fallback keeps ids unique. Scores are carried in dicts keyed by
    # product.id (quality.py, svd.py, standardize.py), so two candidates sharing
    # an id silently share one score.
    return Product(
        id=str(raw.get("product_id") or raw.get("position") or index),
        title=raw.get("title") or "",
        brand=raw.get("source"),
        price=price,
        rating=raw.get("rating") or 0.0,
        review_count=raw.get("reviews") or 0,
        vendor=raw.get("source") or "",
        image_url=raw.get("thumbnail"),
        product_url=raw.get("product_link") or "",
        specs=[],
    )


def _parse_price_string(price: str) -> float:
    match = re.search(r"[\d,]+\.?\d*", price)
    return float(match.group().replace(",", "")) if match else 0.0
