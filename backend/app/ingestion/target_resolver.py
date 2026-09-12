from urllib.parse import urlparse

from app.ingestion import serpapi_client
from app.models import Product, SearchMode, SearchQuery


def resolve_target(query: SearchQuery) -> Product | None:
    if query.mode == SearchMode.EXACT_PRODUCT:
        results = serpapi_client.search_products(query.raw_input)
        return results[0] if results else None

    if query.mode == SearchMode.URL:
        text = _extract_text_from_url(query.raw_input)
        results = serpapi_client.search_products(text)
        return results[0] if results else None

    return None


def _extract_text_from_url(url: str) -> str:
    path = urlparse(url).path
    segments = [segment for segment in path.split("/") if segment]
    slug = segments[-1] if segments else ""

    if "." in slug:
        slug = slug.rsplit(".", 1)[0]

    parts = slug.split("-")
    if parts and parts[-1].isdigit():
        parts = parts[:-1]

    return " ".join(parts).replace("_", " ").strip()
