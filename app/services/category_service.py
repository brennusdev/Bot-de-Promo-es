"""Categorização de produtos por palavras-chave no nome.

ESTUDO: os coletores não expõem a categoria oficial da loja (só título e
preço), então classificamos pelo nome do produto. As categorias cobrem os
grupos que o cliente acompanha: Notebook, Tablet, Monitor, Fone, Mouse,
Teclado — com fallback "Outros" para o que não se encaixar.
"""
import re

# Ordem importa: termos mais específicos primeiro (ex.: "mousepad" não é mouse;
# "headset gamer com microfone" é fone; "dock monitor" não deve virar monitor).
CATEGORY_KEYWORDS = [
    ("notebook", [
        "notebook", "laptop", "macbook", "ultrabook", "chromebook",
        "netbook", "2 em 1", "2-em-1",
    ]),
    ("tablet", [
        "tablet", "ipad", "galaxy tab", "tab s", "fire hd", "e-reader",
        "kindle",
    ]),
    ("monitor", [
        "monitor", "painel gamer", "tela led", "tela lcd",
        "display 24", "display 27", "display 32",
    ]),
    ("fone", [
        "fone", "headset", "earphone", "earbuds", "airpods", "galaxy buds",
        "tws", "intra-auricular", "supra-auricular", "microfone gamer",
    ]),
    ("mouse", [
        "mouse", "ratão gamer", "raton", "magic mouse",
    ]),
    ("teclado", [
        "teclado", "keyboard", "keychron", "nuphy", "tenkeyless", "tkl",
        " ABNT2", "mecanico", "mecânico",
    ]),
]

# Palavras que NÃO devem categorizar mesmo contendo o termo (falsos positivos).
NEGATIVE_PATTERNS = [
    r"mousepad",          # acessório, não mouse
    r"suporte (de|para) (notebook|monitor|tablet|fone)",
    r"capa (para|de) (notebook|tablet)",
    r"cooler (para|de) notebook",
    r"mem[óo]ria.*notebook",
    r"ssd.*notebook",
    r"mesa|bancada|travesseiro",  # móveis que citam notebook
]


def detect_category(product_name: str) -> str:
    """Identifica a categoria do produto pelo nome (sem acento, minúsculo)."""
    text = (product_name or "").lower()
    text = _strip_accents(text)

    for pattern in NEGATIVE_PATTERNS:
        if re.search(pattern, text):
            return "outros"

    for category, keywords in CATEGORY_KEYWORDS:
        for keyword in keywords:
            kw = _strip_accents(keyword.lower())
            # match por palavra inteira quando curto, substring quando longo
            if len(kw) <= 5:
                if re.search(rf"\b{re.escape(kw)}\b", text):
                    return category
            elif kw in text:
                return category

    return "outros"


def get_all_categories() -> list[str]:
    """Lista de categorias suportadas, para filtro do dashboard/API."""
    return [category for category, _ in CATEGORY_KEYWORDS] + ["outros"]


def _strip_accents(text: str) -> str:
    """Remove acentos para casar 'mecânico' com 'mecanico', etc."""
    import unicodedata
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )
