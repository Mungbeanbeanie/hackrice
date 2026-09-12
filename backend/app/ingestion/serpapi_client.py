import logging
import re

import httpx

from app import cache, config
from app.models import Product, SpecAttribute

logger = logging.getLogger(__name__)

SERPAPI_URL = "https://serpapi.com/search"
# A synchronous google_shopping search holds the connection open for the whole
# scrape, so TTFB is the search duration, not network latency. Measured cold:
# 17s, 38s and 71s across sample queries. A repeat of the same query returns in
# 0.1s — SerpAPI replays its own cached copy — so this budget is paid once per
# distinct query, then absorbed by that cache and ours.
#
# 120s is above the 71s worst case observed. Earlier values of 25s and 90s were
# at or below it, and searches died on the read.
#
# ponytail: retry 5xx once, never timeouts. SerpAPI 503s when its own scrape
# fails — observed intermittent, the same query succeeding on the next call, so
# the "add one only if stalls prove intermittent" note above is now settled. A
# 5xx comes back fast, so the retry costs little; the retry loop below only
# fires on HTTPStatusError >= 500, never on a httpx.ReadTimeout, so raising the
# read budget here never risks stacking two long reads back to back.
REQUEST_TIMEOUT = httpx.Timeout(connect=5.0, read=120.0, write=5.0, pool=5.0)

# Generic "<number><unit>" spec, e.g. "18 in", "4.5oz", "500 GB". Deliberately
# unit-driven rather than category-driven: it finds the real specs in a laptop
# title and in a pillow title without either being enumerated anywhere.
_MEASURE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(oz|lb|lbs|kg|g|ml|l|in|inch|inches|cm|mm|ft|w|v|gb|tb|mah)\b",
    re.I,
)
_UNIT_ALIASES = {"inch": "in", "inches": "in", "lbs": "lb"}

# Bedding/furniture sizing is categorical, not numeric, so no unit pattern
# reaches it. Highest-coverage real spec on the sample payload (15/40).
_SIZE = re.compile(r"\b(twin|full|queen|king|standard|jumbo)\b", re.I)


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

    # Cached on the raw upstream payload rather than on the finished response,
    # so scoring changes take effect on the next request instead of waiting out
    # the TTL behind a stale ranking.
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


def _description(raw: dict) -> str | None:
    """The prose SerpAPI gives us beyond the title.

    `snippet` and `extensions` are sparse but are the only spec-bearing text in
    the payload; title alone throws away the material and feature words that
    Layer 1 matches on.
    """
    parts = [raw.get("snippet"), " ".join(raw.get("extensions") or [])]
    return " ".join(p for p in parts if p) or None


def _extract_specs(
    text: str, price: float, original_price: float | None, raw: dict
) -> list[SpecAttribute]:
    """Numeric and categorical attributes for Layers 2-3.

    Coverage is genuinely sparse — on a sample payload, size hit 15/40 and
    measurements 2/40 — so callers must stay correct when this returns only the
    commerce numerics. It is additive signal, never a precondition.
    """
    specs: list[SpecAttribute] = [
        SpecAttribute(name="price", value=price, weight_tier="secondary")
    ]

    if original_price and original_price > price:
        specs.append(
            SpecAttribute(
                name="discount_pct",
                value=round((original_price - price) / original_price * 100, 2),
                weight_tier="secondary",
            )
        )

    rating = raw.get("rating")
    if rating:
        specs.append(
            SpecAttribute(name="rating", value=float(rating), weight_tier="secondary")
        )
    reviews = raw.get("reviews")
    if reviews:
        specs.append(
            SpecAttribute(
                name="review_count", value=float(reviews), weight_tier="secondary"
            )
        )

    # Only the first match per unit: titles repeat dimensions ("18x12 in") and a
    # spec name has to be stable across products for the matrix to align them.
    # Aliases collapse for the same reason — "18 inches" and "18 in" have to
    # reach the matrix as one column, not two half-filled ones.
    for amount, unit in _MEASURE.findall(text):
        name = f"measure_{_UNIT_ALIASES.get(unit.lower(), unit.lower())}"
        if not any(s.name == name for s in specs):
            specs.append(
                SpecAttribute(name=name, value=float(amount), weight_tier="hard")
            )

    size = _SIZE.search(text)
    if size:
        specs.append(
            SpecAttribute(name="size", value=size.group(1).lower(), weight_tier="hard")
        )

    return specs


def _parse_product(raw: dict, index: int) -> Product:
    price = raw.get("extracted_price")
    if price is None:
        price = _parse_price_string(raw.get("price") or "")
    original_price = raw.get("extracted_old_price")
    title = raw.get("title") or ""
    description = _description(raw)

    # `or` rather than a .get() default throughout: SerpAPI sends explicit nulls
    # as well as omitting keys, and .get(k, default) only covers the omission.
    # A null rating would fail Product's non-optional float and 500 the request.
    #
    # The index fallback keeps ids unique. Scores are carried in dicts keyed by
    # product.id (quality.py, svd.py, standardize.py), so two candidates sharing
    # an id silently share one score.
    #
    # brand stays None: `source` is the merchant ("Walmart"), not the maker, and
    # setting both from it made every card read "Walmart · Walmart". Nothing in
    # the payload carries a brand, and the leading title word is not one —
    # "The Purple Pillow" would yield "The".
    return Product(
        id=str(raw.get("product_id") or raw.get("position") or index),
        title=title,
        description=description,
        brand=None,
        price=price,
        original_price=original_price,
        rating=raw.get("rating") or 0.0,
        review_count=raw.get("reviews") or 0,
        vendor=raw.get("source") or "",
        vendor_logo=raw.get("source_icon"),
        image_url=raw.get("thumbnail"),
        product_url=raw.get("product_link") or "",
        specs=_extract_specs(
            f"{title} {description or ''}", price, original_price, raw
        ),
    )


def _parse_price_string(price: str) -> float:
    match = re.search(r"[\d,]+\.?\d*", price)
    return float(match.group().replace(",", "")) if match else 0.0
