import hashlib
import hmac
import time
from datetime import UTC, datetime, timedelta

from fastapi import Request, Response

from app import config

COOKIE_NAME = "session"


def _sign(payload: str) -> str:
    if not config.SESSION_SECRET:
        raise RuntimeError("SESSION_SECRET is not set")
    return hmac.new(
        config.SESSION_SECRET.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()


def create_session_token(account_id: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(days=config.SESSION_TTL_DAYS)
    payload = f"{account_id}.{int(expires_at.timestamp())}"
    return f"{payload}.{_sign(payload)}"


def verify_session_token(token: str) -> str | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None

    account_id, expires_at_ts, signature = parts
    expected = _sign(f"{account_id}.{expires_at_ts}")
    if not hmac.compare_digest(expected, signature):
        return None

    if int(expires_at_ts) < time.time():
        return None

    return account_id


def issue_session_cookie(response: Response, account_id: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        create_session_token(account_id),
        httponly=True,
        secure=config.SESSION_COOKIE_SECURE,
        samesite="lax",
        max_age=config.SESSION_TTL_DAYS * 86400,
    )


def clear_session_cookie(response: Response) -> None:
    # Every attribute except max_age has to match issue_session_cookie above or
    # the browser treats this as a different cookie and quietly keeps the live
    # one — a logout that returns 200 and leaves the user signed in. Lives next
    # to the issuing call for exactly that reason.
    #
    # Note this cannot revoke the token itself: sessions are stateless HMAC, so
    # a copy of the cookie stays valid until its own expiry. Revocation would
    # need a server-side session table.
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        httponly=True,
        secure=config.SESSION_COOKIE_SECURE,
        samesite="lax",
    )


def read_session_cookie(request: Request) -> str | None:
    token = request.cookies.get(COOKIE_NAME)
    return verify_session_token(token) if token else None
