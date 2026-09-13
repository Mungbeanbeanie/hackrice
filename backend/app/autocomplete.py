"""Trie-backed multi-suggestion autocomplete for the search bar.

Additive alongside the frontend's existing single-match ghost suggestion
(frontend/src/lib/autocomplete.ts) — this powers a separate dropdown, not a
replacement. See .claude/currentDev.md for the design rationale: no
Typesense/Meilisearch/Elasticsearch, since the corpus here is small enough
that a plain in-memory Trie covers it without new infrastructure.

Suggestions blend two "guess" sources (so a never-searched prefix still
completes) with real search history (ranked higher, by frequency):
  - _SEED_PRODUCTS: curated specific product names, ported from
    frontend/src/data/brandSuggestions.ts
  - brand_names.json: the ~90 recognized brand names already used by
    ingestion/target_resolver.py's Exact Product Mode gate, reused here as a
    second guess layer so bare brand prefixes ("dys") complete correctly
  - searches.query rows (analytics.py already logs these on every request,
    signed-in or anonymous) — weighted by frequency
"""

import json
import logging
from pathlib import Path

from app import db

logger = logging.getLogger(__name__)

_BRAND_NAMES_PATH = Path(__file__).parent / "brand_names.json"

_SEED_PRODUCTS: list[str] = [
    "Nike Air Zoom Pegasus",
    "Nike Air Force 1",
    "Nike Air Max 270",
    "Apple iPhone 15 Pro",
    "Apple MacBook Air",
    "Apple AirPods Pro",
    "Samsung Galaxy S24",
    "Samsung Galaxy Buds 2",
    "Purple Harmony Pillow",
    "Purple Hybrid Premier Mattress",
    "Sony WH-1000XM5 Headphones",
    "Sony PlayStation 5",
    "Dyson V15 Detect Vacuum",
    "Dyson Airwrap Styler",
]


def _load_brand_names() -> list[str]:
    try:
        return json.loads(_BRAND_NAMES_PATH.read_text())
    except Exception:
        logger.exception("failed to load brand_names.json for autocomplete seed")
        return []


class _Node:
    __slots__ = ("children", "term", "weight")

    def __init__(self) -> None:
        self.children: dict[str, _Node] = {}
        # Only set on the node completing a full term. Original casing is kept
        # for display; matching itself is case-insensitive (see _insert/suggest).
        self.term: str | None = None
        self.weight: int = 0


def _insert(root: _Node, term: str, weight: int) -> None:
    stripped = term.strip()
    if not stripped:
        return
    node = root
    for ch in stripped.lower():
        node = node.children.setdefault(ch, _Node())
    if node.term is None:
        node.term = stripped
        node.weight = weight
    else:
        # Same term reachable from more than one source (seed + history) —
        # combine rather than let the later insert silently win.
        node.weight += weight


def build_trie(seed: list[str], history: list[tuple[str, int]]) -> _Node:
    root = _Node()
    for term in seed:
        _insert(root, term, 1)
    for term, count in history:
        _insert(root, term, count)
    return root


def _collect(node: _Node, out: list[tuple[str, int]]) -> None:
    if node.term is not None:
        out.append((node.term, node.weight))
    for child in node.children.values():
        _collect(child, out)


def suggest(trie: _Node, prefix: str, limit: int = 8) -> list[str]:
    needle = prefix.strip().lower()
    if not needle:
        return []
    node = trie
    for ch in needle:
        next_node = node.children.get(ch)
        if next_node is None:
            return []
        node = next_node
    matches: list[tuple[str, int]] = []
    _collect(node, matches)
    matches.sort(key=lambda item: (-item[1], item[0].lower()))
    return [term for term, _weight in matches[:limit]]


# Seed-only trie available immediately at import, before refresh() ever runs —
# guesses work from process start, real history layers on top once refresh()
# succeeds (called from main.py's startup lifespan).
_TRIE: _Node = build_trie(_SEED_PRODUCTS + _load_brand_names(), [])


def refresh() -> None:
    """Rebuild the module-level trie from seed data + real search history.

    Startup-only for now (known limitation — new searches surface after the
    next restart, not live). Never raises: a missing DATABASE_URL, an
    unreachable Postgres, or any other failure here just means the trie stays
    seed-only, the same swallow-and-log convention as analytics.py.
    """
    global _TRIE
    history: list[tuple[str, int]] = []
    try:
        with db.get_pool().connection() as conn:
            # NOT private matches analytics.admin_stats()'s own convention: an
            # account's share_data opt-out must not leak their query text into
            # other users' suggestions.
            rows = conn.execute(
                "SELECT lower(query), count(*) FROM searches "
                "WHERE NOT private GROUP BY lower(query)"
            ).fetchall()
        history = [(row[0], row[1]) for row in rows]
    except Exception:
        logger.exception("autocomplete history refresh failed; using seed-only trie")
        return

    _TRIE = build_trie(_SEED_PRODUCTS + _load_brand_names(), history)


def get_suggestions(prefix: str, limit: int = 8) -> list[str]:
    return suggest(_TRIE, prefix, limit)
