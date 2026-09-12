from app import config
from app.models import ComparisonResult, Product, Tier


def _assign_tier(spec_match: float, similarity: float, has_reviews: bool) -> Tier:
    # spec_match and similarity arrive normalized against the best candidate in
    # this result set, so the thresholds read as "within 85% of the closest match
    # found" rather than as absolute cosines. Absolute ones were miscalibrated:
    # measured similarity on a real result set spanned 0.016 to 0.758, so a fixed
    # 0.85 bar put essentially every candidate in Tier 3.
    #
    # Unrated products cannot reach Tier 1 or 2 whatever they score. With v=0 the
    # Bayesian estimator returns exactly C, the category baseline, which clears
    # MIN_QUALITY_THRESHOLD for free — on a real result set that was 23 of 39
    # candidates being presented as quality-verified on no evidence. Tier 3 is
    # where an unverified-but-cheap listing belongs.
    if not has_reviews:
        return Tier.TIER_3
    if spec_match >= config.SPEC_MATCH_TIER1:
        return Tier.TIER_1
    if spec_match >= config.SPEC_MATCH_TIER2 or similarity >= config.SPEC_MATCH_TIER1:
        return Tier.TIER_2
    return Tier.TIER_3


def _normalized(scores: dict[str, float]) -> dict[str, float]:
    best = max(scores.values(), default=0.0)
    if best <= 0:
        return dict.fromkeys(scores, 0.0)
    return {k: max(v, 0.0) / best for k, v in scores.items()}


def rank_candidates(
    products: list[Product],
    quality_scores: dict[str, float],
    similarities: dict[str, float],
    spec_matches: dict[str, float],
    target_price: float | None = None,
) -> list[ComparisonResult]:
    norm_similarities = _normalized(similarities)
    norm_spec_matches = _normalized(spec_matches)

    results = []
    for product in products:
        quality = quality_scores.get(product.id)
        similarity = similarities.get(product.id)
        spec_match = spec_matches.get(product.id)
        if quality is None or similarity is None or spec_match is None:
            continue
        if quality < config.MIN_QUALITY_THRESHOLD or product.price <= 0:
            continue

        # Normalized scores decide the tier; the raw cosine is what gets stored
        # and shown. Reporting the normalized one would label the best candidate
        # a 100% match in every search, however poor the field actually was.
        # Sort order is unaffected either way — normalizing divides every
        # candidate by the same constant.
        similarity = similarities[product.id]
        value_score = quality * similarity / product.price
        tier = _assign_tier(
            norm_spec_matches[product.id],
            norm_similarities[product.id],
            product.review_count > 0,
        )

        # A candidate priced above the target is not a saving. Left signed, it
        # reached the UI as "Save $-34".
        savings_amount = None
        savings_percent = None
        if target_price and target_price > product.price:
            savings_amount = target_price - product.price
            savings_percent = savings_amount / target_price * 100

        results.append(
            ComparisonResult(
                candidate=product,
                similarity=similarity,
                quality_score=quality,
                value_score=value_score,
                tier=tier,
                savings_amount=savings_amount,
                savings_percent=savings_percent,
            )
        )

    return sorted(results, key=lambda r: (r.tier.value, -r.value_score))
