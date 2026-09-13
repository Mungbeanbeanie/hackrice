import re
import statistics

import numpy as np
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app import analytics, config
from app.features import attribute_matrix, embeddings, standardize, svd
from app.ingestion import serpapi_client, target_resolver
from app.models import ComparisonResult, Group, Product, SearchMode, SpecAttribute
from app.scoring import explain, quality, value

router = APIRouter()


class SearchRequestBody(BaseModel):
    query: str


class WireProductSpec(BaseModel):
    key: str
    value: str
    # None when the target has no such spec to compare against — every spec in
    # description mode, where no target is resolved at all.
    verdict: explain.Verdict | None = None


class WireProduct(BaseModel):
    id: str
    name: str
    short: str
    brand: str
    price: float
    originalPrice: float | None = None
    image: str
    retailer: str
    retailerLogo: str | None = None
    url: str
    rating: float
    reviewCount: int
    specs: list[WireProductSpec]
    matchScore: float
    savings: float | None = None
    savingsPercent: float | None = None
    # Absent on the target product: it is the reference, not a candidate being
    # argued for.
    rationale: str | None = None
    badge: str | None = None


class Groups(BaseModel):
    same_spec: list[WireProduct]
    same_job: list[WireProduct]
    clears_floor: list[WireProduct]


class SearchApiResponse(BaseModel):
    query: str
    targetProduct: WireProduct | None
    groups: Groups
    # The mode the backend inferred, and the price every savings figure and
    # share bar is measured against. In description mode targetProduct is None
    # but baselinePrice is not — it is the median of the candidate set, which
    # the UI labels differently and must not present as a real product.
    mode: SearchMode
    baselinePrice: float | None = None


def _is_url(raw_input: str) -> bool:
    text = raw_input.strip()
    # A pasted link routinely loses its scheme ("amazon.com/dp/..."), so a bare
    # domain-looking prefix counts too, not just an explicit http(s) scheme.
    return bool(
        text.startswith(("http://", "https://"))
        or re.match(r"^[\w-]+(\.[\w-]+)+/", text)
    )


# Curated, not exhaustive — any brand or product line not on this list is
# invisible to the exact_product escalation below and the query stays in the
# safe default (description). Needs maintaining as new names come up.
#
# Generic-English words are qualified with their parent brand ("samsung
# galaxy", not bare "galaxy") to avoid false-positiving on unrelated queries;
# genuinely unambiguous ones stay bare.
_BRAND_NAMES = frozenset(
    {
        "purple",
        "casper",
        "tempur-pedic",
        "sealy",
        "serta",
        "saatva",
        "leesa",
        "nectar",
        "tuft & needle",
        "sleep number",
        "apple",
        "samsung",
        "sony",
        "lg",
        "bose",
        "jbl",
        "beats",
        "sonos",
        "logitech",
        "anker",
        "garmin",
        "fitbit",
        "gopro",
        "canon",
        "nikon",
        "dell",
        "hp",
        "lenovo",
        "microsoft",
        "google",
        "asus",
        "acer",
        "roku",
        "amazon",
        "dyson",
        "shark",
        "whirlpool",
        "kitchenaid",
        "cuisinart",
        "instant pot",
        "ninja",
        "keurig",
        "vitamix",
        "black+decker",
        "dewalt",
        "bosch",
        "philips",
        "panasonic",
        "irobot",
        "roomba",
        "nike",
        "adidas",
        "under armour",
        "the north face",
        "patagonia",
        "levi's",
        "reebok",
        "new balance",
        "puma",
        "vans",
        "columbia",
        "yeti",
        "coleman",
        "igloo",
        # Product-line names people search without the maker's name.
        "iphone",
        "ipad",
        "macbook",
        "airpods",
        "apple watch",
        "imac",
        "samsung galaxy",
        "playstation",
        "ps5",
        "ps4",
        "xbox",
        "surface pro",
        "surface laptop",
        "chromebook",
        "google pixel",
        "google nest",
        "kindle",
        "alexa",
        "amazon echo",
        "thinkpad",
        "nintendo switch",
        "nintendo",
        "walkman",
        "quietcomfort",
    }
)
_BRAND_PATTERN = re.compile(
    r"\b(?:"
    + "|".join(re.escape(b) for b in sorted(_BRAND_NAMES, key=len, reverse=True))
    + r")\b",
    re.IGNORECASE,
)


