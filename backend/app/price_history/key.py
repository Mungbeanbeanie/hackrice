import re


def _normalize_store(store: str) -> str:
    normalized = store.strip().lower()
    for prefix in ("https://", "http://", "www."):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
    return normalized.rstrip("/")


def normalize_product_key(title: str, brand: str, store: str) -> str:
    """Best-effort identity for a listing, so repeat views of "the same"
    product accumulate into one shared history instead of scattering across
    near-duplicate titles.

    Approximate, not solved: cross-retailer matching on title text alone is
    fuzzy by nature — same caveat as coupons/selector.py's store matching.
    """
    title_part = re.sub(r"[^a-z0-9]+", " ", title.strip().lower()).strip()
    return "|".join((title_part, brand.strip().lower(), _normalize_store(store)))
