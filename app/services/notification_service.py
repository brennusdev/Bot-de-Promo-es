def send_notification(user_id, message, product_info=None):
    """Despacha a notificação pelos canais configurados.

    ESTUDO (robustez): cada canal é independente — falha no e-mail não
    impede o registro no log. product_info (dict opcional) carrega os dados
    do produto para canais que precisam de formatação própria (ex.: e-mail
    HTML); quando ausente, só o log é gerado.
    """
    logger.info("Notificação para %s: %s", user_id, message.replace("\n", " | "))

    channels = ["log"]
    email_result = None

    if email_enabled() and product_info:
        html = build_alert_email_html(
            product_info["product_name"],
            product_info["current_price"],
            product_info["drop_percent"],
            product_info["product_url"],
        )
        subject = f"🚨 Queda de {product_info['drop_percent']:.0f}% — {product_info['product_name'][:60]}"
        email_result = send_email(subject, html)
        if email_result:
            channels.append("email")

    return {
        "status": "sent",
        "user_id": user_id,
        "message": message,
        "channels": channels,
        "email_sent": email_result,
    }


"""ESTUDO (arquitetura): fonte única de mensagens e despacho de notificações.

Este módulo concentra:
  - build_alert_message(): formatação única, reaproveitada por todos os canais
  - send_notification() / send_user_alert(): despacho multi-canal

Canais disponíveis:
  1. Log (sempre) — histórico de auditoria.
  2. E-mail (se SMTP configurado) — via app/services/email_service.py.

Canais novos (Telegram, push, etc.) devem ser adicionados AQUI, como um
passo a mais no pipeline — nunca espalhados pelos serviços chamadores.
"""

import logging

from app.services.email_service import build_alert_email_html, email_enabled, send_email

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
    return send_notification(
        user_id,
        message,
        product_info={
            "product_name": product_name,
            "current_price": current_price,
            "drop_percent": drop_percent,
            "product_url": product_url,
        },
    )
