import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from app import config
from app.accounts import store

CODE_LENGTH = 6


def _generate_code() -> str:
    return f"{secrets.randbelow(10**CODE_LENGTH):0{CODE_LENGTH}d}"


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def request_code(email: str) -> str:
    code = _generate_code()
    expires_at = datetime.now(UTC) + timedelta(
        minutes=config.VERIFICATION_CODE_TTL_MINUTES
    )
    store.store_verification_code(email, _hash_code(code), expires_at)
    return code


def verify_code(email: str, code: str) -> bool:
    return store.consume_verification_code(email, _hash_code(code))
