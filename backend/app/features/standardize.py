from dataclasses import dataclass

import numpy as np

from app import config
from app.features.attribute_matrix import AttributeMatrix
from app.features.svd import cosine_similarity
from app.models import Product


@dataclass
class StandardizedModel:
    mu: np.ndarray
    sigma: np.ndarray
    weights: np.ndarray
    scaled_rows: np.ndarray
    product_ids: list[str]


def _build_weight_vector(
    matrix: AttributeMatrix, products: list[Product]
) -> list[float]:
    spec_tier: dict[str, str] = {}
    for product in products:
        for spec in product.specs:
            if isinstance(spec.value, int | float) and spec.name not in spec_tier:
                spec_tier[spec.name] = spec.weight_tier

    # Each block is divided by the square root of its own width. After z-scoring
    # every dimension carries unit variance, so a block's influence on the cosine
    # grows with how many dimensions it has — and the text block has ~1536 of
    # them against a handful of numeric specs. Without this the weights are
    # decorative: the text block wins on count no matter what W says.
    n_specs = len(matrix.spec_names)
    spec_scale = n_specs**0.5 or 1.0
    embedding_scale = matrix.embedding_dim**0.5 or 1.0

    spec_weights = [
        config.CATEGORY_WEIGHTS[spec_tier.get(name, "secondary")] / spec_scale
        for name in matrix.spec_names
    ]
    embedding_weights = [
        config.CATEGORY_WEIGHTS["soft"] / embedding_scale
    ] * matrix.embedding_dim
    return spec_weights + embedding_weights


def fit_standardization(
    matrix: AttributeMatrix, products: list[Product]
) -> StandardizedModel:
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


def scale_reference_vector(model: StandardizedModel, vector: list[float]) -> np.ndarray:
    return ((np.array(vector, dtype=float) - model.mu) / model.sigma) * model.weights


def compute_weighted_similarities(
    model: StandardizedModel, reference_vector: list[float]
) -> dict[str, float]:
    ref_scaled = scale_reference_vector(model, reference_vector)
    return {
        product_id: cosine_similarity(ref_scaled, model.scaled_rows[i])
        for i, product_id in enumerate(model.product_ids)
    }
