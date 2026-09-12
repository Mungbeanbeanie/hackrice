import logging

import httpx

from app import config

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"


def send_verification_code(email: str, code: str) -> None:
    if not config.RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not set")

    try:
        response = httpx.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {config.RESEND_API_KEY}"},
            json={
                "from": config.MAIL_FROM_ADDRESS,
                "to": [email],
                "subject": "Your verification code",
                "html": (
                    f"<p>Your code is <strong>{code}</strong>. "
                    f"It expires in {config.VERIFICATION_CODE_TTL_MINUTES} minutes.</p>"
                ),
            },
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        # Resend puts the actual reason in the body (unverified domain, bad
        # sender, sandbox recipient restriction); raise_for_status only reports
        # the status line, which is never enough to act on.
        logger.exception("Resend request failed for email=%r", email)
        detail = f"Resend request failed: {exc}: {exc.response.text}"
        raise RuntimeError(detail) from exc
    except httpx.HTTPError as exc:
        logger.exception("Resend request failed for email=%r", email)
        raise RuntimeError(f"Resend request failed: {exc}") from exc
