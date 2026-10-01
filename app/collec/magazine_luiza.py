from app.collec.common import fetch_and_parse_product


def get_product_data(url):
    """Coleta dados de produtos da Magazine Luiza."""
    return fetch_and_parse_product(
        url=url,
        store_name="Magazine Luiza",
        market_name="magazine_luiza",
        title_selectors=[
            "h1",
            "meta[property='og:title']",
            ".product-title",
        ],
        price_selectors=[
            "[data-testid='price']",
            "[data-testid='price-value']",
            ".price__current",
            ".product-price",
            "span[content]",
        ],
    )
