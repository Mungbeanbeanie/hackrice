from datetime import UTC, datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import Account
from app.saved_products.models import SavedProduct

client = TestClient(app)


def _account() -> Account:
    return Account(id="acc-1", email="a@b.com", created_at=datetime.now(UTC))


def _saved(id: int = 1) -> SavedProduct:
    return SavedProduct(
        id=id,
        title="Nike Air Force 1",
        brand="Nike",
        store="nike.com",
        price=110.0,
        image_url=None,
        product_url=None,
        created_at=datetime.now(UTC),
    )


def test_save_product_requires_auth() -> None:
    response = client.post(
        "/api/saved-products",
        json={"title": "Nike Air Force 1", "brand": "Nike", "store": "nike.com"},
    )
    assert response.status_code == 401


def test_save_product_success() -> None:
    with (
        patch("app.routes.saved_products.store.save_product", return_value=_saved()),
        patch("app.routes.auth.session.read_session_cookie", return_value="acc-1"),
        patch("app.routes.auth.store.get_account_by_id", return_value=_account()),
    ):
        response = client.post(
            "/api/saved-products",
            json={"title": "Nike Air Force 1", "brand": "Nike", "store": "nike.com"},
        )
    assert response.status_code == 200
    assert response.json()["title"] == "Nike Air Force 1"


def test_list_saved_products() -> None:
    with (
        patch(
            "app.routes.saved_products.store.list_saved_products",
            return_value=[_saved(1), _saved(2)],
        ),
        patch("app.routes.auth.session.read_session_cookie", return_value="acc-1"),
        patch("app.routes.auth.store.get_account_by_id", return_value=_account()),
    ):
        response = client.get("/api/saved-products")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_delete_saved_product_success() -> None:
    with (
        patch(
            "app.routes.saved_products.store.delete_saved_product", return_value=True
        ),
        patch("app.routes.auth.session.read_session_cookie", return_value="acc-1"),
        patch("app.routes.auth.store.get_account_by_id", return_value=_account()),
    ):
        response = client.delete("/api/saved-products/1")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}


def test_delete_saved_product_not_owned_returns_404() -> None:
    # store.delete_saved_product scopes the DELETE to account_id, so a saved_id
    # belonging to someone else (or that doesn't exist) returns False, not an
    # exception — the route must translate that into a 404, not a 200.
    with (
        patch(
            "app.routes.saved_products.store.delete_saved_product", return_value=False
        ),
        patch("app.routes.auth.session.read_session_cookie", return_value="acc-1"),
        patch("app.routes.auth.store.get_account_by_id", return_value=_account()),
    ):
        response = client.delete("/api/saved-products/999")
    assert response.status_code == 404


def test_save_product_upsert_does_not_duplicate(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # Real behavior lives in the SQL's ON CONFLICT (account_id, product_key) DO
    # UPDATE clause — not exercised here without a live DB. This just asserts
    # the route always calls the single upserting store function, never an
    # insert-only path, so a second save of "the same" listing can't duplicate.
    calls = []

    def fake_save(account_id: str, body: object) -> SavedProduct:
        calls.append((account_id, body))
        return _saved()

    with (
        patch("app.routes.saved_products.store.save_product", side_effect=fake_save),
        patch("app.routes.auth.session.read_session_cookie", return_value="acc-1"),
        patch("app.routes.auth.store.get_account_by_id", return_value=_account()),
    ):
        client.post(
            "/api/saved-products",
            json={"title": "Nike Air Force 1", "brand": "Nike", "store": "nike.com"},
        )
        client.post(
            "/api/saved-products",
            json={"title": "Nike Air Force 1", "brand": "Nike", "store": "nike.com"},
        )
    assert len(calls) == 2
    assert calls[0][0] == calls[1][0] == "acc-1"
