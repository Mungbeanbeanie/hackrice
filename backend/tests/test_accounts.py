import time
from typing import cast

import httpx
import pytest

from app import config, db
from app.accounts import mailer, passwords, session


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


def test_mailer_surfaces_resend_error_body(monkeypatch: pytest.MonkeyPatch) -> None:
    # The status line alone ("403 Forbidden") does not say why Resend refused.
    monkeypatch.setattr(config, "RESEND_API_KEY", "fake-key")
    body = '{"statusCode":403,"message":"You can only send testing emails to..."}'

    def forbidden(*args: object, **kwargs: object) -> httpx.Response:
        return httpx.Response(
            403, text=body, request=httpx.Request("POST", mailer.RESEND_URL)
        )

    monkeypatch.setattr(httpx, "post", forbidden)

    with pytest.raises(RuntimeError, match="only send testing emails"):
        mailer.send_verification_code("a@b.com", "123456")


def test_mailer_sends_from_configured_address(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "RESEND_API_KEY", "fake-key")
    monkeypatch.setattr(config, "MAIL_FROM_ADDRESS", "hi@nectarly.us")
    sent: dict[str, object] = {}

    def capture(*args: object, **kwargs: object) -> httpx.Response:
        sent.update(cast(dict[str, object], kwargs["json"]))
        return httpx.Response(
            200, json={"id": "x"}, request=httpx.Request("POST", mailer.RESEND_URL)
        )

    monkeypatch.setattr(httpx, "post", capture)
    mailer.send_verification_code("a@b.com", "123456")

    assert sent["from"] == "hi@nectarly.us"
    assert sent["to"] == ["a@b.com"]


def test_get_pool_raises_when_database_url_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config, "DATABASE_URL", None)
    monkeypatch.setattr(db, "_pool", None)
    with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
        db.get_pool()


def test_password_hash_verify_round_trip() -> None:
    hashed = passwords.hash_password("correct-password")
    assert passwords.verify_password("correct-password", hashed)


def test_password_verify_fails_on_wrong_password() -> None:
    hashed = passwords.hash_password("correct-password")
    assert not passwords.verify_password("wrong-password", hashed)


def test_password_verify_returns_false_not_raise_on_malformed_stored_value() -> None:
    assert passwords.verify_password("anything", "not-a-valid-stored-hash") is False
    assert passwords.verify_password("anything", "") is False


def test_password_hash_salts_differ_for_same_password() -> None:
    first = passwords.hash_password("same-password")
    second = passwords.hash_password("same-password")
    assert first != second
