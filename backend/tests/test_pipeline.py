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
    with patch("app.routes.search.serpapi_client.search_products", return_value=[]):
        response = client.post(
            "/api/search", json={"query": "a very long descriptive search query here"}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["tiers"] == {"tier1": [], "tier2": [], "tier3": []}


def test_search_404s_when_target_not_found() -> None:
    with patch("app.routes.search.serpapi_client.search_products", return_value=[]):
        response = client.post("/api/search", json={"query": "Nike Shoe"})
    assert response.status_code == 404


def test_search_502s_when_upstream_fails() -> None:
    with patch(
        "app.routes.search.serpapi_client.search_products",
        side_effect=RuntimeError("SerpAPI request failed: read operation timed out"),
    ):
        response = client.post("/api/search", json={"query": "Nike Shoe"})
    assert response.status_code == 502


def test_search_makes_one_upstream_call_and_splits_target_from_candidates() -> None:
    results = [_product("t1"), _product("c1"), _product("c2")]
    fake_embedding = [0.1, 0.2, 0.3]
    with (
        patch(
            "app.routes.search.serpapi_client.search_products", return_value=results
        ) as search,
        patch("app.features.embeddings.embed_text", return_value=fake_embedding),
        patch(
            "app.features.embeddings.embed_texts",
            return_value=[fake_embedding, fake_embedding],
        ),
    ):
        response = client.post("/api/search", json={"query": "Nike Shoe"})

    assert response.status_code == 200
    # The regression guard: resolving the target used to cost a second search.
    assert search.call_count == 1
    body = response.json()
    assert body["targetProduct"]["id"] == "t1"
    returned = {p["id"] for tier in body["tiers"].values() for p in tier}
    assert returned <= {"c1", "c2"}


def test_description_mode_keeps_every_result_as_a_candidate() -> None:
    results = [_product("c1"), _product("c2")]
    fake_embedding = [0.1, 0.2, 0.3]
    with (
        patch("app.routes.search.serpapi_client.search_products", return_value=results),
        patch("app.features.embeddings.embed_text", return_value=fake_embedding),
        patch(
            "app.features.embeddings.embed_texts",
            return_value=[fake_embedding, fake_embedding],
        ),
    ):
        response = client.post(
            "/api/search", json={"query": "a very long descriptive search query here"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["targetProduct"] is None
