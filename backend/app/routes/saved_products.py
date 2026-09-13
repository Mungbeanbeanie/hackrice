from fastapi import APIRouter, HTTPException

from app.routes.auth import AccountDep
from app.saved_products import store
from app.saved_products.models import SavedProduct, SavedProductCreate

router = APIRouter()


@router.post("/api/saved-products", response_model=SavedProduct)
def save_product(body: SavedProductCreate, account: AccountDep) -> SavedProduct:
    return store.save_product(account.id, body)


@router.get("/api/saved-products", response_model=list[SavedProduct])
def list_saved_products(account: AccountDep) -> list[SavedProduct]:
    return store.list_saved_products(account.id)


@router.delete("/api/saved-products/{saved_id}")
def delete_saved_product(saved_id: int, account: AccountDep) -> dict[str, bool]:
    deleted = store.delete_saved_product(account.id, saved_id)
    if not deleted:
        raise HTTPException(404, "Saved product not found")
    return {"deleted": True}
