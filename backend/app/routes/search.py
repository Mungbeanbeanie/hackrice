import re

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app import analytics
from app.features import attribute_matrix, standardize, svd
from app.ingestion import serpapi_client, target_resolver
from app.models import ComparisonResult, Product, SearchMode, Tier
from app.scoring import quality, value

router = APIRouter()


class SearchRequestBody(BaseModel):
    query: str


class WireProductSpec(BaseModel):
    key: str
    value: str


class WireProduct(BaseModel):
    id: str
    name: str
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
    tier: int
    badge: str | None = None


class Tiers(BaseModel):
    tier1: list[WireProduct]
    tier2: list[WireProduct]
    tier3: list[WireProduct]


class SearchApiResponse(BaseModel):
    query: str
    targetProduct: WireProduct | None
    tiers: Tiers


# Above this many words the input reads as a functional description rather than
# a product name, so no target is resolved.
#
# Known limitation: a short functional phrase ("ergonomic memory foam pillow",
# 4 words) resolves a target it should not, and the top result then becomes a
# baseline it was never meant to be. Deciding from the top result's similarity
# to the query instead would be accurate, but couples mode inference to scoring
# for a wrong answer at one edge.
EXACT_PRODUCT_MAX_WORDS = 4


def _infer_mode(raw_input: str) -> SearchMode:
    text = raw_input.strip()
    # A pasted link routinely loses its scheme ("amazon.com/dp/..."), and since
    # a URL carries no whitespace it would then pass the <=4-word exact-product
    # test and get sent to SerpAPI verbatim, which matches nothing.
    if text.startswith(("http://", "https://")) or re.match(
        r"^[\w-]+(\.[\w-]+)+/", text
    ):
        return SearchMode.URL
    if len(text.split()) <= EXACT_PRODUCT_MAX_WORDS:
        return SearchMode.EXACT_PRODUCT
    return SearchMode.DESCRIPTION


def _tier_to_int(tier: Tier) -> int:
    return {Tier.TIER_1: 1, Tier.TIER_2: 2, Tier.TIER_3: 3}[tier]


def _format_spec(value: float | str) -> str:
    # Extracted specs are floats, so "queen" survives but 6.0 would reach the UI
    # chips as "6.0" and a review count as "1200.0".
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _to_wire_product(
    product: Product, comparison: ComparisonResult | None = None
) -> WireProduct:
    if comparison is not None:
        match_score = round(comparison.similarity * 100, 1)
        savings = comparison.savings_amount
        savings_percent = comparison.savings_percent
        tier = _tier_to_int(comparison.tier)
    else:
        match_score = 100.0
        savings = None
        savings_percent = None
        tier = 1

    return WireProduct(
        id=product.id,
        name=product.title,
        brand=product.brand or "",
        price=product.price,
        originalPrice=product.original_price,
        image=product.image_url or "",
        retailer=product.vendor,
        retailerLogo=product.vendor_logo,
        url=product.product_url,
        rating=product.rating,
        reviewCount=product.review_count,
        specs=[
            WireProductSpec(key=s.name, value=_format_spec(s.value))
            for s in product.specs
        ],
        matchScore=match_score,
        savings=savings,
        savingsPercent=round(savings_percent, 1) if savings_percent else None,
        tier=tier,
    )


@router.post("/api/search", response_model=SearchApiResponse)
def search(body: SearchRequestBody, request: Request) -> SearchApiResponse:
    mode = _infer_mode(body.query)
    search_text = (
        target_resolver.url_to_text(body.query)
        if mode == SearchMode.URL
        else body.query
    )

    # One upstream call, not two. Resolving the target separately and then
    # re-searching on its title doubled latency and quota for the same result
    # set — and the cache could not dedupe the pair, since the raw query and the
    # resolved title hash differently.
    try:
        results = serpapi_client.search_products(search_text)
    except RuntimeError as exc:
        raise HTTPException(502, f"Product search upstream unavailable: {exc}") from exc

    # Recorded here, before the mode branch, so there is one call site rather
    # than one per return path — and so searches that die on the 404 below
    # still count as the real user attempts they were.
    analytics.record_search(request, body.query, mode.value, len(results))

    if mode == SearchMode.DESCRIPTION:
        target, candidates = None, results
    else:
        if not results:
            raise HTTPException(404, "Target product not found")
        target, candidates = results[0], results[1:]

    target_price = target.price if target is not None else None
    target_wire = _to_wire_product(target) if target is not None else None

    if not candidates:
        return SearchApiResponse(
            query=body.query,
            targetProduct=target_wire,
            tiers=Tiers(tier1=[], tier2=[], tier3=[]),
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

    tier1: list[WireProduct] = []
    tier2: list[WireProduct] = []
    tier3: list[WireProduct] = []
    buckets = {1: tier1, 2: tier2, 3: tier3}
    for result in ranked:
        buckets[_tier_to_int(result.tier)].append(
            _to_wire_product(result.candidate, result)
        )

    return SearchApiResponse(
        query=body.query,
        targetProduct=target_wire,
        tiers=Tiers(tier1=tier1, tier2=tier2, tier3=tier3),
    )
