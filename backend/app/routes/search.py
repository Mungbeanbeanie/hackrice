import re

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app import analytics
from app.features import attribute_matrix, standardize, svd
from app.ingestion import serpapi_client, target_resolver
from app.models import ComparisonResult, Group, Product, SearchMode
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


def _to_wire_product(
    product: Product,
    target_specs: dict[str, float | str] | None = None,
    comparison: ComparisonResult | None = None,
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
        savingsPercent=round(savings_percent, 1) if savings_percent else None,
        rationale=(
            explain.rationale(comparison, [s.verdict for s in specs])
            if comparison is not None
            else None
        ),
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

    buckets: dict[Group, list[WireProduct]] = {group: [] for group in Group}
    for result in ranked:
        buckets[result.group].append(
            _to_wire_product(result.candidate, target_specs, result)
        )

    return SearchApiResponse(
        query=body.query,
        targetProduct=target_wire,
        groups=Groups(
            same_spec=buckets[Group.SAME_SPEC],
            same_job=buckets[Group.SAME_JOB],
            clears_floor=buckets[Group.CLEARS_FLOOR],
        ),
    )
