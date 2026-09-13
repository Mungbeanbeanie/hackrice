import pytest
from fastapi.testclient import TestClient

from app import autocomplete, db
from app.main import app

client = TestClient(app)


def test_prefix_match_returns_expected_term() -> None:
    trie = autocomplete.build_trie(["Nike Air Zoom Pegasus", "Nike Air Force 1"], [])
    assert autocomplete.suggest(trie, "nike air f") == ["Nike Air Force 1"]


def test_higher_weight_history_term_ranks_above_seed_only_term() -> None:
    # Same prefix, one seed-only (weight 1), one from history (weight 5) —
    # the real-search term must sort first.
    trie = autocomplete.build_trie(["dyson vacuum"], [("dyson v15", 5)])
    assert autocomplete.suggest(trie, "dyson") == ["dyson v15", "dyson vacuum"]


def test_seed_only_term_still_suggested_with_zero_history() -> None:
    # The "guessing" requirement: a never-searched prefix still completes.
    trie = autocomplete.build_trie(["Purple Harmony Pillow"], [])
    assert autocomplete.suggest(trie, "purple") == ["Purple Harmony Pillow"]


def test_case_insensitive_matching() -> None:
    trie = autocomplete.build_trie(["Nike Air Zoom Pegasus"], [])
    assert autocomplete.suggest(trie, "NIKE AIR") == ["Nike Air Zoom Pegasus"]


def test_blank_prefix_returns_nothing() -> None:
    trie = autocomplete.build_trie(["Nike Air Zoom Pegasus"], [])
    assert autocomplete.suggest(trie, "") == []
    assert autocomplete.suggest(trie, "   ") == []


def test_no_match_returns_nothing() -> None:
    trie = autocomplete.build_trie(["Nike Air Zoom Pegasus"], [])
    assert autocomplete.suggest(trie, "adidas") == []


def test_limit_truncates_results() -> None:
    terms = [f"Nike Shoe {i}" for i in range(10)]
    trie = autocomplete.build_trie(terms, [])
    assert len(autocomplete.suggest(trie, "nike", limit=3)) == 3


def test_refresh_falls_back_to_seed_only_on_db_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_unset() -> None:
        raise RuntimeError("DATABASE_URL is not set")

    monkeypatch.setattr(db, "get_pool", raise_unset)

    autocomplete.refresh()

    # Did not raise, and seed data (ported from brandSuggestions.ts) is still
    # reachable through the module-level trie. "purple" also matches
    # brand_names.json's own "purple" entry, so this checks membership, not
    # exact equality.
    assert "Purple Harmony Pillow" in autocomplete.get_suggestions("purple")


def test_route_returns_suggestions_for_a_seeded_prefix() -> None:
    response = client.get("/api/autocomplete", params={"q": "purple"})
    assert response.status_code == 200
    assert "Purple Harmony Pillow" in response.json()["suggestions"]


def test_route_returns_empty_list_for_blank_query() -> None:
    response = client.get("/api/autocomplete")
    assert response.status_code == 200
    assert response.json() == {"suggestions": []}
