from dataclasses import dataclass

import numpy as np

from app import config
from app.features.attribute_matrix import AttributeMatrix
from app.models import Product


@dataclass
class StandardizedModel:
    mu: np.ndarray
    sigma: np.ndarray
    weights: np.ndarray
    scaled_rows: np.ndarray
    product_ids: list[str]


def _build_weight_vector(matrix: AttributeMatrix, products: list[Product]) -> list[float]:
    spec_tier: dict[str, str] = {}
    for product in products:
        for spec in product.specs:
            if isinstance(spec.value, int | float) and spec.name not in spec_tier:
                spec_tier[spec.name] = spec.weight_tier

    spec_weights = [
        config.CATEGORY_WEIGHTS[spec_tier.get(name, "secondary")] for name in matrix.spec_names
    ]
    embedding_weights = [config.CATEGORY_WEIGHTS["soft"]] * matrix.embedding_dim
    return spec_weights + embedding_weights


def fit_standardization(matrix: AttributeMatrix, products: list[Product]) -> StandardizedModel:
    A = np.array(matrix.rows, dtype=float)
    mu = A.mean(axis=0)
    sigma = np.where(A.std(axis=0) == 0, 1.0, A.std(axis=0))
    z = (A - mu) / sigma
    weights = np.array(_build_weight_vector(matrix, products))
    scaled_rows = z * weights

    return StandardizedModel(
        mu=mu,
        sigma=sigma,
        weights=weights,
        scaled_rows=scaled_rows,
        product_ids=matrix.product_ids,
    )


def _cosine_similarity(u: np.ndarray, v: np.ndarray) -> float:
    denom = np.linalg.norm(u) * np.linalg.norm(v)
    if denom == 0:
        return 0.0
    return float(np.dot(u, v) / denom)


def scale_reference_vector(model: StandardizedModel, vector: list[float]) -> np.ndarray:
    return ((np.array(vector, dtype=float) - model.mu) / model.sigma) * model.weights


def compute_weighted_similarities(
    model: StandardizedModel, reference_vector: list[float]
) -> dict[str, float]:
    ref_scaled = scale_reference_vector(model, reference_vector)
    return {
        product_id: _cosine_similarity(ref_scaled, model.scaled_rows[i])
        for i, product_id in enumerate(model.product_ids)
    }
