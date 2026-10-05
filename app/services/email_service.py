"""Notificação por e-mail (SMTP) — canal real de alertas.

ESTUDO (arquitetura): o ponto único de saída continua sendo
app/services/notification_service.py. Este módulo é o adapter de e-mail:
se SMTP_HOST não estiver configurado, o envio é desativado silenciosamente
(os alertas continuam indo para o log, comportamento anterior).

Configuração (variáveis de ambiente):
    SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASSWORD
    ALERT_EMAIL_FROM (remetente; default = SMTP_USER)
    ALERT_EMAIL_TO   (destinatários separados por vírgula)
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("pricebot.email")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM", "") or SMTP_USER
ALERT_EMAIL_TO = [
    address.strip()
    for address in os.getenv("ALERT_EMAIL_TO", "").split(",")
    if address.strip()
]


def email_enabled() -> bool:
    """Email só é enviado com host, remetente e destinatário configurados."""
    return bool(SMTP_HOST and ALERT_EMAIL_FROM and ALERT_EMAIL_TO)


def send_email(subject: str, html_body: str) -> bool:
    """Envia um e-mail HTML via SMTP com STARTTLS. Retorna True se enviado."""
    if not email_enabled():
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = ALERT_EMAIL_FROM
    message["To"] = ", ".join(ALERT_EMAIL_TO)
    message.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(ALERT_EMAIL_FROM, ALERT_EMAIL_TO, message.as_string())
        logger.info("E-mail de alerta enviado para %s", ALERT_EMAIL_TO)
        return True
    except Exception:
        # Falha de e-mail não pode derrubar o ciclo do worker.
        logger.exception("Falha ao enviar e-mail de alerta")
        return False


def build_alert_email_html(product_name: str, current_price: float, drop_percent: float, product_url: str) -> str:
    """Monta o corpo HTML do e-mail de alerta de preço."""
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;
                border:1px solid #e5e7eb;border-radius:12px;overflow:hidden">
      <div style="background:#0f172a;color:#22c55e;padding:20px 24px">
        <h2 style="margin:0;font-size:18px">🚨 Alerta de preço!</h2>
      </div>
      <div style="padding:24px;color:#111827">
        <p style="margin:0 0 12px;font-size:15px"><strong>{product_name}</strong></p>
        <p style="margin:0 0 6px;font-size:14px">
          Preço atual: <strong style="font-size:17px">R$ {current_price:.2f}</strong>
        </p>
        <p style="margin:0 0 18px;font-size:14px;color:#16a34a">
          ⬇ Queda de <strong>{drop_percent:.1f}%</strong>
        </p>
        <a href="{product_url}"
           style="background:#22c55e;color:#052e16;padding:11px 20px;
                  border-radius:999px;text-decoration:none;font-weight:bold;font-size:14px">
          Ver oferta na loja
        </a>
      </div>
      <div style="background:#f9fafb;padding:14px 24px;font-size:11px;color:#6b7280">
        Enviado automaticamente pelo Bot de Promoções.
      </div>
    </div>
    """
