import uuid
from datetime import UTC, datetime

from app import db
from app.models import Account


def get_account_by_id(account_id: str) -> Account | None:
    with db.get_pool().connection() as conn:
        row = conn.execute(
            "SELECT id, email, created_at FROM accounts WHERE id = %s",
            (account_id,),
        ).fetchone()
    if row is None:
        return None
    return Account(id=str(row[0]), email=row[1], created_at=row[2])


def get_or_create_account(email: str) -> Account:
    with db.get_pool().connection() as conn:
        row = conn.execute(
            """
            INSERT INTO accounts (id, email) VALUES (%s, %s)
            ON CONFLICT (email) DO NOTHING
            RETURNING id, email, created_at
            """,
            (str(uuid.uuid4()), email),
        ).fetchone()
        if row is None:
            row = conn.execute(
                "SELECT id, email, created_at FROM accounts WHERE email = %s",
                (email,),
            ).fetchone()
    assert row is not None
    return Account(id=str(row[0]), email=row[1], created_at=row[2])


def store_verification_code(email: str, code: str, expires_at: datetime) -> None:
    with db.get_pool().connection() as conn:
        conn.execute(
            """
            INSERT INTO verification_codes (email, code, expires_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (email) DO UPDATE
                SET code = EXCLUDED.code, expires_at = EXCLUDED.expires_at
            """,
            (email, code, expires_at),
        )


def consume_verification_code(email: str, code: str) -> bool:
    with db.get_pool().connection() as conn:
        row = conn.execute(
            "SELECT code, expires_at FROM verification_codes WHERE email = %s",
            (email,),
        ).fetchone()
        if row is None:
            return False

        stored_code, expires_at = row
        valid = stored_code == code and expires_at > datetime.now(UTC)
        if valid:
            conn.execute("DELETE FROM verification_codes WHERE email = %s", (email,))
        return valid
