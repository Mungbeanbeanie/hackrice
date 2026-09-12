import httpx
import pytest

from app import config
from app.ingestion import serpapi_client


def test_raises_when_key_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "SERPAPI_API_KEY", None)
    with pytest.raises(RuntimeError, match="SERPAPI_API_KEY is not set"):
        serpapi_client.search_products("anything")


def test_wraps_network_failure_as_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config, "SERPAPI_API_KEY", "fake-key")

    def raise_timeout(*args: object, **kwargs: object) -> None:
        raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(httpx, "get", raise_timeout)

    with pytest.raises(RuntimeError, match="SerpAPI request failed"):
        serpapi_client.search_products("anything")


def test_second_search_serves_from_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "SERPAPI_API_KEY", "fake-key")

    store: dict[str, str] = {}
    monkeypatch.setattr(serpapi_client.cache, "_get", store.get)
    monkeypatch.setattr(
        serpapi_client.cache,
        "_setex",
        lambda k, ttl, payload: store.update({k: payload}),
    )

    calls = 0

    def fake_get(*args: object, **kwargs: object) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={"shopping_results": [{"position": 1, "title": "pillow"}]},
            request=httpx.Request("GET", serpapi_client.SERPAPI_URL),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    first = serpapi_client.search_products("pillow")
    second = serpapi_client.search_products("pillow")

    assert calls == 1
    assert [p.title for p in second] == [p.title for p in first]


def test_empty_results_are_not_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "SERPAPI_API_KEY", "fake-key")
    monkeypatch.setattr(serpapi_client.cache, "_get", lambda key: None)

    def fail_on_write(key: str, ttl: int, payload: str) -> None:
        raise AssertionError("empty result list was cached")

    monkeypatch.setattr(serpapi_client.cache, "_setex", fail_on_write)
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: httpx.Response(
            200,
            json={"shopping_results": []},
            request=httpx.Request("GET", serpapi_client.SERPAPI_URL),
        ),
    )

    assert serpapi_client.search_products("nothing matches this") == []


def test_parse_product_handles_missing_fields() -> None:
    product = serpapi_client._parse_product({"position": 1}, 0)
    assert product.id == "1"
    assert product.price == 0.0
    # Price is always extractable, so it is the one spec every listing carries.
    assert [s.name for s in product.specs] == ["price"]


def test_brand_is_not_the_retailer() -> None:
    # `source` is the merchant. Assigning it to both fields made every card read
    # "Walmart · Walmart".
    product = serpapi_client._parse_product(
        {"position": 1, "title": "Contour Pillow", "source": "Walmart"}, 0
    )
    assert product.vendor == "Walmart"
    assert product.brand is None


def test_extracts_numeric_and_categorical_specs() -> None:
    raw = {
        "position": 1,
        "title": "Memory Foam Pillow Queen 18 in",
        "snippet": "Cooling gel",
        "extracted_price": 40.0,
        "extracted_old_price": 50.0,
        "rating": 4.5,
        "reviews": 120,
    }
    specs = {s.name: s.value for s in serpapi_client._parse_product(raw, 0).specs}
    assert specs["price"] == 40.0
    assert specs["discount_pct"] == 20.0
    assert specs["rating"] == 4.5
    assert specs["review_count"] == 120.0
    assert specs["measure_in"] == 18.0
    assert specs["size"] == "queen"


def test_unit_aliases_collapse_to_one_spec_name() -> None:
    # "18 inches" and "18 in" must land in the same matrix column, or each
    # spelling produces a half-filled feature the z-scoring cannot align.
    names = [
        {s.name for s in serpapi_client._parse_product({"title": t}, 0).specs}
        for t in ("Pillow 18 inches", "Pillow 18 in", "Pillow 18 inch")
    ]
    assert all("measure_in" in n for n in names)


def test_description_carries_snippet_and_extensions() -> None:
    # The only spec-bearing prose in the payload; dropping it left Layer 1
    # matching on titles alone.
    raw = {
        "position": 1,
        "title": "Pillow",
        "snippet": "Latex core",
        "extensions": ["Free delivery"],
    }
    product = serpapi_client._parse_product(raw, 0)
    assert product.description is not None
    assert "Latex core" in product.description
    assert "Free delivery" in product.description


def test_parse_product_handles_explicit_nulls() -> None:
    # SerpAPI sends nulls as well as omitting keys, and a null rating would fail
    # Product's non-optional float.
    raw = {
        "product_id": None,
        "position": None,
        "title": None,
        "rating": None,
        "reviews": None,
        "source": None,
        "price": None,
        "product_link": None,
    }
    product = serpapi_client._parse_product(raw, 3)
    assert product.id == "3"
    assert product.rating == 0.0
    assert product.review_count == 0


def test_parse_products_get_unique_ids_without_identifiers() -> None:
    products = [serpapi_client._parse_product({}, i) for i in range(3)]
    assert len({p.id for p in products}) == 3
