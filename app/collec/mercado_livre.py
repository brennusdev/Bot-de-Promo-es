import re

import requests
from bs4 import BeautifulSoup


def _parse_price_text(value):
    """Converte textos de preço em float com tolerância a variações de formatacao."""
    if not value:
        raise ValueError("Preço não encontrado")

    cleaned = re.sub(r"[^0-9,\.]", "", value)
    if not cleaned:
        raise ValueError("Preço inválido")

    if cleaned.count(",") > 0 and cleaned.count(".") == 0:
        cleaned = cleaned.replace(",", ".")
    elif cleaned.count(".") > 0 and cleaned.count(",") > 0:
        cleaned = cleaned.replace(".", "").replace(",", ".")

    return float(cleaned)


def get_product_data(url):
    """Coleta os dados básicos de um produto em uma página do Mercado Livre."""
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    name_tag = soup.find("h1")
    if not name_tag:
        raise ValueError("Não foi possível encontrar o nome do produto.")
    name = name_tag.get_text(strip=True)

    price_tag = soup.select_one(".price-tag") or soup.select_one(".andes-money-amount__fraction") or soup.select_one(".andes-money-amount__fraction")
    if not price_tag:
        raise ValueError("Não foi possível encontrar o preço do produto.")

    price_value = _parse_price_text(price_tag.get_text(strip=True))

    return {
        "name": name,
        "price": price_value,
        "url": url,
        "store": "Mercado Livre",
    }
