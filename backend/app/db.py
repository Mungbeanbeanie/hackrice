from psycopg_pool import ConnectionPool

from app import config

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        if not config.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set")
        _pool = ConnectionPool(config.DATABASE_URL, min_size=1, max_size=5)
        _pool.open(wait=False)
    return _pool


def init_schema() -> None:
    with get_pool().connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id UUID PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS verification_codes (
                email TEXT PRIMARY KEY,
                code TEXT NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS coupon_offers (
                offer_id TEXT PRIMARY KEY,
                store TEXT NOT NULL,
                code TEXT,
                discount_description TEXT NOT NULL,
                expires_at TIMESTAMPTZ,
                start_date TIMESTAMPTZ,
                rating INTEGER NOT NULL
            )
            """
        )
