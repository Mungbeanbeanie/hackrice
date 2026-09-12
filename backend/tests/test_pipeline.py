from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import Product

client = TestClient(app)


def _product(id: str, title: str = "Widget", price: float = 10.0) -> Product:
    return Product(
        id=id,
        title=title,
        description=None,
        brand="b",
        price=price,
        original_price=None,
        rating=4.0,
        review_count=10,
        vendor="v",
        vendor_logo=None,
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


def _fake_embeddings(texts: list[str]) -> list[list[float]]:
    return [[0.1, 0.2, 0.3] for _ in texts]


def test_search_makes_one_upstream_call_and_splits_target_from_candidates() -> None:
    results = [_product("t1"), _product("c1"), _product("c2")]
    with (
        patch(
            "app.routes.search.serpapi_client.search_products", return_value=results
        ) as search,
        patch("app.features.embeddings.embed_texts", side_effect=_fake_embeddings),
    ):
        response = client.post("/api/search", json={"query": "Nike Shoe"})

    assert response.status_code == 200
    # The regression guard: resolving the target used to cost a second search.
    assert search.call_count == 1
    body = response.json()
    assert body["targetProduct"]["id"] == "t1"
    returned = {p["id"] for tier in body["tiers"].values() for p in tier}
    assert returned <= {"c1", "c2"}


def test_candidates_and_reference_share_one_embedding_call() -> None:
    results = [_product("t1"), _product("c1"), _product("c2")]
    with (
        patch("app.routes.search.serpapi_client.search_products", return_value=results),
        patch(
            "app.features.embeddings.embed_texts", side_effect=_fake_embeddings
        ) as embed,
    ):
        client.post("/api/search", json={"query": "Nike Shoe"})

    # Embedding the reference separately doubled the round trips per request.
    assert embed.call_count == 1
    assert len(embed.call_args.args[0]) == 3  # two candidates plus the reference


def test_search_falls_back_to_tfidf_when_embeddings_fail() -> None:
    # The regression this whole pass exists for: with the OpenAI account out of
    # credits, the uncaught RateLimitError escaped as a bare 500 and every real
    # search died roughly a minute in.
    results = [
        _product("t1", title="Contour Memory Foam Pillow", price=120.0),
        _product("c1", title="Contour Memory Foam Pillow Generic", price=40.0),
        _product("c2", title="Unrelated Garden Hose", price=20.0),
    ]
    with (
        patch("app.routes.search.serpapi_client.search_products", return_value=results),
        patch(
            "app.features.embeddings.embed_texts",
            side_effect=RuntimeError("insufficient_quota"),
        ),
    ):
        response = client.post("/api/search", json={"query": "Contour Pillow"})

    assert response.status_code == 200
    returned = [p for tier in response.json()["tiers"].values() for p in tier]
    assert {p["id"] for p in returned} == {"c1", "c2"}
    # TF-IDF still has to rank: the near-identical title must beat the hose.
    by_id = {p["id"]: p["matchScore"] for p in returned}
    assert by_id["c1"] > by_id["c2"]


def test_description_mode_keeps_every_result_as_a_candidate() -> None:
    results = [_product("c1"), _product("c2")]
    with (
        patch("app.routes.search.serpapi_client.search_products", return_value=results),
        patch("app.features.embeddings.embed_texts", side_effect=_fake_embeddings),
    ):
        response = client.post(
            "/api/search", json={"query": "a very long descriptive search query here"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["targetProduct"] is None
