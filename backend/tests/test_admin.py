from datetime import UTC, datetime
from unittest.mock import patch

from fastapi import Request
from fastapi.testclient import TestClient

from app import analytics
from app.main import app

client = TestClient(app)

PASSWORD = "s3cret"


def _stats(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "accounts_total": 2,
        "accounts_24h": 1,
        "recent_accounts": [("a@b.com", datetime.now(UTC))],
        "searches_total": 5,
        "searches_24h": 3,
        "searches_signed_in": 2,
        "searches_anonymous": 3,
        "top_queries": [("memory foam pillow", 4)],
        "recent_searches": [
            (datetime.now(UTC), "memory foam pillow", "description", 12, None)
        ],
    }
    return base | overrides


def test_401_without_credentials() -> None:
    with patch("app.routes.admin.config.ADMIN_PASSWORD", PASSWORD):
        response = client.get("/api/admin")
    assert response.status_code == 401


def test_401_with_wrong_password() -> None:
    with patch("app.routes.admin.config.ADMIN_PASSWORD", PASSWORD):
        response = client.get("/api/admin", auth=("admin", "wrong"))
    assert response.status_code == 401


def test_503_when_password_unset() -> None:
    # Fails closed: an unconfigured box must not serve the dashboard open.
    with patch("app.routes.admin.config.ADMIN_PASSWORD", None):
        response = client.get("/api/admin", auth=("admin", "anything"))
    assert response.status_code == 503


def test_200_with_correct_password() -> None:
    with (
        patch("app.routes.admin.config.ADMIN_PASSWORD", PASSWORD),
        patch("app.routes.admin.analytics.admin_stats", return_value=_stats()),
    ):
        response = client.get("/api/admin", auth=("admin", PASSWORD))
    assert response.status_code == 200
    assert "memory foam pillow" in response.text
    assert "a@b.com" in response.text


def test_502_when_stats_query_fails() -> None:
    with (
        patch("app.routes.admin.config.ADMIN_PASSWORD", PASSWORD),
        patch(
            "app.routes.admin.analytics.admin_stats",
            side_effect=RuntimeError("DATABASE_URL is not set"),
        ),
    ):
        response = client.get("/api/admin", auth=("admin", PASSWORD))
    assert response.status_code == 502


def test_user_supplied_query_is_html_escaped() -> None:
    evil = "<script>alert(1)</script>"
    with (
        patch("app.routes.admin.config.ADMIN_PASSWORD", PASSWORD),
        patch(
            "app.routes.admin.analytics.admin_stats",
            return_value=_stats(top_queries=[(evil, 1)]),
        ),
    ):
        response = client.get("/api/admin", auth=("admin", PASSWORD))
    assert response.status_code == 200
    assert evil not in response.text
    assert "&lt;script&gt;" in response.text


def _fake_request() -> Request:
    return Request({"type": "http", "headers": [], "method": "POST", "path": "/"})


# record_search must never raise: analytics is not worth failing a search over.
def test_record_search_swallows_db_failure() -> None:
    with patch("app.analytics.db.get_pool", side_effect=RuntimeError("no DB")):
        analytics.record_search(_fake_request(), "pillow", "description", 3)


def test_record_search_swallows_unset_session_secret() -> None:
    with patch(
        "app.analytics.session.read_session_cookie",
        side_effect=RuntimeError("SESSION_SECRET is not set"),
    ):
        analytics.record_search(_fake_request(), "pillow", "description", 3)
