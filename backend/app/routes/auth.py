from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app.accounts import mailer, session, store, verification
from app.models import Account

router = APIRouter()


class RequestCodeBody(BaseModel):
    email: str


class VerifyBody(BaseModel):
    email: str
    code: str


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
def me(request: Request) -> Account:
    try:
        account_id = session.read_session_cookie(request)
        if account_id is None:
            raise HTTPException(401, "Not authenticated")

        account = store.get_account_by_id(account_id)
        if account is None:
            raise HTTPException(401, "Not authenticated")

        return account
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from exc
