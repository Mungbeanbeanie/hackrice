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
        # account_id is nullable on purpose: search needs no sign-in, so most
        # rows are anonymous. They still count as usage.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS searches (
                id BIGSERIAL PRIMARY KEY,
                account_id UUID REFERENCES accounts(id),
                query TEXT NOT NULL,
                mode TEXT NOT NULL,
                result_count INT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
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
        # Profile/settings columns. CREATE TABLE IF NOT EXISTS above is a no-op
        # on a database that already has these tables, so new columns have to
        # be added explicitly or they only ever exist on a fresh local DB.
        # ADD COLUMN ... NOT NULL DEFAULT is metadata-only on PG 11+, so this
        # does not rewrite the table.
        conn.execute("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS display_name TEXT")
        conn.execute("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS avatar TEXT")
        conn.execute(
            "ALTER TABLE accounts "
            "ADD COLUMN IF NOT EXISTS share_data BOOLEAN NOT NULL DEFAULT true"
        )
        # Stamped per row at insert time, so flipping the account setting later
        # never rewrites history in either direction.
        conn.execute(
            "ALTER TABLE searches "
            "ADD COLUMN IF NOT EXISTS private BOOLEAN NOT NULL DEFAULT false"
        )
        # Shared/product-keyed, not account-tied — one row per view of a
        # specific listing, written only when a candidate is clicked/selected,
        # never on search. source distinguishes real click-triggered rows from
        # manually-seeded historical rows (price_history/loader.py).
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS price_snapshots (
                id BIGSERIAL PRIMARY KEY,
                product_key TEXT NOT NULL,
                title TEXT NOT NULL,
                store TEXT NOT NULL,
                price NUMERIC NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                source TEXT NOT NULL DEFAULT 'click'
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS price_snapshots_product_key_idx "
            "ON price_snapshots (product_key)"
        )
