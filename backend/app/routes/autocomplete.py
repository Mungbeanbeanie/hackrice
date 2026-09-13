from fastapi import APIRouter, Query

from app import autocomplete

router = APIRouter()


@router.get("/api/autocomplete")
def get_autocomplete(q: str = Query("")) -> dict[str, list[str]]:
    # No DB hit here — the trie is already in memory, rebuilt by
    # autocomplete.refresh() at startup, not per request.
    return {"suggestions": autocomplete.get_suggestions(q)}
