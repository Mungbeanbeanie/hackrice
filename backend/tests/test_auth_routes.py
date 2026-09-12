from datetime import UTC, datetime
from unittest.mock import patch

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
