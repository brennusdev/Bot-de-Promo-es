from app.collectors.common import fetch_and_parse_product


def get_product_data(url):
    """Coleta dados de produtos da Casas Bahia."""
    return fetch_and_parse_product(
        url=url,
        store_name="Casas Bahia",
        market_name="casas_bahia",
        title_selectors=[
            "h1",
            "meta[property='og:title']",
            ".product-name",
        ],
        price_selectors=[
            ".price__sales",
            ".skuBestPrice",
            ".product-price",
            "span[content]",
        ],
    )
