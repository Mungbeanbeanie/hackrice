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


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch, serving whatever the cache already holds.

    Errors propagate: attribute_matrix.build_vector_space catches them and falls
    back to TF-IDF. Swallowing them here would return a half-built space.
    """
    keys = [cache.hash_key(text) for text in texts]
    cached = [cache.get_cached_embedding(key) for key in keys]

    missing_indices = [i for i, embedding in enumerate(cached) if embedding is None]
    if missing_indices:
        response = _get_client().embeddings.create(
            model=EMBEDDING_MODEL,
            input=[texts[i] for i in missing_indices],
        )
        for i, data in zip(missing_indices, response.data, strict=True):
            cached[i] = data.embedding
            cache.set_cached_embedding(keys[i], data.embedding)

    # every None slot was filled above (zip strict=True), so no Nones remain
    return cast(list[list[float]], cached)
