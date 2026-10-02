from app.collectors.common import fetch_and_parse_product


def get_product_data(url):
    """Coleta dados de produtos da Amazon."""
    return fetch_and_parse_product(
        url=url,
        store_name="Amazon",
        market_name="amazon",
        title_selectors=[
            "#productTitle",
            "h1",
            "meta[property='og:title']",
        ],
        price_selectors=[
            ".a-price .a-offscreen",
            ".a-price-whole",
            ".a-price",
            "span[aria-label*='R$']",
        ],
    )
