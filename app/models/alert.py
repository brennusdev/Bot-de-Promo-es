# Modelo de alerta.
# Guarda a condição que dispara notificação para o usuário.

class Alert:
    def __init__(self, id=None, product_id=None, target_price=None, active=True):
        self.id = id
        self.product_id = product_id
        self.target_price = target_price
        self.active = active
