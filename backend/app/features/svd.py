from dataclasses import dataclass

import numpy as np

from app import config
from app.features.attribute_matrix import AttributeMatrix


@dataclass
class SVDModel:
    # None when the candidate set was too small to decompose — see fit_svd.
    V: np.ndarray | None
    latent_rows: np.ndarray
    product_ids: list[str]


def fit_svd(matrix: AttributeMatrix, rank: int | None = None) -> SVDModel:
    A = np.array(matrix.rows, dtype=float)
    r = min(rank or config.SVD_RANK, *A.shape)

    # Below roughly 2r candidates the decomposition has no redundancy left to
    # discard, and projecting anyway inflates every cosine toward 1.0 — measured
    # on a real 39-candidate set, rank-5 latent similarity averaged 0.53 against
    # 0.23 for the same comparison unprojected. Skip it and compare in the full
    # space rather than manufacturing agreement.
    if A.shape[0] < 2 * r:
        return SVDModel(V=None, latent_rows=A, product_ids=matrix.product_ids)

    _, _, Vt = np.linalg.svd(A, full_matrices=False)
    V = Vt[:r].T
    return SVDModel(V=V, latent_rows=A @ V, product_ids=matrix.product_ids)


def project(model: SVDModel, vector: list[float]) -> np.ndarray:
    v = np.array(vector, dtype=float)
    return v if model.V is None else v @ model.V


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
