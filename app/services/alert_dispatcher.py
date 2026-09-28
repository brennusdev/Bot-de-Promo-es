from app.services.alert_service import check_product_alert
from app.services.notification_service import send_user_alert
from app.services.user_service import list_alerts_for_product


def dispatch_alerts_for_product(product, current_price):
    """Dispara alertas para todos os usuários que monitoram um produto."""
    product_id = product["id"]
    product_name = product["name"]
    product_url = product["url"]

    triggered, drop_percent = check_product_alert(product_id, current_price)
    if not triggered:
        return {"triggered": False, "drop_percent": drop_percent}

    alerts = list_alerts_for_product(product_id)
    sent = []
    for alert in alerts:
        sent.append(
            send_user_alert(
                alert["user_id"],
                product_name,
                current_price,
                drop_percent,
                product_url,
            )
        )

    return {
        "triggered": True,
        "drop_percent": drop_percent,
        "alerts_sent": len(sent),
        "deliveries": sent,
    }
