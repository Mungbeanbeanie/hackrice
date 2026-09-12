import time

import httpx
import pytest

from app import config, db
from app.accounts import mailer, session


def test_create_and_verify_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "SESSION_SECRET", "test-secret")
    token = session.create_session_token("account-1")
    assert session.verify_session_token(token) == "account-1"


def test_verify_rejects_malformed_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "SESSION_SECRET", "test-secret")
    assert session.verify_session_token("not-a-real-token") is None


def test_verify_rejects_tampered_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "SESSION_SECRET", "test-secret")
    token = session.create_session_token("account-1")
    account_id, ts, sig = token.split(".")
    tampered = f"{account_id}.{ts}.{'0' * len(sig)}"
    assert session.verify_session_token(tampered) is None


def test_verify_rejects_expired_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "SESSION_SECRET", "test-secret")
    payload = f"account-1.{int(time.time()) - 10}"
    token = f"{payload}.{session._sign(payload)}"
    assert session.verify_session_token(token) is None


def test_create_session_token_requires_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "SESSION_SECRET", None)
    with pytest.raises(RuntimeError, match="SESSION_SECRET is not set"):
        session.create_session_token("account-1")


def test_mailer_raises_when_key_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "RESEND_API_KEY", None)
    with pytest.raises(RuntimeError, match="RESEND_API_KEY is not set"):
        mailer.send_verification_code("a@b.com", "123456")


def test_mailer_wraps_network_failure_as_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config, "RESEND_API_KEY", "fake-key")

    def raise_connect_error(*args: object, **kwargs: object) -> None:
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "post", raise_connect_error)

    with pytest.raises(RuntimeError, match="Resend request failed"):
        mailer.send_verification_code("a@b.com", "123456")


def test_get_pool_raises_when_database_url_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config, "DATABASE_URL", None)
    monkeypatch.setattr(db, "_pool", None)
    with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
        db.get_pool()
