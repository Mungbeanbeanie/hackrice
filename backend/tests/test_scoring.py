import pytest

from app import config
from app.models import Product
from app.scoring import quality, value


def _product(
    id: str = "p1", price: float = 10.0, rating: float = 4.0, review_count: int = 5
) -> Product:
    return Product(
        id=id,
        title="t",
        brand="b",
        price=price,
        rating=rating,
        review_count=review_count,
        vendor="v",
        image_url=None,
        product_url="u",
        specs=[],
    )


def test_compute_quality_handles_zero_reviews() -> None:
    product = _product(review_count=0, rating=0.0)
    score = quality.compute_quality(product)
    assert isinstance(score, float)


def test_compute_quality_handles_zero_denominator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config, "BAYESIAN_M", 0.0)
    product = _product(review_count=0)
    assert quality.compute_quality(product) == config.BAYESIAN_C


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


def test_rank_candidates_skips_product_missing_from_score_dicts() -> None:
    product = _product()
    assert value.rank_candidates([product], {}, {}, {}) == []
