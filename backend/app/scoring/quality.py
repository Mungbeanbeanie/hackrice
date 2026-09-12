from app import config
from app.models import Product


def compute_quality(product: Product, m: float | None = None, c: float | None = None) -> float:
    m = m if m is not None else config.BAYESIAN_M
    c = c if c is not None else config.BAYESIAN_C
    v = product.review_count
    R = product.rating
    return (v / (v + m)) * R + (m / (v + m)) * c


def compute_quality_scores(
    products: list[Product], m: float | None = None, c: float | None = None
) -> dict[str, float]:
    return {p.id: compute_quality(p, m, c) for p in products}
