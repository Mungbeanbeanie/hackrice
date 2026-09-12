import openai

from app import cache, config

EMBEDDING_MODEL = "text-embedding-3-small"

_client: openai.OpenAI | None = None


def _get_client() -> openai.OpenAI:
    global _client
    if _client is None:
        if not config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set")
        _client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


def embed_text(text: str) -> list[float]:
    key = cache.hash_key(text)
    cached = cache.get_cached_embedding(key)
    if cached is not None:
        return cached

    response = _get_client().embeddings.create(model=EMBEDDING_MODEL, input=text)
    embedding = response.data[0].embedding
    cache.set_cached_embedding(key, embedding)
    return embedding


def embed_texts(texts: list[str]) -> list[list[float]]:
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

    return cached
