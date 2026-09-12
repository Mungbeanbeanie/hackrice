from app import config
from app.models import Product, Tier
from app.scoring import quality, value


def _product(
    id: str = "p1", price: float = 10.0, rating: float = 4.0, review_count: int = 5
) -> Product:
    return Product(
        id=id,
        title="t",
        description=None,
        brand="b",
        price=price,
        original_price=None,
        rating=rating,
        review_count=review_count,
        vendor="v",
        vendor_logo=None,
        image_url=None,
        product_url="u",
        specs=[],
    )


def test_compute_quality_handles_zero_reviews() -> None:
    product = _product(review_count=0, rating=0.0)
    score = quality.compute_quality(product)
    assert isinstance(score, float)


def test_compute_quality_scores_handles_empty_list() -> None:
    assert quality.compute_quality_scores([]) == {}


def test_rank_candidates_skips_zero_price_products() -> None:
    product = _product(price=0.0)
    results = value.rank_candidates(
        [product], {product.id: 5.0}, {product.id: 1.0}, {product.id: 1.0}
    )
    assert results == []


def test_rank_candidates_filters_below_quality_threshold() -> None:
    product = _product()
    low_quality = config.MIN_QUALITY_THRESHOLD - 1
    results = value.rank_candidates(
        [product], {product.id: low_quality}, {product.id: 1.0}, {product.id: 1.0}
    )
    assert results == []


def test_rank_candidates_handles_empty_input() -> None:
    assert value.rank_candidates([], {}, {}, {}) == []


def test_unrated_product_cannot_rise_above_tier_3() -> None:
    # With v=0 the Bayesian estimator returns exactly C, which clears the
    # threshold for free. A perfect spec match must still not present a product
    # with no reviews as a verified equivalent.
    product = _product(review_count=0, rating=0.0)
    results = value.rank_candidates(
        [product], {product.id: 5.0}, {product.id: 1.0}, {product.id: 1.0}
    )
    assert [r.tier for r in results] == [Tier.TIER_3]


def test_rated_product_with_top_spec_match_reaches_tier_1() -> None:
    product = _product(review_count=500)
    results = value.rank_candidates(
        [product], {product.id: 5.0}, {product.id: 1.0}, {product.id: 1.0}
    )
    assert [r.tier for r in results] == [Tier.TIER_1]


def test_candidate_pricier_than_target_reports_no_savings() -> None:
    product = _product(price=200.0)
    results = value.rank_candidates(
        [product], {product.id: 5.0}, {product.id: 1.0}, {product.id: 1.0}, 100.0
    )
    assert results[0].savings_amount is None
    assert results[0].savings_percent is None


def test_tiers_spread_across_a_realistic_similarity_range() -> None:
    # Absolute cosine thresholds put this whole spread in Tier 3; normalizing
    # against the best candidate in the set is what makes them discriminate.
    products = [_product(id=f"p{i}", review_count=100) for i in range(3)]
    scores = dict(zip([p.id for p in products], [0.75, 0.5, 0.1], strict=True))
    quality_scores = dict.fromkeys(scores, 5.0)
    results = value.rank_candidates(products, quality_scores, scores, scores)
    assert {r.tier for r in results} == {Tier.TIER_1, Tier.TIER_2, Tier.TIER_3}
