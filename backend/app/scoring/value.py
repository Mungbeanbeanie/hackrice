from app import config
from app.models import ComparisonResult, Product, Tier


def _assign_tier(spec_match: float, similarity: float) -> Tier:
    if spec_match >= config.SPEC_MATCH_TIER1:
        return Tier.TIER_1
    if spec_match >= config.SPEC_MATCH_TIER2 or similarity >= config.SPEC_MATCH_TIER1:
        return Tier.TIER_2
    return Tier.TIER_3


def rank_candidates(
    products: list[Product],
    quality_scores: dict[str, float],
    similarities: dict[str, float],
    spec_matches: dict[str, float],
    target_price: float | None = None,
) -> list[ComparisonResult]:
    results = []
    for product in products:
        quality = quality_scores[product.id]
        if quality < config.MIN_QUALITY_THRESHOLD or product.price <= 0:
            continue

        similarity = similarities[product.id]
        value_score = quality * similarity / product.price
        tier = _assign_tier(spec_matches[product.id], similarity)

        savings_amount = target_price - product.price if target_price is not None else None
        savings_percent = (
            (savings_amount / target_price * 100)
            if target_price and savings_amount is not None
            else None
        )

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
