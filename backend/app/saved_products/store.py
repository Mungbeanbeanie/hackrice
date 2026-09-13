from typing import Any

from app import db
from app.price_history.key import normalize_product_key
from app.saved_products.models import SavedProduct, SavedProductCreate

_COLUMNS = "id, title, brand, store, price, image_url, product_url, created_at"


def _to_saved_product(row: tuple[Any, ...]) -> SavedProduct:
    return SavedProduct(
        id=row[0],
        title=row[1],
        brand=row[2],
        store=row[3],
        # NUMERIC comes back as Decimal from psycopg; the column is nullable
        # here (unlike price_snapshots.price, which is NOT NULL), so guard
        # against None before casting.
        price=float(row[4]) if row[4] is not None else None,
        image_url=row[5],
        product_url=row[6],
        created_at=row[7],
    )


def save_product(account_id: str, body: SavedProductCreate) -> SavedProduct:
    key = normalize_product_key(body.title, body.brand, body.store)
    with db.get_pool().connection() as conn:
        row = conn.execute(
            f"""
            INSERT INTO saved_products
                (account_id, product_key, title, brand, store,
                 price, image_url, product_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_id, product_key) DO UPDATE SET
                price = EXCLUDED.price,
                title = EXCLUDED.title,
                image_url = EXCLUDED.image_url,
                product_url = EXCLUDED.product_url
            RETURNING {_COLUMNS}
            """,
            (
                account_id,
                key,
                body.title,
                body.brand,
                body.store,
                body.price,
                body.image_url,
                body.product_url,
            ),
        ).fetchone()
    assert row is not None
    return _to_saved_product(row)


def list_saved_products(account_id: str) -> list[SavedProduct]:
    with db.get_pool().connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_COLUMNS} FROM saved_products
            WHERE account_id = %s
            ORDER BY created_at DESC
            """,
            (account_id,),
        ).fetchall()
    return [_to_saved_product(row) for row in rows]


def delete_saved_product(account_id: str, saved_id: int) -> bool:
    with db.get_pool().connection() as conn:
        return (
            conn.execute(
                "DELETE FROM saved_products WHERE id = %s AND account_id = %s",
                (saved_id, account_id),
            ).rowcount
            > 0
        )
