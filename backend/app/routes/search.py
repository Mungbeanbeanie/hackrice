import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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


def _infer_mode(raw_input: str) -> SearchMode:
    text = raw_input.strip()
    # A pasted link routinely loses its scheme ("amazon.com/dp/..."), and since
    # a URL carries no whitespace it would then pass the <=4-word exact-product
    # test and get sent to SerpAPI verbatim, which matches nothing.
    if text.startswith(("http://", "https://")) or re.match(
        r"^[\w-]+(\.[\w-]+)+/", text
    ):
        return SearchMode.URL
    if len(text.split()) <= 4:
        return SearchMode.EXACT_PRODUCT
    return SearchMode.DESCRIPTION


def _tier_to_int(tier: Tier) -> int:
    return {Tier.TIER_1: 1, Tier.TIER_2: 2, Tier.TIER_3: 3}[tier]


def _to_wire_product(
    product: Product, comparison: ComparisonResult | None = None
) -> WireProduct:
    if comparison is not None:
        match_score = round(comparison.similarity * 100, 1)
        savings = comparison.savings_amount
        tier = _tier_to_int(comparison.tier)
    else:
        match_score = 100.0
        savings = None
        tier = 1

    return WireProduct(
        id=product.id,
        name=product.title,
        brand=product.brand or "",
        price=product.price,
        image=product.image_url or "",
        retailer=product.vendor,
        url=product.product_url,
        rating=product.rating,
        reviewCount=product.review_count,
        specs=[WireProductSpec(key=s.name, value=str(s.value)) for s in product.specs],
        matchScore=match_score,
        savings=savings,
        tier=tier,
    )


@router.post("/api/search", response_model=SearchApiResponse)
def search(body: SearchRequestBody) -> SearchApiResponse:
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

    # Same treatment as the search call above: an embedding outage is an
    # upstream failure, not a bug in this handler, so it gets a 502 with a
    # reason rather than a bare 500.
    try:
        matrix = attribute_matrix.build_attribute_matrix(candidates)
        reference_vector = attribute_matrix.build_reference_vector(
            matrix, search_text, product=target
        )
    except RuntimeError as exc:
        raise HTTPException(502, f"Embedding service unavailable: {exc}") from exc

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
