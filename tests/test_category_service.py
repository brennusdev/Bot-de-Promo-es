"""Testes do serviço de categorização."""
from app.services.category_service import detect_category, get_all_categories


def test_notebook():
    assert detect_category("Notebook Lenovo IdeaPad 3i 8GB 256GB SSD") == "notebook"
    assert detect_category("MacBook Air M2 13 polegadas") == "notebook"


def test_tablet():
    assert detect_category("Apple iPad 10ª geração 64GB") == "tablet"
    assert detect_category("Samsung Galaxy Tab A9 64GB") == "tablet"


def test_monitor():
    assert detect_category("Monitor Gamer LG UltraGear 24 144Hz") == "monitor"


def test_fone():
    assert detect_category("Fone de ouvido JBL Tune 510BT") == "fone"
    assert detect_category("Headset Gamer HyperX Cloud Stinger") == "fone"


def test_mouse():
    assert detect_category("Mouse Gamer Logitech G Pro X") == "mouse"


def test_teclado():
    assert detect_category("Teclado Mecânico Redragon Kumara ABNT2") == "teclado"


def test_outros_para_produto_desconhecido():
    assert detect_category("Cadeira Gamer") == "outros"
    assert detect_category("Cadeira Ergonômica") == "outros"


def test_falso_positivo_mousepad():
    # mousepad contém "mouse", mas é acessório
    assert detect_category("Mousepad Gamer Extra Grande 900x400") == "outros"


def test_falso_positivo_acessorio_notebook():
    assert detect_category("Memória RAM 8GB DDR4 para Notebook") == "outros"


def test_acentos_ignorados():
    assert detect_category("Teclado Mecânico") == "teclado"


def test_categorias_suportadas():
    cats = get_all_categories()
    assert "notebook" in cats and "outros" in cats
