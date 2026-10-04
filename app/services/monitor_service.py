# Serviço de monitoramento.
# Ele executa o ciclo de coleta, comparação e alerta.

import time

from app.services.alert_dispatcher import dispatch_alerts_for_product
from app.services.alert_service import check_product_alert
from app.services.price_service import save_price
from app.services.product_service import list_products


def monitor_all_products(get_current_price_function, delay_seconds=0):
    """Varre todos os produtos e verifica se a coleta atual gerou alerta.

    delay_seconds: pausa entre produtos para não martelar as lojas com
    requisições seguidas (evita bloqueio de IP). 0 mantém o comportamento
    original (útil em testes).
    """
    results = []

    for index, product in enumerate(list_products()):
        if index > 0 and delay_seconds > 0:
            time.sleep(delay_seconds)

        current_price = get_current_price_function(product["url"])
        triggered, drop_percent = check_product_alert(product["id"], current_price)

        # Não poluir o histórico quando a coleta falha (preço 0 ou negativo).
        if current_price and current_price > 0:
            save_price(product["id"], current_price)

        dispatch = dispatch_alerts_for_product(product, current_price)

        results.append({
            "product_id": product["id"],
            "product_name": product["name"],
            "current_price": current_price,
            "drop_percent": drop_percent,
            "alert_triggered": triggered,
            "dispatch": dispatch,
        })

    return results
