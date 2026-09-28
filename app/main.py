from app.collec.router import get_product_data_for_url
from app.database.connection import init_db
from app.services.price_service import save_price
from app.services.product_service import save_product


def process_product(url, store_name=None, market=None):
    """Fluxo completo: coleta, salva o produto e registra o preço atual."""
    init_db()

    data = get_product_data_for_url(url)

    product = save_product(
        name=data["name"],
        url=data["url"],
        store=data.get("store", store_name or "Loja desconhecida"),
        market=data.get("market", market or "desconhecida"),
        specifications=data.get("specifications", {}),
        reference_price=data.get("reference_price", 0),
        promotion_score=data.get("promotion_score", 0),
    )

    price = save_price(product["id"], data["price"])

    return {
        "product": product,
        "price": price,
    }


if __name__ == "__main__":
    result = process_product("https://www.mercadolivre.com.br/")
    print(result)
