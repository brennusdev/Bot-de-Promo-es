from app.collec.common import fetch_and_parse_product


def get_product_data(url):
    """Coleta dados de produtos da Pichau."""
    return fetch_and_parse_product(
        url=url,
        store_name="Pichau",
        market_name="pichau",
        title_selectors=[
            "h1",
            "meta[property='og:title']",
            ".product-title",
        ],
        price_selectors=[
            ".price",
            ".product-price",
            ".promo-price",
            "span[content]",
        ],
    )
