import uuid
from datetime import UTC, datetime
from typing import Any

from app import db
from app.models import Account, SearchHistoryItem

# One list, three query sites — they drifted apart the moment profile columns
# landed, so the column order lives here and _to_account reads it positionally.
_COLUMNS = "id, email, created_at, display_name, avatar, share_data"


def _to_account(row: tuple[Any, ...]) -> Account:
    return Account(
        id=str(row[0]),
        email=row[1],
        created_at=row[2],
        display_name=row[3],
        avatar=row[4],
        share_data=row[5],
    )


def get_account_by_id(account_id: str) -> Account | None:
    with db.get_pool().connection() as conn:
        row = conn.execute(
            f"SELECT {_COLUMNS} FROM accounts WHERE id = %s",
            (account_id,),
        ).fetchone()
    if row is None:
        return None
    return _to_account(row)


def get_or_create_account(email: str) -> Account:
    with db.get_pool().connection() as conn:
        row = conn.execute(
            f"""
            INSERT INTO accounts (id, email) VALUES (%s, %s)
            ON CONFLICT (email) DO NOTHING
            RETURNING {_COLUMNS}
            """,
            (str(uuid.uuid4()), email),
        ).fetchone()
        if row is None:
            row = conn.execute(
                f"SELECT {_COLUMNS} FROM accounts WHERE email = %s",
                (email,),
            ).fetchone()
    assert row is not None
    return _to_account(row)


def update_account(
    account_id: str,
    display_name: str | None,
    avatar: str | None,
    share_data: bool | None,
) -> Account | None:
    """Partial update — a None argument leaves that column untouched.

    The explicit casts matter: psycopg sends None as an untyped NULL, and
    COALESCE(unknown, boolean) is not something to leave to type inference.
    """
    with db.get_pool().connection() as conn:
        row = conn.execute(
            f"""
            UPDATE accounts SET
                display_name = COALESCE(%s::text, display_name),
                avatar       = COALESCE(%s::text, avatar),
                share_data   = COALESCE(%s::boolean, share_data)
            WHERE id = %s
            RETURNING {_COLUMNS}
            """,
            (display_name, avatar, share_data, account_id),
        ).fetchone()
    return _to_account(row) if row else None


def get_search_history(account_id: str, limit: int = 100) -> list[SearchHistoryItem]:
    with db.get_pool().connection() as conn:
        rows = conn.execute(
            """
            SELECT id, query, mode, result_count, created_at
            FROM searches WHERE account_id = %s
            ORDER BY created_at DESC LIMIT %s
            """,
            (account_id, limit),
        ).fetchall()
    return [
        SearchHistoryItem(
            id=r[0], query=r[1], mode=r[2], result_count=r[3], created_at=r[4]
        )
        for r in rows
    ]


def delete_search_history(account_id: str) -> int:
    with db.get_pool().connection() as conn:
        return conn.execute(
            "DELETE FROM searches WHERE account_id = %s", (account_id,)
        ).rowcount


def get_password_hash(account_id: str) -> str | None:
    with db.get_pool().connection() as conn:
        row = conn.execute(
            "SELECT password_hash FROM accounts WHERE id = %s", (account_id,)
        ).fetchone()
    return row[0] if row else None


def get_account_for_login(email: str) -> tuple[Account, str | None] | None:
    """Only for the password-login path — the returned hash must never reach
    the client. Never merged into _COLUMNS/_to_account for that reason.
    """
    with db.get_pool().connection() as conn:
        row = conn.execute(
            f"SELECT {_COLUMNS}, password_hash FROM accounts WHERE email = %s",
            (email,),
        ).fetchone()
    if row is None:
        return None
    return _to_account(row[:-1]), row[-1]


def set_password(account_id: str, password_hash: str) -> None:
    with db.get_pool().connection() as conn:
        conn.execute(
            "UPDATE accounts SET password_hash = %s WHERE id = %s",
            (password_hash, account_id),
        )


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
