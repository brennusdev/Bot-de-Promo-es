import json

from app.database.connection import get_connection


def save_product(name, url, store, market="mercado", specifications=None, reference_price=0, promotion_score=0):
    """Salva o produto no banco. Se já existir, retorna o existente."""
    conn = get_connection()
    cursor = conn.cursor()

    specs = json.dumps(specifications or {}, ensure_ascii=False)

    cursor.execute(
        "SELECT * FROM products WHERE url = ?",
        (url,),
    )
    product = cursor.fetchone()

    if product is None:
        cursor.execute(
            """
            INSERT INTO products (name, url, store, market, specifications, reference_price, promotion_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, url, store, market, specs, float(reference_price), int(promotion_score)),
        )
        conn.commit()
        product_id = cursor.lastrowid
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
        if product.get("specifications"):
            product["specifications"] = json.loads(product["specifications"])

    conn.close()
    return product


def get_product_by_url(url):
    """Busca um produto pelo link da página."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE url = ?",
        (url,),
    )
    product = cursor.fetchone()

    conn.close()
    return dict(product) if product else None


def list_products():
    """Lista todos os produtos cadastrados."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    products = cursor.fetchall()

    conn.close()
    return [dict(item) for item in products]
