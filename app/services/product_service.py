import json

from app.database.connection import get_connection, get_placeholder, supports_returning, fetch_new_id
from app.services.category_service import detect_category


def save_product(name, url, store, market="mercado", category=None, specifications=None, reference_price=0, promotion_score=0):
    """Salva o produto no banco. Se já existir, retorna o existente."""
    conn = get_connection()
    cursor = conn.cursor()
    ph = get_placeholder()

    specs = json.dumps(specifications or {}, ensure_ascii=False)
    # Fallback: sem categoria explícita, classifica pelo nome do produto.
    category = category or detect_category(name)

    cursor.execute(
        f"SELECT * FROM products WHERE url = {ph}",
        (url,),
    )
    product = cursor.fetchone()

    if product is None:
        insert_sql = f"""
            INSERT INTO products (name, url, store, market, category, specifications, reference_price, promotion_score)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
            """
        if supports_returning():
            insert_sql += " RETURNING id"
        cursor.execute(insert_sql,
            (name, url, store, market, category, specs, float(reference_price), int(promotion_score)),
        )
        conn.commit()
        product_id = fetch_new_id(cursor)
        product = {
            "id": product_id,
            "name": name,
            "url": url,
            "store": store,
            "market": market,
            "category": category,
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

        # ESTUDO (migração): produtos antigos ficaram sem categoria (NULL ou
        # 'outros' default). Backfill on-the-fly classifica pelo nome —
        # depois de algumas execuções, toda a base fica categorizada.
        if not product.get("category") or product.get("category") == "outros":
            detected = detect_category(product.get("name") or "")
            if detected != "outros":
                cursor.execute(
                    f"UPDATE products SET category = {ph} WHERE id = {ph}",
                    (detected, product["id"]),
                )
                conn.commit()
                product["category"] = detected

    conn.close()
    return product


def get_product_by_id(product_id):
    """Busca um produto pelo id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM products WHERE id = {get_placeholder()}",
        (product_id,),
    )
    product = cursor.fetchone()
    conn.close()
    return dict(product) if product else None


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


def update_promotion_score(product_id, score):
    """Atualiza o score de promoção de um produto após novo ciclo de coleta."""
    conn = get_connection()
    cursor = conn.cursor()
    ph = get_placeholder()
    cursor.execute(
        f"UPDATE products SET promotion_score = {ph} WHERE id = {ph}",
        (int(score), product_id),
    )
    conn.commit()
    conn.close()
    return int(score)


def delete_product(product_id):
    """Remove um produto e seus registros dependentes (preços e alertas).

    ESTUDO (SQL): o SQLite pode não ter PRAGMA foreign_keys=ON por conexão,
    então fazemos o cascade manualmente — mesma semântica do
    ON DELETE CASCADE do esquema PostgreSQL.
    """
    conn = get_connection()
    cursor = conn.cursor()
    ph = get_placeholder()

    cursor.execute(f"DELETE FROM prices WHERE product_id = {ph}", (product_id,))
    cursor.execute(f"DELETE FROM alerts WHERE product_id = {ph}", (product_id,))
    cursor.execute(f"DELETE FROM products WHERE id = {ph}", (product_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted > 0


def list_products(limit=None, offset=0, category=None):
    """Lista produtos cadastrados com paginação e filtro opcional por categoria.

    ESTUDO (API): sem paginação, a lista cresce indefinidamente e o
    endpoint fica lento. limit/offset permitem o dashboard carregar aos
    poucos (ex.: ?limit=20&offset=40). limit=None mantém compatibilidade.
    category filtra por categoria detectada (ex.: ?category=notebook).
    """
    conn = get_connection()
    cursor = conn.cursor()

    ph = get_placeholder()
    sql = "SELECT * FROM products"
    params = []
    if category:
        sql += f" WHERE category = {ph}"
        params.append(category)
    sql += " ORDER BY id DESC"
    if limit is not None:
        sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"
    cursor.execute(sql, tuple(params))
    products = cursor.fetchall()

    conn.close()
    return [dict(item) for item in products]
