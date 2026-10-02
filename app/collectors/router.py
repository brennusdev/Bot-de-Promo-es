from importlib import import_module
from urllib.parse import urlparse


STORE_MAP = {
    "amazon": "app.collectors.amazon",
    "mercado_livre": "app.collectors.mercado_livre",
    "kabum": "app.collectors.kabum",
    "pichau": "app.collectors.pichau",
    "casas_bahia": "app.collectors.casas_bahia",
    "magazine_luiza": "app.collectors.magazine_luiza",
}


def detect_store_from_url(url):
    """Identifica a loja pela URL do produto."""
    host = urlparse(url).netloc.lower()

    if "amazon" in host:
        return "amazon"
    if "mercadolivre" in host or "mercadolibre" in host:
        return "mercado_livre"
    if "kabum" in host:
        return "kabum"
    if "pichau" in host:
        return "pichau"
    if "casasbahia" in host:
        return "casas_bahia"
    if "magazineluiza" in host:
        return "magazine_luiza"

    raise ValueError(f"Loja não suportada para a URL: {url}")


def get_product_data_for_url(url):
    """Retorna os dados do produto usando o coletor correto da loja."""
    market = detect_store_from_url(url)
    module = import_module(STORE_MAP[market])
    return module.get_product_data(url)
