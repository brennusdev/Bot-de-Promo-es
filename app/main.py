from app.collectors.router import get_product_data_for_url
from app.database.connection import init_db
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

    price = save_collected_price(product, data)

    return {
        "product": product,
        "price": price,
    }


def save_collected_price(product, data):
    """Registra o preço coletado, exceto quando a coleta falhou (preço 0).

    ESTUDO (dados): quando o scraper não encontra o preço, antes salvava
    0.0 no histórico — o que disparava alerta falso de "queda de 100%"
    e poluía o histórico. Melhor pular o registro e deixar o worker tentar
    de novo no próximo ciclo.
    """
    price_value = data.get("price") or 0
    if float(price_value) <= 0:
        return None
    return save_price(product["id"], price_value)


if __name__ == "__main__":
    result = process_product("https://www.mercadolivre.com.br/")
    print(result)
