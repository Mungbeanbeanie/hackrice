import logging
from dataclasses import dataclass

from app.features import embeddings, lexical
from app.models import Product

logger = logging.getLogger(__name__)


@dataclass
class AttributeMatrix:
    product_ids: list[str]
    spec_names: list[str]
    embedding_dim: int
    rows: list[list[float]]

    @property
    def numeric_dim(self) -> int:
        return len(self.spec_names)


def _product_text(product: Product) -> str:
    text_specs = " ".join(
        str(s.value) for s in product.specs if not isinstance(s.value, int | float)
    )
    parts = (product.title, product.description or "", text_specs)
    return " ".join(p for p in parts if p).strip()


def _numeric_row(product: Product | None, spec_names: list[str]) -> list[float]:
    if product is None:
        return [0.0] * len(spec_names)
    values = {
        s.name: s.value for s in product.specs if isinstance(s.value, int | float)
    }
    return [float(values.get(name, 0.0)) for name in spec_names]


def _l2_normalize(values: list[float]) -> list[float]:
    norm = sum(v * v for v in values) ** 0.5
    return [v / norm for v in values] if norm else values


def build_vector_space(
    products: list[Product], reference_text: str, target: Product | None = None
) -> tuple[AttributeMatrix, list[float]]:
    """Build matrix A and the reference vector to compare against it.

    Candidates and reference are built together rather than in two calls: the
    reference has to land in the same space as the rows, and with the embeddings
    API that is also one network round trip instead of two.

    The embedding model is primary. Any failure — no credits, no key, a timeout —
    downgrades the whole space to TF-IDF rather than failing the request. Ranking
    within a single shopping query's results is largely lexical, so the offline
    path degrades quality without breaking the feature.
    """
    texts = [_product_text(p) for p in products]

    try:
        vectors = embeddings.embed_texts([*texts, reference_text])
        text_rows, reference_text_vector = vectors[:-1], vectors[-1]
    except Exception as exc:
        # Message only, no traceback: when the cause is standing (an expired key,
        # an empty balance) this fires on every single request, and a stack per
        # search buries the errors worth reading.
        logger.warning(
            "Embeddings unavailable (%s: %s), ranking %d candidates with TF-IDF",
            type(exc).__name__,
            exc,
            len(products),
        )
        text_rows, reference_text_vector = lexical.tfidf_vectors(texts, reference_text)

    spec_names = sorted(
        {s.name for p in products for s in p.specs if isinstance(s.value, int | float)}
    )
    embedding_dim = len(text_rows[0]) if text_rows else 0

    # Each block is normalized on its own before they are concatenated. Without
    # it the ~1536 text dimensions swamp a handful of numeric ones by sheer
    # count, and Layer 2's weight matrix cannot shift the balance back.
    rows = [
        _l2_normalize(_numeric_row(p, spec_names)) + _l2_normalize(list(text_row))
        for p, text_row in zip(products, text_rows, strict=True)
    ]
    reference_vector = _l2_normalize(_numeric_row(target, spec_names)) + _l2_normalize(
        list(reference_text_vector)
    )

    return (
        AttributeMatrix(
            product_ids=[p.id for p in products],
            spec_names=spec_names,
            embedding_dim=embedding_dim,
            rows=rows,
        ),
        reference_vector,
    )
