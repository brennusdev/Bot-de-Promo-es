from datetime import datetime, timezone

from app.database.connection import get_connection, get_placeholder


def save_price(product_id, value):
    """Salva um novo registro de preço para um produto."""
    conn = get_connection()
    cursor = conn.cursor()
    collected_at = datetime.now(timezone.utc).isoformat()
    ph = get_placeholder()

    cursor.execute(
        f"INSERT INTO prices (product_id, value, collected_at) VALUES ({ph}, {ph}, {ph})",
        (product_id, float(value), collected_at),
    )
    conn.commit()

    price_id = cursor.lastrowid
    conn.close()

    return {
        "id": price_id,
        "product_id": product_id,
        "value": float(value),
        "collected_at": collected_at,
    }


def get_price_history(product_id):
    """Busca todos os preços registrados de um produto em ordem cronológica."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT * FROM prices WHERE product_id = {ph} ORDER BY collected_at ASC",
        (product_id,),
    )
    rows = cursor.fetchall()

    conn.close()
    return [dict(row) for row in rows]


def get_latest_price(product_id):
    """Retorna o último preço registrado para um produto."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT * FROM prices WHERE product_id = {ph} ORDER BY id DESC LIMIT 1",
        (product_id,),
    )
    row = cursor.fetchone()

    conn.close()
    return dict(row) if row else None
