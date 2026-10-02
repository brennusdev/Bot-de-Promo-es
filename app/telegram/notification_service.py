# ESTUDO (arquitetura): adapter do canal Telegram.
# NÃO recria a mensagem: delega a formatação ao módulo único
# (app/services/notification_service.py). Qualquer canal novo segue
# o mesmo padrão — um adapter fino sobre a fonte única.
from app.services.notification_service import build_alert_message, send_notification


def send_telegram_message(chat_id, message):
    """Envia a mensagem pelo Telegram (hoje simulado via envio genérico)."""
    return send_notification(chat_id, message)


def build_telegram_alert(product_name, current_price, drop_percent, product_url):
    """Cria a mensagem de alerta para o usuário (delega ao construtor único)."""
    return build_alert_message(product_name, current_price, drop_percent, product_url)
