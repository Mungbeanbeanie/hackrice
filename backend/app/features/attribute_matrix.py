from dataclasses import dataclass

from app.features import embeddings
from app.models import Product


@dataclass
class AttributeMatrix:
    product_ids: list[str]
    spec_names: list[str]
    embedding_dim: int
    rows: list[list[float]]


def _product_text(product: Product) -> str:
    text_specs = " ".join(
        str(s.value) for s in product.specs if not isinstance(s.value, int | float)
    )
    return f"{product.title} {text_specs}".strip()


def build_attribute_matrix(products: list[Product]) -> AttributeMatrix:
    spec_names = sorted(
        {s.name for p in products for s in p.specs if isinstance(s.value, int | float)}
    )
    vecs = embeddings.embed_texts([_product_text(p) for p in products])
    embedding_dim = len(vecs[0]) if vecs else 0

    rows = []
    for product, vec in zip(products, vecs, strict=True):
        spec_values = {
            s.name: s.value for s in product.specs if isinstance(s.value, int | float)
        }
        numeric_row = [float(spec_values.get(name, 0.0)) for name in spec_names]
        rows.append(numeric_row + list(vec))

    return AttributeMatrix(
        product_ids=[p.id for p in products],
        spec_names=spec_names,
        embedding_dim=embedding_dim,
        rows=rows,
    )


def build_reference_vector(
    matrix: AttributeMatrix, text: str, product: Product | None = None
) -> list[float]:
    if product is not None:
        spec_values = {
            s.name: s.value for s in product.specs if isinstance(s.value, int | float)
        }
        numeric_part = [float(spec_values.get(name, 0.0)) for name in matrix.spec_names]
    else:
        numeric_part = [0.0] * len(matrix.spec_names)

    return numeric_part + embeddings.embed_text(text)
