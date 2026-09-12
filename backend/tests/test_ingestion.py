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


def test_parse_product_handles_missing_fields() -> None:
    product = serpapi_client._parse_product({"position": 1})
    assert product.id == "1"
    assert product.price == 0.0
    assert product.specs == []
