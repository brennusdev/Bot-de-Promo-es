# Serviço de monitoramento.
# Ele executa o ciclo de coleta, comparação e alerta.

from app.services.alert_dispatcher import dispatch_alerts_for_product
from app.services.alert_service import check_product_alert
from app.services.price_service import save_price
from app.services.product_service import list_products


def monitor_all_products(get_current_price_function):
    """Varre todos os produtos e verifica se a coleta atual gerou alerta."""
    results = []

    for product in list_products():
        current_price = get_current_price_function(product["url"])
        triggered, drop_percent = check_product_alert(product["id"], current_price)

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
