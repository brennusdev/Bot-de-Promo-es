# Serviço de alerta.
# Ele decide se a queda do preço é grande o suficiente para disparar notificação.

from app.services.price_service import get_latest_price


def calculate_drop_percent(current_price, previous_price):
    """Calcula a queda percentual em relação ao preço anterior."""
    if previous_price is None or previous_price <= 0:
        return 0.0

    return ((previous_price - current_price) / previous_price) * 100


def calculate_price_change(current_price, previous_price):
    """Calcula variação absoluta e percentual entre preços, útil para painel e alertas."""
    if previous_price is None or previous_price == 0:
        return {
            "delta": 0.0,
            "percent_change": 0.0,
            "trend": "igual",
        }

    delta = float(current_price) - float(previous_price)
    percent_change = ((float(current_price) - float(previous_price)) / float(previous_price)) * 100

    if abs(percent_change) < 0.0001:
        trend = "igual"
    elif percent_change > 0:
        trend = "mais_caro"
    else:
        trend = "mais_barato"

    return {
        "delta": round(delta, 2),
        "percent_change": round(percent_change, 2),
        "trend": trend,
    }


def should_alert(current_price, previous_price, threshold_percent=10.0):
    """Retorna True se a queda foi maior ou igual ao limite configurado."""
    drop_percent = calculate_drop_percent(current_price, previous_price)
    return drop_percent >= threshold_percent, round(drop_percent, 2)


def check_product_alert(product_id, current_price, threshold_percent=10.0):
    """Busca o último valor registrado e verifica se houve queda relevante."""
    latest = get_latest_price(product_id)

    if latest is None:
        return False, 0.0

    previous_price = float(latest["value"])
    return should_alert(current_price, previous_price, threshold_percent)
