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
    assert product.specs == []


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