def _detected_brand(text: str) -> str | None:
    match = _BRAND_PATTERN.search(text)
    return match.group(0).lower() if match else None


def _semantic_match(a: str, b: str) -> float:
    # Never lets an OpenAI outage 502 the whole search over an optional
    # signal — same tolerance as attribute_matrix's TF-IDF fallback. Falls
    # back to "unconfirmed" (0.0), keeping mode inference on the safe default
    # (description).
    try:
        vectors = embeddings.embed_texts([a, b])
    except RuntimeError:
        return 0.0
    return svd.cosine_similarity(np.array(vectors[0]), np.array(vectors[1]))


# Price and rating already have their own places in the UI — as the price line,
# the savings figure and the rating chip. Left in specs they crowded out the
# physical attributes the comparison overlay exists to show, and a spec-by-spec
# table of a product against itself on price is not a comparison.
COMMERCE_SPECS = frozenset({"price", "discount_pct", "rating", "review_count"})


def _format_spec(value: float | str) -> str:
    # Extracted specs are floats, so "queen" survives but 6.0 would reach the UI
    # chips as "6.0" and a review count as "1200.0".
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _short(title: str) -> str:
    # Table column headers get two or three words, not a 90-character listing
    # title that would force the side-by-side view to scroll.
    return " ".join(title.split()[:3])


def _median_product(candidates: list[Product]) -> Product | None:
    """A synthetic "typical product" standing in for the target in description mode.

    A description names no product, so there was no baseline at all: every
    savings figure came back None and the share bar never rendered. The median
    of the candidate set is the honest answer to "compared to what" — half the
    market is cheaper, half dearer.

    Never returned to the client and never added to `candidates`: it has no URL,
    no reviews and nothing to buy, so as a row in the matrix it would be scored
    and rendered as a real listing.
    """
    prices = [c.price for c in candidates if c.price > 0]
    if not prices:
        return None

    # Only numeric specs have a median. Text specs (material, size) would need a
    # mode rather than a median, and picking the most common material would
    # assert a material the "typical product" does not actually have.
    numeric: dict[str, list[float]] = {}
    tiers: dict[str, str] = {}
    for candidate in candidates:
        for spec in candidate.specs:
            if isinstance(spec.value, int | float):
                numeric.setdefault(spec.name, []).append(float(spec.value))
                tiers[spec.name] = spec.weight_tier

    return Product(
        id="__median__",
        title="Typical product at this price",
        description=None,
        brand=None,
        price=statistics.median(prices),
        original_price=None,
        rating=statistics.median([c.rating for c in candidates]),
        review_count=int(statistics.median([c.review_count for c in candidates])),
        vendor="",
        vendor_logo=None,
        image_url=None,
        product_url="",
        specs=[
            SpecAttribute(
                name=name,
                value=statistics.median(values),
                weight_tier=tiers[name],  # type: ignore[arg-type]
            )
            for name, values in numeric.items()
        ],
    )


def _to_wire_product(
    product: Product,
    target_specs: dict[str, float | str] | None = None,
    comparison: ComparisonResult | None = None,
    baseline_label: str = "the original",
) -> WireProduct:
    if comparison is not None:
        match_score = round(comparison.similarity * 100, 1)
        savings = comparison.savings_amount
        savings_percent = comparison.savings_percent
    else:
        match_score = 100.0
        savings = None
        savings_percent = None

    specs = [
        WireProductSpec(
            key=s.name,
            value=_format_spec(s.value),
            verdict=explain.verdict(s.name, (target_specs or {}).get(s.name), s.value),
        )
        for s in product.specs
        if s.name not in COMMERCE_SPECS
    ]

    return WireProduct(
        id=product.id,
        name=product.title,
        short=_short(product.title),
        brand=product.brand or "",
        price=product.price,
        originalPrice=product.original_price,
        image=product.image_url or "",
        retailer=product.vendor,
        retailerLogo=product.vendor_logo,
        url=product.product_url,
        rating=product.rating,
        reviewCount=product.review_count,
        specs=specs,
        matchScore=match_score,
        savings=savings,
        savingsPercent=(
            round(savings_percent, 1) if savings_percent is not None else None
        ),
        rationale=(
            explain.rationale(comparison, [s.verdict for s in specs], baseline_label)
            if comparison is not None
            else None
        ),
    )


