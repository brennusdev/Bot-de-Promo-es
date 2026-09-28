# Modelo de mercado.
# Representa a origem do produto e o site em que ele foi coletado.

class Market:
    def __init__(self, id=None, name=None, url=None):
        self.id = id
        self.name = name
        self.url = url
