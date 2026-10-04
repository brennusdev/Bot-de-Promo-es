from datetime import datetime, timezone

from app.database.connection import get_connection, get_placeholder, supports_returning, fetch_new_id


def save_price(product_id, value):
    """Salva um novo registro de preço para um produto."""
    conn = get_connection()
    cursor = conn.cursor()
    collected_at = datetime.now(timezone.utc).isoformat()
    ph = get_placeholder()

    insert_sql = f"INSERT INTO prices (product_id, value, collected_at) VALUES ({ph}, {ph}, {ph})"
    if supports_returning():
        insert_sql += " RETURNING id"
    cursor.execute(insert_sql, (product_id, float(value), collected_at))
    conn.commit()

    price_id = fetch_new_id(cursor)
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
        f"SELECT * FROM prices WHERE product_id = {get_placeholder()} ORDER BY collected_at ASC",
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
        f"SELECT * FROM prices WHERE product_id = {get_placeholder()} ORDER BY id DESC LIMIT 1",
        (product_id,),
    )
    row = cursor.fetchone()

    conn.close()
    return dict(row) if row else None


def get_recent_prices(product_id, count=2):
    """Retorna os `count` últimos preços, do mais antigo para o mais novo.

    ESTUDO (performance): o dashboard só precisa do preço atual + anterior
    para calcular variação. Buscar o histórico inteiro (que pode ter milhares
    de registros após meses de worker) é desperdício; com o índice
    idx_prices_product_id essa consulta é O(log n).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT * FROM prices WHERE product_id = {get_placeholder()} ORDER BY id DESC LIMIT {int(count)}",
        (product_id,),
    )
    rows = cursor.fetchall()

    conn.close()
    return [dict(row) for row in reversed(rows)]
