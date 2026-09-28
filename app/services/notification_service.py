def send_notification(user_id, message):
    """Simula envio de notificação para o usuário."""
    print(f"Notificação para {user_id}: {message}")
    return {"status": "sent", "user_id": user_id, "message": message}


def send_user_alert(user_id, product_name, current_price, drop_percent, product_url):
    """Cria um alerta de texto para usuário e devolve o payload simples."""
    message = (
        f"🚨 Alerta de preço!\n"
        f"Produto: {product_name}\n"
        f"Preço atual: R$ {current_price:.2f}\n"
        f"Queda: {drop_percent:.2f}%\n"
        f"Link: {product_url}"
    )
    return send_notification(user_id, message)
