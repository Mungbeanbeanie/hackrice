from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import Product, SpecAttribute

client = TestClient(app)


def _product(
    id: str,
    title: str = "Widget",
    price: float = 10.0,
    specs: list[SpecAttribute] | None = None,
) -> Product:
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
        specs=specs if specs is not None else [],
    )


def test_search_returns_empty_groups_when_no_candidates() -> None:
    with patch("app.routes.search.serpapi_client.search_products", return_value=[]):
        response = client.post(
            "/api/search", json={"query": "a very long descriptive search query here"}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["groups"] == {"same_spec": [], "same_job": [], "clears_floor": []}


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
    returned = {p["id"] for group in body["groups"].values() for p in group}
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
    returned = [p for group in response.json()["groups"].values() for p in group]
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


def _spec(name: str, value: float | str, tier: str = "hard") -> SpecAttribute:
    return SpecAttribute(name=name, value=value, weight_tier=tier)  # type: ignore[arg-type]


_SPECS = [
    _spec("price", 40.0, "secondary"),
    _spec("discount_pct", 20.0, "secondary"),
    _spec("rating", 4.5, "secondary"),
    _spec("review_count", 120.0, "secondary"),
    _spec("material", "memory foam"),
    _spec("measure_in", 18.0),
]


def _search_with_specs(query: str = "Nike Shoe"):
    results = [
        _product("t1", specs=_SPECS),
        _product("c1", specs=_SPECS),
        _product("c2", specs=[_spec("material", "latex"), _spec("measure_in", 24.0)]),
    ]
    with (
        patch("app.routes.search.serpapi_client.search_products", return_value=results),
        patch("app.features.embeddings.embed_texts", side_effect=_fake_embeddings),
    ):
        return client.post("/api/search", json={"query": query})


def test_commerce_specs_never_reach_the_wire() -> None:
    # Price and rating have their own places in the UI; left in specs they
    # crowded the comparison overlay out of showing anything physical.
    body = _search_with_specs().json()
    every_spec = [
        s
        for p in [
            body["targetProduct"],
            *[c for g in body["groups"].values() for c in g],
        ]
        for s in p["specs"]
    ]
    assert every_spec, "fixture must emit specs or this asserts nothing"
    keys = {s["key"] for s in every_spec}
    assert keys.isdisjoint({"price", "discount_pct", "rating", "review_count"})
    assert keys == {"material", "measure_in"}


def test_target_carries_short_but_no_rationale() -> None:
    # The target is the reference, not a candidate being argued for.
    target = _search_with_specs().json()["targetProduct"]
    assert target["short"] == "Widget"
    assert target["rationale"] is None
    assert all(s["verdict"] is None for s in target["specs"])


def test_candidates_carry_a_rationale_and_verdicts() -> None:
    body = _search_with_specs().json()
    candidates = [c for g in body["groups"].values() for c in g]
    assert candidates
    for c in candidates:
        assert c["rationale"]
        assert c["short"]
        # Both fixture candidates share the target's spec names, so every
        # verdict is comparable here.
        assert all(s["verdict"] is not None for s in c["specs"])


def test_description_mode_leaves_every_verdict_none() -> None:
    # No target resolved means nothing to compare any spec against.
    results = [_product("c1", specs=_SPECS), _product("c2", specs=_SPECS)]
    with (
        patch("app.routes.search.serpapi_client.search_products", return_value=results),
        patch("app.features.embeddings.embed_texts", side_effect=_fake_embeddings),
    ):
        response = client.post(
            "/api/search", json={"query": "a very long descriptive search query here"}
        )

    body = response.json()
    candidates = [c for g in body["groups"].values() for c in g]
    assert candidates
    assert all(s["verdict"] is None for c in candidates for s in c["specs"])
