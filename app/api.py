# API principal com FastAPI.
# Serve para expor os dados do projeto para frontend e outras integrações.

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool

from app.health import register_health_checks
from app.logging_config import configure_logging
from app.schemas import AlertCreate, ProductCreate, UserCreate
from app.services.alert_service import calculate_price_change
from app.services.price_service import get_price_history, get_recent_prices
from app.services.product_service import list_products
from app.services.user_service import create_user, list_users, save_alert, list_alerts

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
def get_products(limit: int | None = None, offset: int = 0):
    """Lista produtos cadastrados com paginação opcional.

    ESTUDO (API): ?limit=20&offset=0 — o dashboard pode paginar sem
    carregar a tabela inteira. Query params do FastAPI já validam tipos.
    """
    products = list_products(limit=limit, offset=offset)
    enriched = []
    for product in products:
        recent = get_recent_prices(product["id"], count=2)

        # ESTUDO (performance): antes isso buscava o histórico COMPLETO de cada
        # produto (uma query por produto, com milhares de linhas). Agora busca
        # só os 2 últimos preços — o índice idx_prices_product_id torna isso barato.
        current_price = float(recent[-1]["value"]) if recent else float(product.get("reference_price") or 0)
        previous = float(recent[-2]["value"]) if len(recent) >= 2 else (recent[0]["value"] if recent else None)
        if previous is not None:
            previous = float(previous)

        change = calculate_price_change(current_price, previous)
        product["current_price"] = current_price
        product["variation"] = change
        enriched.append(product)

    return enriched


@app.get("/products/{product_id}/history")
def get_product_history(product_id: int):
    """Retorna o histórico de preços de um produto."""
    return get_price_history(product_id)


@app.post("/products", status_code=201)
async def create_product(payload: ProductCreate):
    """Registra um produto a partir da URL (o coletor busca nome/preço).

    ESTUDO (performance): o scraping é síncrono (requests), então o handler
    é async e o trabalho pesado vai para o threadpool. Sem isso, vários
    cadastros simultâneos travariam o event loop da API.
    """
    from app.main import process_product  # import local evita ciclo de imports
    try:
        result = await run_in_threadpool(process_product, payload.url)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Falha ao coletar o produto: {exc}") from exc
    return {"product": result["product"], "price": result["price"]}


@app.get("/users")
def get_users():
    """Lista usuários cadastrados no sistema."""
    return list_users()


@app.post("/users", status_code=201)
def post_user(payload: UserCreate):
    """Cria um usuário para receber alertas.

    ESTUDO (REST): criação de recurso deve responder 201 Created, não 200.
    FastAPI usa o status_code do decorator automaticamente.
    """
    return create_user(name=payload.name, phone=payload.phone)


@app.post("/users/{user_id}/alerts", status_code=201)
def add_alert(user_id: int, payload: AlertCreate):
    """Cria um alerta para um produto de forma personalizada (201 Created)."""
    return save_alert(
        user_id=user_id,
        product_id=payload.product_id,
        threshold_percent=payload.threshold_percent,
    )


@app.get("/users/{user_id}/alerts")
def user_alerts(user_id: int):
    """Lista alertas de um usuário."""
    return list_alerts(user_id)
