from typing import cast

import openai

from app import cache, config

EMBEDDING_MODEL = "text-embedding-3-small"

_client: openai.OpenAI | None = None


def _get_client() -> openai.OpenAI:
    global _client
    if _client is None:
        if not config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set")
        # The SDK default is a 600s timeout — a stalled embeddings call would
        # hang the request for ten minutes behind an already-slow search.
        _client = openai.OpenAI(
            api_key=config.OPENAI_API_KEY, timeout=20.0, max_retries=2
        )
    return _client


# Wrapped the way serpapi_client wraps its HTTP errors: an exhausted quota or a
# stalled embeddings call is an upstream outage the route can answer with a 502,
# and openai's own exception types shouldn't leak past this module to say so.
def _create(texts: list[str]) -> list[list[float]]:
    try:
        response = _get_client().embeddings.create(model=EMBEDDING_MODEL, input=texts)
    except openai.OpenAIError as exc:
        raise RuntimeError(f"Embedding request failed: {exc}") from exc
    return [data.embedding for data in response.data]


def embed_text(text: str) -> list[float]:
    key = cache.hash_key(text)
    cached = cache.get_cached_embedding(key)
    if cached is not None:
        return cached

    embedding = _create([text])[0]
    cache.set_cached_embedding(key, embedding)
    return embedding


def embed_texts(texts: list[str]) -> list[list[float]]:
    keys = [cache.hash_key(text) for text in texts]
    cached = [cache.get_cached_embedding(key) for key in keys]

    missing_indices = [i for i, embedding in enumerate(cached) if embedding is None]
    if missing_indices:
        fetched = _create([texts[i] for i in missing_indices])
        for i, embedding in zip(missing_indices, fetched, strict=True):
            cached[i] = embedding
            cache.set_cached_embedding(keys[i], embedding)

    # every None slot was filled above (zip strict=True), so no Nones remain
    return cast(list[list[float]], cached)
