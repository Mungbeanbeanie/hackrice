from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.accounts import mailer, session, store, verification
from app.models import Account, SearchHistoryItem

router = APIRouter()

# A 128px JPEG at q0.8 lands around 4-8 KB of base64; the cap is for hostile
# clients, not real photos.
AVATAR_MAX_CHARS = 100_000


class RequestCodeBody(BaseModel):
    email: str


class VerifyBody(BaseModel):
    email: str
    code: str


class UpdateProfileBody(BaseModel):
    # None means "leave this alone". An empty string is a real value: it clears
    # the field.
    display_name: str | None = Field(default=None, max_length=60)
    avatar: str | None = None
    share_data: bool | None = None


def current_account(request: Request) -> Account:
    """The signed-in account, or 401. Four routes need this."""
    try:
        account_id = session.read_session_cookie(request)
        account = store.get_account_by_id(account_id) if account_id else None
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from exc
    if account is None:
        raise HTTPException(401, "Not authenticated")
    return account


AccountDep = Annotated[Account, Depends(current_account)]


@router.post("/api/auth/request-code")
def request_code(body: RequestCodeBody) -> dict[str, str]:
    try:
        code = verification.request_code(body.email)
        mailer.send_verification_code(body.email, code)
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from exc

    return {"status": "sent"}


@router.post("/api/auth/verify", response_model=Account)
def verify(body: VerifyBody, response: Response) -> Account:
    try:
        if not verification.verify_code(body.email, body.code):
            raise HTTPException(401, "Invalid or expired code")

        account = store.get_or_create_account(body.email)
        session.issue_session_cookie(response, account.id)
        return account
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.get("/api/auth/me", response_model=Account)
def me(account: AccountDep) -> Account:
    return account


@router.post("/api/auth/logout")
def logout(response: Response) -> dict[str, str]:
    # Deliberately unauthenticated: clearing a cookie nobody has is a no-op,
    # and 401-ing a logout is a worse experience than letting it succeed.
    session.clear_session_cookie(response)
    return {"status": "ok"}


@router.patch("/api/auth/me", response_model=Account)
def update_me(body: UpdateProfileBody, account: AccountDep) -> Account:
    # Checked here rather than as a pydantic constraint: FastAPI's 422 body
    # echoes the offending input, so a rejected 200 KB avatar would come
    # straight back down the wire. The value is rendered into an <img src>, so
    # the data:image/ prefix is a trust-boundary check, not cosmetics.
    # "" is allowed through — that is how the client clears a picture.
    if body.avatar:
        if len(body.avatar) > AVATAR_MAX_CHARS:
            raise HTTPException(413, "Avatar too large")
        if not body.avatar.startswith("data:image/"):
            raise HTTPException(400, "Avatar must be a data:image/ URL")

    try:
        updated = store.update_account(
            account.id, body.display_name, body.avatar, body.share_data
        )
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from exc

    if updated is None:
        raise HTTPException(401, "Not authenticated")
    return updated


@router.get("/api/auth/history", response_model=list[SearchHistoryItem])
def history(account: AccountDep) -> list[SearchHistoryItem]:
    try:
        return store.get_search_history(account.id)
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.delete("/api/auth/history")
def clear_history(account: AccountDep) -> dict[str, int]:
    try:
        return {"deleted": store.delete_search_history(account.id)}
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from exc
