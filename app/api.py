# API principal com FastAPI.
# Serve para expor os dados do projeto para frontend e outras integrações.

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.health import register_health_checks
from app.logging_config import configure_logging
from app.services.alert_service import calculate_price_change
from app.services.price_service import get_latest_price, get_price_history
from app.services.product_service import list_products
from app.services.user_service import create_user, list_users, save_alert, list_alerts
from app.services.whatsapp_service import verify_whatsapp_webhook, process_whatsapp_webhook

configure_logging()

app = FastAPI(title="Bot de Promoções", version="1.0.0")
register_health_checks(app)

frontend_dir = Path(__file__).resolve().parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


@app.get("/")
def root():
    """Endpoint simples de teste da API."""
    return {"message": "Bot de Promoções funcionando"}


@app.get("/dashboard")
def dashboard_page():
    """Serve o dashboard web do sistema."""
    return FileResponse(frontend_dir / "index.html")


@app.get("/products")
def get_products():
    """Lista todos os produtos cadastrados."""
    products = list_products()
    enriched = []
    for product in products:
        latest = get_latest_price(product["id"])
        current_price = float(latest["value"]) if latest else float(product.get("reference_price") or 0)
        previous = None
        history = get_price_history(product["id"])
        if len(history) >= 2:
            previous = float(history[-2]["value"])
        elif len(history) == 1:
            previous = float(history[0]["value"])

        change = calculate_price_change(current_price, previous)
        product["current_price"] = current_price
        product["variation"] = change
        enriched.append(product)

    return enriched


@app.get("/products/{product_id}/history")
def get_product_history(product_id: int):
    """Retorna o histórico de preços de um produto."""
    return get_price_history(product_id)


@app.get("/users")
def get_users():
    """Lista usuários cadastrados no sistema."""
    return list_users()


@app.post("/users")
def post_user(payload: dict):
    """Cria um usuário para receber alertas."""
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload inválido")
    name = payload.get("name")
    phone = payload.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="phone é obrigatório")
    return create_user(name=name, phone=phone)


@app.post("/users/{user_id}/alerts")
def add_alert(user_id: int, payload: dict):
    """Cria um alerta para um produto de forma personalizada."""
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload inválido")
    product_id = payload.get("product_id")
    threshold_percent = payload.get("threshold_percent", 10.0)
    if product_id is None:
        raise HTTPException(status_code=400, detail="product_id é obrigatório")
    try:
        value = float(threshold_percent)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="threshold_percent deve ser numérico") from None
    return save_alert(user_id=user_id, product_id=product_id, threshold_percent=value)


@app.get("/users/{user_id}/alerts")
def user_alerts(user_id: int):
    """Lista alertas de um usuário."""
    return list_alerts(user_id)


@app.get("/webhooks/whatsapp")
def whatsapp_webhook_verify(request: Request):
    """Valida o webhook do WhatsApp."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if verify_whatsapp_webhook(mode, token):
        return challenge
    raise HTTPException(status_code=403, detail="Token inválido")


@app.post("/webhooks/whatsapp")
async def whatsapp_webhook_post(request: Request):
    """Recebe eventos do WhatsApp e processa mensagens."""
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="JSON inválido") from exc
    return process_whatsapp_webhook(payload)
