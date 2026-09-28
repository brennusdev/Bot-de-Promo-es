from app.database.connection import get_connection, init_db
from app.services.alert_service import calculate_price_change
from app.services.product_service import get_product_by_url, save_product
from app.services.price_service import get_price_history, save_price


def test_calculate_price_change():
    result = calculate_price_change(150.0, 200.0)
    assert result["delta"] == -50.0
    assert result["percent_change"] == -25.0
    assert result["trend"] == "mais_barato"


def test_save_product_and_history():
    init_db()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM prices")
    cursor.execute("DELETE FROM products")
    conn.commit()
    conn.close()

    product = save_product("Teclado Gamer", "https://example.com/produto/1", "Mercado Livre")
    save_price(product["id"], 299.90)
    save_price(product["id"], 259.90)

    found = get_product_by_url("https://example.com/produto/1")
    assert found is not None
    assert found["name"] == "Teclado Gamer"

    history = get_price_history(product["id"])
    assert len(history) == 2
    assert history[0]["value"] == 299.90
    assert history[1]["value"] == 259.90
