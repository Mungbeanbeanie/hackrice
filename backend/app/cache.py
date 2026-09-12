import hashlib
import json
from typing import cast

import redis

from app import config
from app.models import Product

_client: redis.Redis | None = None


def _get_client() -> redis.Redis | None:
    global _client
    if _client is None:
        if not config.CACHE_URL:
            return None
        _client = redis.Redis.from_url(config.CACHE_URL, decode_responses=True)
    return _client


# The cache is an optimization, never a dependency: with CACHE_URL unset (local
# dev, CI) or the server unreachable, every read misses and every write is
# dropped. A cache outage makes search slow, not dead.
#
# ponytail: from_url() connects lazily, so a bad URL surfaces here rather than
# in _get_client, and a dead server is re-dialled on every call. Connection
# refused is fast; add a breaker only if it ever shows up in a trace.
def _get(key: str) -> str | None:
    client = _get_client()
    if client is None:
        return None
    try:
        # decode_responses=True on the client, so this is str, never bytes.
        return cast(str | None, client.get(key))
    except redis.RedisError:
        return None


def _setex(key: str, ttl: int, payload: str) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        client.setex(key, ttl, payload)
    except redis.RedisError:
        pass


def hash_key(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def get_cached_search(query_hash: str) -> list[Product] | None:
    raw = _get(f"search:{query_hash}")
    if raw is None:
        return None
    return [Product.model_validate(p) for p in json.loads(raw)]


def set_cached_search(query_hash: str, products: list[Product], ttl: int = 3600) -> None:
    payload = json.dumps([p.model_dump(mode="json") for p in products])
    _setex(f"search:{query_hash}", ttl, payload)


def get_cached_embedding(text_hash: str) -> list[float] | None:
    raw = _get(f"embedding:{text_hash}")
    if raw is None:
        return None
    return json.loads(raw)


def set_cached_embedding(text_hash: str, embedding: list[float], ttl: int = 86400) -> None:
    _setex(f"embedding:{text_hash}", ttl, json.dumps(embedding))