@router.post("/api/search", response_model=SearchApiResponse)
def search(body: SearchRequestBody, request: Request) -> SearchApiResponse:
    is_url = _is_url(body.query)
    search_text = target_resolver.url_to_text(body.query) if is_url else body.query

    # One upstream call, not two. Resolving the target separately and then
    # re-searching on its title doubled latency and quota for the same result
    # set — and the cache could not dedupe the pair, since the raw query and the
    # resolved title hash differently.
    try:
        results = serpapi_client.search_products(search_text)
    except RuntimeError as exc:
        raise HTTPException(502, f"Product search upstream unavailable: {exc}") from exc

    # Logs the user's apparent intent (a brand was named), not the final
    # resolved outcome — a brand-bearing query downgraded to description below
    # still counted as a real exact-product attempt. One analytics call site,
    # same as before; a 404 below still counts, no special-casing needed.
    brand = None if is_url else _detected_brand(body.query)
    provisional_mode = (
        SearchMode.URL
        if is_url
        else SearchMode.EXACT_PRODUCT
        if brand is not None
        else SearchMode.DESCRIPTION
    )
    analytics.record_search(request, body.query, provisional_mode.value, len(results))

    if is_url:
        if not results:
            raise HTTPException(404, "Target product not found")
        mode = SearchMode.URL
        target = target_resolver.pick_target(results, body.query, search_text)
    elif brand is not None:
        if not results:
            raise HTTPException(404, "Target product not found")
        # Both gates required: a brand named in the query but confirmed on a
        # DIFFERENT product (wrong brand) or a topically-similar-but-wrong
        # product (right brand, low semantic match) must not become the
        # target — either failure alone falls back to the safe default.
        candidate = target_resolver.pick_target(results, body.query, search_text)
        brand_confirmed = brand in candidate.title.lower()
        semantic_ok = (
            _semantic_match(body.query, candidate.title)
            >= config.EXACT_PRODUCT_MATCH_THRESHOLD
        )
        if brand_confirmed and semantic_ok:
            mode, target = SearchMode.EXACT_PRODUCT, candidate
        else:
            mode, target = SearchMode.DESCRIPTION, None
    else:
        mode, target = SearchMode.DESCRIPTION, None

    if mode == SearchMode.DESCRIPTION:
        candidates = results
        # Stands in for the target so savings, spec verdicts and the reference
        # vector all have something to measure against. Deliberately not
        # returned to the client — it is not a product anyone can buy.
        target = _median_product(candidates)
        target_wire = None
    else:
        # Only the DESCRIPTION-producing branches above ever set target=None.
        assert target is not None
        # Not results[1:] — the target is no longer guaranteed to be index 0.
        candidates = [p for p in results if p.id != target.id]
        target_wire = _to_wire_product(target)

    target_price = target.price if target is not None else None
    # Built once per request rather than scanning the target's spec list again
    # for every spec of every candidate.
    target_specs = (
        {s.name: s.value for s in target.specs} if target is not None else None
    )

    if not candidates:
        return SearchApiResponse(
            query=body.query,
            targetProduct=target_wire,
            groups=Groups(same_spec=[], same_job=[], clears_floor=[]),
            mode=mode,
            baselinePrice=target_price,
        )

    matrix, reference_vector = attribute_matrix.build_vector_space(
        candidates, search_text, target=target
    )

    svd_model = svd.fit_svd(matrix)
    similarities = svd.compute_similarities(svd_model, reference_vector)

    std_model = standardize.fit_standardization(matrix, candidates)
    spec_matches = standardize.compute_weighted_similarities(
        std_model, reference_vector
    )

    quality_scores = quality.compute_quality_scores(candidates)

    ranked = value.rank_candidates(
        candidates, quality_scores, similarities, spec_matches, target_price
    )

    baseline_label = (
        "the median price" if mode == SearchMode.DESCRIPTION else "the original"
    )

    buckets: dict[Group, list[WireProduct]] = {group: [] for group in Group}
    for result in ranked:
        buckets[result.group].append(
            _to_wire_product(result.candidate, target_specs, result, baseline_label)
        )

    return SearchApiResponse(
        query=body.query,
        targetProduct=target_wire,
        groups=Groups(
            same_spec=buckets[Group.SAME_SPEC],
            same_job=buckets[Group.SAME_JOB],
            clears_floor=buckets[Group.CLEARS_FLOOR],
        ),
        mode=mode,
        baselinePrice=target_price,
    )
