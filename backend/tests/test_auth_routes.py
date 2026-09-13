from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import Account

client = TestClient(app)


def _account(id: str = "acc-1", email: str = "a@b.com") -> Account:
    return Account(id=id, email=email, created_at=datetime.now(UTC))


def test_request_code_returns_200_on_success() -> None:
    with (
        patch("app.routes.auth.verification.request_code", return_value="123456"),
        patch("app.routes.auth.mailer.send_verification_code"),
    ):
        response = client.post("/api/auth/request-code", json={"email": "a@b.com"})
    assert response.status_code == 200


def test_request_code_502s_on_upstream_failure() -> None:
    with patch(
        "app.routes.auth.verification.request_code",
        side_effect=RuntimeError("DATABASE_URL is not set"),
    ):
        response = client.post("/api/auth/request-code", json={"email": "a@b.com"})
    assert response.status_code == 502


def test_verify_401s_on_invalid_code() -> None:
    with patch("app.routes.auth.verification.verify_code", return_value=False):
        response = client.post(
            "/api/auth/verify", json={"email": "a@b.com", "code": "000000"}
        )
    assert response.status_code == 401


def test_verify_returns_account_and_sets_cookie_on_success() -> None:
    account = _account()
    with (
        patch("app.routes.auth.verification.verify_code", return_value=True),
        patch("app.routes.auth.store.get_or_create_account", return_value=account),
        patch("app.routes.auth.session.issue_session_cookie") as issue_cookie,
    ):
        response = client.post(
            "/api/auth/verify", json={"email": "a@b.com", "code": "123456"}
        )
    assert response.status_code == 200
    assert response.json()["id"] == "acc-1"
    issue_cookie.assert_called_once()


def test_verify_502s_on_upstream_failure() -> None:
    with patch(
        "app.routes.auth.verification.verify_code",
        side_effect=RuntimeError("SESSION_SECRET is not set"),
    ):
        response = client.post(
            "/api/auth/verify", json={"email": "a@b.com", "code": "123456"}
        )
    assert response.status_code == 502


def test_me_401s_without_cookie() -> None:
    with patch("app.routes.auth.session.read_session_cookie", return_value=None):
        response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_401s_when_account_missing() -> None:
    with (
        patch("app.routes.auth.session.read_session_cookie", return_value="acc-1"),
        patch("app.routes.auth.store.get_account_by_id", return_value=None),
    ):
        response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_account_when_valid() -> None:
    account = _account()
    with (
        patch("app.routes.auth.session.read_session_cookie", return_value="acc-1"),
        patch("app.routes.auth.store.get_account_by_id", return_value=account),
    ):
        response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["id"] == "acc-1"


@contextmanager
def _signed_in(account: Account | None = None) -> Iterator[Mock]:
    """Patch the two calls `current_account` makes; yield the store mock."""
    store = Mock(get_account_by_id=Mock(return_value=account or _account()))
    with (
        patch("app.routes.auth.session.read_session_cookie", return_value="acc-1"),
        patch("app.routes.auth.store", store),
    ):
        yield store


def test_logout_expires_the_cookie() -> None:
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    # The attributes must match issue_session_cookie or the browser keeps the
    # live cookie and the user stays signed in despite the 200.
    cookie = response.headers["set-cookie"]
    assert "session=" in cookie
    assert "Max-Age=0" in cookie
    assert "Path=/" in cookie
    assert "httponly" in cookie.lower()
    assert "samesite=lax" in cookie.lower()


def test_logout_succeeds_when_not_signed_in() -> None:
    # Clearing a cookie nobody has is a no-op, not a 401.
    assert client.post("/api/auth/logout").status_code == 200


def test_patch_me_401s_without_cookie() -> None:
    with patch("app.routes.auth.session.read_session_cookie", return_value=None):
        response = client.patch("/api/auth/me", json={"share_data": False})
    assert response.status_code == 401


def test_history_401s_without_cookie() -> None:
    with patch("app.routes.auth.session.read_session_cookie", return_value=None):
        assert client.get("/api/auth/history").status_code == 401


def test_clear_history_401s_without_cookie() -> None:
    with patch("app.routes.auth.session.read_session_cookie", return_value=None):
        assert client.delete("/api/auth/history").status_code == 401


def test_patch_me_rejects_oversized_avatar() -> None:
    huge = "data:image/jpeg;base64," + "A" * 200_000
    with _signed_in():
        response = client.patch("/api/auth/me", json={"avatar": huge})
    assert response.status_code == 413


def test_patch_me_rejects_non_image_avatar() -> None:
    # The avatar is rendered into an <img src>, so this is a trust boundary.
    with _signed_in():
        response = client.patch("/api/auth/me", json={"avatar": "javascript:alert(1)"})
    assert response.status_code == 400


def test_patch_me_allows_empty_avatar_to_clear_it() -> None:
    # "" is how the client removes a picture — it must not trip the prefix check.
    with _signed_in() as store:
        store.update_account.return_value = _account()
        response = client.patch("/api/auth/me", json={"avatar": ""})
    assert response.status_code == 200
    assert store.update_account.call_args.args == ("acc-1", None, "", None)


def test_patch_me_leaves_unsupplied_fields_alone() -> None:
    # None reaches the COALESCE as "don't touch this column".
    with _signed_in() as store:
        store.update_account.return_value = _account()
        response = client.patch("/api/auth/me", json={"share_data": False})
    assert response.status_code == 200
    assert store.update_account.call_args.args == ("acc-1", None, None, False)


def test_history_returns_empty_list_for_a_new_account() -> None:
    with _signed_in() as store:
        store.get_search_history.return_value = []
        response = client.get("/api/auth/history")
    assert response.status_code == 200
    assert response.json() == []


def test_clear_history_reports_how_many_rows_went() -> None:
    with _signed_in() as store:
        store.delete_search_history.return_value = 3
        response = client.delete("/api/auth/history")
    assert response.status_code == 200
    assert response.json() == {"deleted": 3}
    assert store.delete_search_history.call_args.args == ("acc-1",)
