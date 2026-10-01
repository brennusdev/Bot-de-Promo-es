# REVISÃO (comentário de estudo):
# Antes este módulo fazia requests.get() direto, SEM:
#   - retries com backoff (sites de e-commerce falham seguido);
#   - User-Agent de navegador (sem isso o Mercado Livre pode bloquear com 403);
#   - fallback quando o preço não é encontrado (a coleta inteira quebrava).
# Os outros coletores (Amazon, KaBuM etc.) usam fetch_and_parse_product() do
# common.py, que já resolve tudo isso. Este módulo agora segue o MESMO padrão,
# herdando retries, UA e tolerância a falha de preço — e ainda garante as
# chaves "market", "specifications", "reference_price" e "promotion_score" no
# retorno, que o fluxo principal (app/main.py) espera.

from app.collec.common import fetch_and_parse_product


def get_product_data(url):
    """Coleta os dados básicos de um produto em uma página do Mercado Livre."""
    return fetch_and_parse_product(
        url=url,
        store_name="Mercado Livre",
        market_name="mercado_livre",
        title_selectors=[
            # Título principal da página de produto.
            "h1",
            # Fallback via metatag, compartilhada por todos os e-commerces.
            "meta[property='og:title']",
            # Nome exibido no card de resultado de busca.
            ".poly-component__title",
        ],
        price_selectors=[
            # Fração do preço no componente novo do Mercado Livre
            # (ex.: "8.599" em "R$ 8.599,00").
            ".andes-money-amount__fraction",
            # Componente antigo de preço, ainda presente em várias páginas.
            ".price-tag-fraction",
        ],
    )
