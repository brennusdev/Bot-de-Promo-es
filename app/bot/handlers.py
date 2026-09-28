def handle_message(message):
    """Recebe a mensagem do usuário e decide o que fazer."""
    text = (message or "").strip()
    if not text:
        return {"text": "", "status": "empty_message"}

    if text.startswith("/start"):
        return {
            "text": "Olá! Envie a URL do produto para acompanhar o preço.",
            "status": "started",
        }

    if text.startswith("http://") or text.startswith("https://"):
        return {
            "text": text,
            "status": "product_url_received",
        }

    return {
        "text": text,
        "status": "message_received",
    }
