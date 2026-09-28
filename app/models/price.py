# Modelo do histórico de preços.
# Cada coleta gera um registro novo para o mesmo produto.

class Price:
    def __init__(self, id=None, product_id=None, value=None, collected_at=None):
        self.id = id
        self.product_id = product_id
        self.value = value
        self.collected_at = collected_at
