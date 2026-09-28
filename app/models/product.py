# Modelo do produto.
# Ele guarda o nome, a URL, a loja, as especificações e a referência do mercado.

class Product:
    def __init__(
        self,
        id=None,
        name=None,
        url=None,
        store=None,
        price=None,
        specifications=None,
        market=None,
        promotion_score=None,
    ):
        self.id = id
        self.name = name
        self.url = url
        self.store = store
        self.price = price
        self.specifications = specifications or {}
        self.market = market
        self.promotion_score = promotion_score
