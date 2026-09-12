import hashlib
import json
import re
from typing import cast

import redis

from app import config
from app.coupons.models import CouponOffer
from app.models import Product

_client: redis.Redis | None = None


def _get_client() -> redis.Redis | None:
    global _client
    if _client is None:
        if not config.CACHE_URL:
            return None
        _client = redis.Redis.from_url(
            config.CACHE_URL,
            decode_responses=True,
            # Without these the client inherits the OS TCP timeout. A refused
            # connection fails instantly, but a firewalled or black-holed host
            # does not: every request would block for ~75s on Linux, on top of
            # an already slow upstream search, to reach a cache that is down.
            # The cache exists to save seconds, so it may not cost minutes.
            socket_connect_timeout=2.0,
            socket_timeout=2.0,
        )
    return _client


# The cache is an optimization, never a dependency: with CACHE_URL unset (local
# dev, CI) or the server unreachable, every read misses and every write is
# dropped. A cache outage makes search slow, not dead.
#
# ponytail: from_url() connects lazily, so a bad URL surfaces here rather than
# in _get_client, and a dead server is re-dialled on every call, bounded by the
# timeouts above. Add a breaker only if reconnect cost shows up in a trace.
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
    # Normalized before hashing so "Purple Harmony Pillow" and "purple harmony
    # pillow" share one entry. Unnormalized, each spelling paid the full upstream
    # search — measured at 38-71s cold — for an identical result set.
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()


def get_cached_search(query_hash: str) -> list[Product] | None:
    raw = _get(f"search:{query_hash}")
    if raw is None:
        return None
    return [Product.model_validate(p) for p in json.loads(raw)]


def set_cached_search(
    query_hash: str, products: list[Product], ttl: int = 3600
) -> None:
    payload = json.dumps([p.model_dump(mode="json") for p in products])
    _setex(f"search:{query_hash}", ttl, payload)


def get_cached_embedding(text_hash: str) -> list[float] | None:
    raw = _get(f"embedding:{text_hash}")
    if raw is None:
        return None
    return json.loads(raw)


def set_cached_embedding(
    text_hash: str, embedding: list[float], ttl: int = 86400
) -> None:
    _setex(f"embedding:{text_hash}", ttl, json.dumps(embedding))


def get_cached_coupon(store: str) -> CouponOffer | None:
    raw = _get(f"coupon:{store}")
    if raw is None:
        return None
    return CouponOffer.model_validate(json.loads(raw))


def set_cached_coupon(store: str, offer: CouponOffer, ttl: int = 3600) -> None:
    _setex(f"coupon:{store}", ttl, json.dumps(offer.model_dump(mode="json")))
