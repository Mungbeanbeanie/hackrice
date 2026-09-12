"""The cache is an optimization, never a dependency.

Both of these used to take down every search: an unset CACHE_URL raised
RuntimeError, and an unreachable server raised ConnectionError. Either one
must now be a miss instead.
"""

import pytest
import redis

from app import cache


def test_disabled_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cache.config, "CACHE_URL", None)
    monkeypatch.setattr(cache, "_client", None)

    assert cache.get_cached_embedding("k") is None
    assert cache.get_cached_search("k") is None
    cache.set_cached_embedding("k", [1.0])
    cache.set_cached_search("k", [])


def test_degrades_when_server_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    class Unreachable:
        def get(self, key: str) -> str:
            raise redis.ConnectionError("down")

        def setex(self, key: str, ttl: int, payload: str) -> None:
            raise redis.ConnectionError("down")

    monkeypatch.setattr(cache, "_get_client", lambda: Unreachable())

    assert cache.get_cached_embedding("k") is None
    assert cache.get_cached_search("k") is None
    cache.set_cached_embedding("k", [1.0])
    cache.set_cached_search("k", [])
