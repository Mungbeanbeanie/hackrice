import hashlib
import json

import redis

from app import config
from app.models import Product

_client: redis.Redis | None = None


def _get_client() -> redis.Redis:
    global _client
    if _client is None:
        if not config.CACHE_URL:
            raise RuntimeError("CACHE_URL is not set")
        _client = redis.Redis.from_url(config.CACHE_URL, decode_responses=True)
    return _client


def hash_key(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def get_cached_search(query_hash: str) -> list[Product] | None:
    raw = _get_client().get(f"search:{query_hash}")
    if raw is None:
        return None
    return [Product.model_validate(p) for p in json.loads(raw)]


def set_cached_search(query_hash: str, products: list[Product], ttl: int = 3600) -> None:
    payload = json.dumps([p.model_dump(mode="json") for p in products])
    _get_client().setex(f"search:{query_hash}", ttl, payload)


def get_cached_embedding(text_hash: str) -> list[float] | None:
    raw = _get_client().get(f"embedding:{text_hash}")
    if raw is None:
        return None
    return json.loads(raw)


def set_cached_embedding(text_hash: str, embedding: list[float], ttl: int = 86400) -> None:
    _get_client().setex(f"embedding:{text_hash}", ttl, json.dumps(embedding))
