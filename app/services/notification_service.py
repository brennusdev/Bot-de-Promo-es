def send_notification(user_id, message):
    """Envia a notificação. HOJE: simulado (log).

    ESTUDO: para integrar um canal real (Telegram, WhatsApp, e-mail),
    troque este ponto único de saída — todos os alertas do sistema
    passam por aqui, então a mudança vale para o projeto inteiro.
    """
    logger.info("Notificação para %s: %s", user_id, message.replace("\n", " | "))
    return {"status": "sent", "user_id": user_id, "message": message}


"""ESTUDO (arquitetura): fonte única de mensagens e despacho de notificações.

Antes havia dois módulos duplicados:
  - app/services/notification_service.py  (usado pelo alert_dispatcher)
  - app/telegram/notification_service.py  (cópia com a mesma formatação)

Agora este módulo concentra:
  - build_alert_message(): formatação única, reaproveitada por todos os canais
  - send_notification() / send_user_alert(): envio genérico (hoje simulado via log)

Canais específicos (ex.: Telegram) devem importar daqui em vez de recriar
a mensagem — assim um ajuste de texto reflete em todos os canais de uma vez.
"""

import logging

logger = logging.getLogger("pricebot.notification")


def build_alert_message(product_name, current_price, drop_percent, product_url):
    """Monta a mensagem de alerta (fonte única, reutilizada por todos os canais)."""
    return (
        f"🚨 Alerta de preço!\n"
        f"Produto: {product_name}\n"
        f"Preço atual: R$ {current_price:.2f}\n"
        f"Queda: {drop_percent:.2f}%\n"
        f"Link: {product_url}"
    )


def send_user_alert(user_id, product_name, current_price, drop_percent, product_url):
    """Cria um alerta de texto para usuário e devolve o payload simples."""
    message = build_alert_message(product_name, current_price, drop_percent, product_url)
    return send_notification(user_id, message)
