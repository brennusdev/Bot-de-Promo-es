import logging
import re
import time

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("pricebot.collec")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def fetch_with_retry(url, attempts=3, timeout=20):
    """Baixa a página com retries e backoff simples (sites de e-commerce falham com frequência)."""
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(
                url,
                timeout=timeout,
                headers={"User-Agent": USER_AGENT, "Accept-Language": "pt-BR,pt;q=0.9"},
            )
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(2 ** attempt)
                logger.warning("Tentativa %s/%s falhou para %s: %s", attempt, attempts, url, exc)
    raise last_error


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
    response = fetch_with_retry(url)

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
