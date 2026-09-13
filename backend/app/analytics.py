import logging
from typing import Any

from fastapi import Request

from app import db
from app.accounts import session

logger = logging.getLogger(__name__)


def record_search(request: Request, query: str, mode: str, result_count: int) -> None:
    """Log one search attempt. Never raises.

    Swallowing here rather than at the call site means a caller cannot forget
    to. Analytics is not worth failing a user's search over, and there are
    several ways this legitimately fails on a half-configured box: no
    DATABASE_URL, Postgres unreachable, no SESSION_SECRET (which makes reading
    the cookie raise), or a session naming an account row that no longer exists.
    """
    try:
        account_id = session.read_session_cookie(request)
        with db.get_pool().connection() as conn:
            # private is stamped from the account's setting as it stands right
            # now, in the same statement — no extra round trip. Anonymous
            # searches (account_id NULL) match no row, so COALESCE makes them
            # public and they keep counting toward usage.
            conn.execute(
                """
                INSERT INTO searches (account_id, query, mode, result_count, private)
                VALUES (%s, %s, %s, %s,
                        COALESCE((SELECT NOT share_data FROM accounts WHERE id = %s),
                                 false))
                """,
                (account_id, query, mode, result_count, account_id),
            )
    except Exception:
        logger.exception("search analytics write failed")


def admin_stats() -> dict[str, Any]:
    """Everything the /api/admin dashboard renders, in one connection."""
    with db.get_pool().connection() as conn:
        accounts_row = conn.execute(
            """
            SELECT count(*),
                   count(*) FILTER (WHERE created_at > now() - interval '24 hours')
            FROM accounts
            """
        ).fetchone()
        recent_accounts = conn.execute(
            "SELECT email, created_at FROM accounts ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        # count(account_id) skips NULLs, so it is exactly the signed-in count.
        # Every search query here excludes private rows — that opt-out covers
        # searches only, so the two accounts queries above are left alone.
        searches_row = conn.execute(
            """
            SELECT count(*),
                   count(*) FILTER (WHERE created_at > now() - interval '24 hours'),
                   count(account_id)
            FROM searches
            WHERE NOT private
            """
        ).fetchone()
        top_queries = conn.execute(
            """
            SELECT query, count(*) AS n
            FROM searches
            WHERE NOT private
            GROUP BY query
            ORDER BY n DESC
            LIMIT 20
            """
        ).fetchall()
        recent_searches = conn.execute(
            """
            SELECT s.created_at, s.query, s.mode, s.result_count, a.email
            FROM searches s
            LEFT JOIN accounts a ON a.id = s.account_id
            WHERE NOT s.private
            ORDER BY s.created_at DESC
            LIMIT 50
            """
        ).fetchall()

    accounts_total, accounts_24h = accounts_row or (0, 0)
    searches_total, searches_24h, searches_signed_in = searches_row or (0, 0, 0)

    return {
        "accounts_total": accounts_total,
        "accounts_24h": accounts_24h,
        "recent_accounts": recent_accounts,
        "searches_total": searches_total,
        "searches_24h": searches_24h,
        "searches_signed_in": searches_signed_in,
        "searches_anonymous": searches_total - searches_signed_in,
        "top_queries": top_queries,
        "recent_searches": recent_searches,
    }
