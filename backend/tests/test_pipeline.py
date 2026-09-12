from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import Product

client = TestClient(app)


def _product(id: str, title: str = "Widget", price: float = 10.0) -> Product:
    return Product(
        id=id,
        title=title,
        brand="b",
        price=price,
        rating=4.0,
        review_count=10,
        vendor="v",
        image_url=None,
        product_url="u",
        specs=[],
    )


def test_search_returns_empty_tiers_when_no_candidates() -> None:
    with (
        patch("app.routes.search.target_resolver.resolve_target", return_value=None),
        patch("app.routes.search.serpapi_client.search_products", return_value=[]),
    ):
        response = client.post(
            "/api/search", json={"query": "a very long descriptive search query here"}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["tiers"] == {"tier1": [], "tier2": [], "tier3": []}


def test_search_404s_when_target_not_found() -> None:
    with patch("app.routes.search.target_resolver.resolve_target", return_value=None):
        response = client.post("/api/search", json={"query": "Nike Shoe"})
    assert response.status_code == 404


def test_search_does_not_crash_with_mocked_candidates() -> None:
    target = _product("t1")
    candidates = [_product("c1"), _product("c2")]
    fake_embedding = [0.1, 0.2, 0.3]
    with (
        patch("app.routes.search.target_resolver.resolve_target", return_value=target),
        patch(
            "app.routes.search.serpapi_client.search_products", return_value=candidates
        ),
        patch("app.features.embeddings.embed_text", return_value=fake_embedding),
        patch(
            "app.features.embeddings.embed_texts",
            return_value=[fake_embedding, fake_embedding],
        ),
    ):
        response = client.post("/api/search", json={"query": "Nike Shoe"})
    assert response.status_code == 200
