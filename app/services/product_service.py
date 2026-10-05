import json

from app.database.connection import get_connection, get_placeholder, supports_returning, fetch_new_id


def save_product(name, url, store, market="mercado", specifications=None, reference_price=0, promotion_score=0):
    """Salva o produto no banco. Se já existir, retorna o existente."""
    conn = get_connection()
    cursor = conn.cursor()
    ph = get_placeholder()

    specs = json.dumps(specifications or {}, ensure_ascii=False)

    cursor.execute(
        f"SELECT * FROM products WHERE url = {ph}",
        (url,),
    )
    product = cursor.fetchone()

    if product is None:
        insert_sql = f"""
            INSERT INTO products (name, url, store, market, specifications, reference_price, promotion_score)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
            """
        if supports_returning():
            insert_sql += " RETURNING id"
        cursor.execute(insert_sql,
            (name, url, store, market, specs, float(reference_price), int(promotion_score)),
        )
        conn.commit()
        product_id = fetch_new_id(cursor)
        product = {
            "id": product_id,
            "name": name,
            "url": url,
            "store": store,
            "market": market,
            "specifications": specifications or {},
            "reference_price": float(reference_price),
            "promotion_score": int(promotion_score),
        }
    else:
        product = dict(product)
        specs = product.get("specifications")
        if specs:
            # ESTUDO (banco): no PostgreSQL (JSONB) o driver já devolve dict;
            # no SQLite (TEXT) devolve string JSON. Suportamos os dois formatos.
            if isinstance(specs, str):
                try:
                    specs = json.loads(specs)
                except (TypeError, ValueError):
                    specs = {}
            product["specifications"] = specs or {}

    conn.close()
    return product


def get_product_by_url(url):
    """Busca um produto pelo link da página."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT * FROM products WHERE url = {get_placeholder()}",
        (url,),
    )
    product = cursor.fetchone()

    conn.close()
    return dict(product) if product else None


def list_products(limit=None, offset=0):
    """Lista produtos cadastrados com paginação opcional.

    ESTUDO (API): sem paginação, a lista cresce indefinidamente e o
    endpoint fica lento. limit/offset permitem o dashboard carregar aos
    poucos (ex.: ?limit=20&offset=40). limit=None mantém compatibilidade.
    """
    conn = get_connection()
    cursor = conn.cursor()

    ph = get_placeholder()
    sql = "SELECT * FROM products ORDER BY id DESC"
    params = []
    if limit is not None:
        sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"
    cursor.execute(sql, tuple(params))
    products = cursor.fetchall()

    conn.close()
    return [dict(item) for item in products]
