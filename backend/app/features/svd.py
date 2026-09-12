from dataclasses import dataclass

import numpy as np

from app import config
from app.features.attribute_matrix import AttributeMatrix


@dataclass
class SVDModel:
    V: np.ndarray
    latent_rows: np.ndarray
    product_ids: list[str]


def fit_svd(matrix: AttributeMatrix, rank: int | None = None) -> SVDModel:
    A = np.array(matrix.rows, dtype=float)
    _, _, Vt = np.linalg.svd(A, full_matrices=False)
    r = min(rank or config.SVD_RANK, Vt.shape[0])
    V = Vt[:r].T
    latent_rows = A @ V
    return SVDModel(V=V, latent_rows=latent_rows, product_ids=matrix.product_ids)


def project(model: SVDModel, vector: list[float]) -> np.ndarray:
    return np.array(vector, dtype=float) @ model.V


def cosine_similarity(u: np.ndarray, v: np.ndarray) -> float:
    denom = np.linalg.norm(u) * np.linalg.norm(v)
    if denom == 0:
        return 0.0
    return float(np.dot(u, v) / denom)


def compute_similarities(
    model: SVDModel, reference_vector: list[float]
) -> dict[str, float]:
    ref_latent = project(model, reference_vector)
    return {
        product_id: cosine_similarity(ref_latent, model.latent_rows[i])
        for i, product_id in enumerate(model.product_ids)
    }
