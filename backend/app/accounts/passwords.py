import hashlib
import hmac
import os

# OWASP-minimum interactive-login parameters for scrypt: ~16 MiB memory cost
# (128 * n * r * p bytes), no new dependency — matches this codebase's
# existing preference for stdlib over a new library where one covers the job
# (see mailer.py's plain httpx call instead of a Resend SDK).
_N, _R, _P = 2**14, 8, 1
_DKLEN = 32


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN
    )
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False
    actual = hashlib.scrypt(
        password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN
    )
    return hmac.compare_digest(actual, expected)
