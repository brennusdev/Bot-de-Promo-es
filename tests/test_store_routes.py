from app.collec.router import detect_store_from_url


def test_detect_store_from_url_for_all_supported_markets():
    assert detect_store_from_url("https://www.amazon.com.br/teclado") == "amazon"
    assert detect_store_from_url("https://www.mercadolivre.com.br/teclado") == "mercado_livre"
    assert detect_store_from_url("https://www.kabum.com.br/produto/teclado") == "kabum"
    assert detect_store_from_url("https://www.pichau.com.br/teclado") == "pichau"
    assert detect_store_from_url("https://www.casasbahia.com.br/teclado") == "casas_bahia"
    assert detect_store_from_url("https://www.magazineluiza.com.br/teclado") == "magazine_luiza"
