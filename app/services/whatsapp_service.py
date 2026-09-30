from app.bot.handlers import handle_message
from app.config.settings import WHATSAPP_WEBHOOK_VERIFY_TOKEN
from app.main import process_product


def verify_whatsapp_webhook(mode, token):
    """Valida o webhook do WhatsApp usando o token configurado."""
    if not mode or not token:
        return False
    return mode == "subscribe" and token == WHATSAPP_WEBHOOK_VERIFY_TOKEN


def process_whatsapp_webhook(payload):
    """Processa mensagens recebidas pelo WhatsApp e encadeia com o bot."""
    if not isinstance(payload, dict):
        return {"status": "invalid_payload"}

    entries = payload.get("entry", [])
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes", []):
            if not isinstance(change, dict):
                continue
            value = change.get("value", {})
            if not isinstance(value, dict):
                continue
            for message in value.get("messages", []):
                if not isinstance(message, dict):
                    continue
                text = message.get("text", {}).get("body", "") if isinstance(message.get("text"), dict) else ""
                from_phone = message.get("from")
                if text:
                    result = handle_message(text)

                    if result.get("status") == "product_url_received":
                        try:
                            product_data = process_product(text)
                            result["product"] = product_data["product"]
                            result["price"] = product_data["price"]
                        except Exception as exc:
                            result = {"status": "product_error", "error": str(exc)}

                    return {
                        "status": result.get("status", "message_received"),
                        "from": from_phone,
                        "reply": result,
                    }

    return {"status": "no_message"}
