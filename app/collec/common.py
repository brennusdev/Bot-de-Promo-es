import re

import requests
from bs4 import BeautifulSoup


def normalize_price(value):
    """Converte textos de preço em float com suporte a R$ e variações de milhar."""
    if value is None:
        raise ValueError("Preço não encontrado")

    text = str(value).strip()
    cleaned = re.sub(r"[^0-9,\.]", "", text)
    if not cleaned:
        raise ValueError("Preço inválido")

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")

    return float(cleaned)


def extract_text_from_selectors(soup, selectors):
    for selector in selectors:
        if selector.startswith("meta["):
            element = soup.select_one(selector)
            if element and element.get("content"):
                return element.get("content")
            continue

        element = soup.select_one(selector)
        if element:
            text = element.get_text(" ", strip=True)
            if text:
                return text
    return None


def find_price_in_text(text):
    if not text:
        raise ValueError("Preço não encontrado")

    patterns = [
        r"R\$\s*[0-9]+(?:[\.,][0-9]{3})*(?:[\.,][0-9]{2})",
        r"[0-9]+(?:[\.,][0-9]{3})*(?:[\.,][0-9]{2})",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            candidate = matches[0]
            if isinstance(candidate, tuple):
                candidate = "".join(part for part in candidate if part)
            return normalize_price(candidate)
    raise ValueError("Preço não encontrado")


def fetch_and_parse_product(url, store_name, market_name, title_selectors, price_selectors):
    """Busca uma página e extrai nome e preço usando seletores por loja."""
    response = requests.get(url, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title = extract_text_from_selectors(soup, title_selectors)
    if not title:
        title_tag = soup.title
        title = title_tag.get_text(" ", strip=True) if title_tag else "Produto"

    price_text = extract_text_from_selectors(soup, price_selectors)
    if price_text is None:
        price_text = soup.get_text(" ", strip=True)

    try:
        price = find_price_in_text(price_text)
    except ValueError:
        price = 0.0

    return {
        "name": title[:200],
        "price": price,
        "url": url,
        "store": store_name,
        "market": market_name,
        "specifications": {
            "categoria": "sem categoria",
            "marca": "sem marca",
        },
        "reference_price": price,
        "promotion_score": 0,
    }
