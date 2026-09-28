# Serviço de notificação para Telegram.
# Aqui fica a lógica de mandar a mensagem quando o alerta dispara.


def send_telegram_message(chat_id, message):
    """Simula envio de mensagem para Telegram."""
    print(f"[Telegram] chat_id={chat_id} | message={message}")
    return True


def build_alert_message(product_name, current_price, drop_percent, product_url):
    """Cria a mensagem de alerta para o usuário."""
    return (
        f"🚨 Alerta de preço!\n"
        f"Produto: {product_name}\n"
        f"Preço atual: R$ {current_price:.2f}\n"
        f"Queda: {drop_percent:.2f}%\n"
        f"Link: {product_url}"
    )
