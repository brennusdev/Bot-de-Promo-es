from app.collec.common import fetch_and_parse_product


def get_product_data(url):
    """Coleta dados de produtos da KaBuM."""
    return fetch_and_parse_product(
        url=url,
        store_name="KaBuM",
        market_name="kabum",
        title_selectors=[
            "h1",
            "meta[property='og:title']",
            ".product-name",
        ],
        price_selectors=[
            ".final-price",
            ".price-current",
            ".prices .price",
            "span[content]",
        ],
    )
