from fastapi import APIRouter, HTTPException

router = APIRouter()


# Stub: SpecBreakdownModal.tsx computes the spec comparison client-side from
# data already returned by /api/search — nothing in the frontend calls this.
@router.get("/api/compare/{product_id}")
def compare(product_id: str) -> None:
    raise HTTPException(501, "Not implemented — spec comparison is computed client-side")
