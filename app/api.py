# API principal com FastAPI.
# Serve para expor os dados do projeto para frontend e outras integrações.

from pathlib import Path
import os
import time

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool

from app.health import register_health_checks
from app.logging_config import configure_logging
from app.schemas import AdminLogin, AlertCreate, ProductCreate, UserCreate
from app.services import rate_limit_service
from app.services.alert_service import calculate_price_change
from app.services.price_service import get_price_history, get_recent_prices
from app.services.product_service import delete_product, list_products
from app.services.user_service import create_user, list_users, save_alert, list_alerts

configure_logging()

# ===== Autenticação administrativa simples =====
# ESTUDO (segurança): se ADMIN_PASSWORD estiver definido, as rotas de escrita
# (POST/DELETE) exigem o header X-Admin-Token com a senha. Leitura (GET)
# continua aberta — o cliente só precisa VER os produtos.
# Em produção, configure ADMIN_PASSWORD no .env do provedor.
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# ===== Rate limit (persistido no banco) =====
# ESTUDO (serverless): a versão antiga usava memória por processo — na Vercel
# cada invocação tem memória própria, então o limite não era global. Agora os
# hits vão para a tabela rate_limit_hits, criada em init_db.
rate_limit_service.configure_rate_limit(
    max_requests=int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "10")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
)

# ===== Cron (worker serverless) =====
# ESTUDO (arquitetura): o worker original tem while True — impossível na
# Vercel Functions. O endpoint /cron/monitor executa UM ciclo de coleta e é
# disparado periodicamente pelo cron do vercel.json (ver CRON_SECRET).
CRON_SECRET = os.getenv("CRON_SECRET", "")


def require_cron_secret(request: Request) -> None:
    """Valida o header x-cron-secret. Em dev (sem CRON_SECRET) fica aberto."""
    if not CRON_SECRET:
        return
    if request.headers.get("x-cron-secret", "") != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Cron secret inválido")


def check_rate_limit(request: Request) -> None:
    """Lança 429 se o IP exceder o limite de cadastros na janela."""
    client_ip = request.client.host if request.client else "unknown"
    try:
        rate_limit_service.check_rate_limit(client_ip)
    except PermissionError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


def require_admin(request: Request) -> None:
    """Exige senha administrativa nas rotas de escrita (se configurada)."""
    if not ADMIN_PASSWORD:
        return  # sem senha configurada (dev): rotas abertas
    if request.headers.get("X-Admin-Token", "") != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Senha administrativa incorreta")


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


@app.get("/products/view")
def product_detail_page():
    """Página de detalhe do produto com gráfico de histórico (ECharts)."""
    return FileResponse(frontend_dir / "product.html")


@app.get("/products")
def get_products(limit: int | None = None, offset: int = 0, category: str | None = None):
    """Lista produtos cadastrados com paginação e filtro opcional por categoria.

    ESTUDO (API): ?limit=20&offset=0 — o dashboard pode paginar sem
    carregar a tabela inteira. Query params do FastAPI já validam tipos.
    ?category=notebook filtra pela categoria detectada.
    """
    products = list_products(limit=limit, offset=offset, category=category)
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


@app.get("/categories")
def get_categories():
    """Categorias suportadas com contagem de produtos em cada uma.

    ESTUDO (API): o dashboard usa isso para montar os botões de filtro por
    categoria (Notebook, Tablet, Monitor, Fone, Mouse, Teclado) e mostrar
    quantos produtos existem em cada grupo.
    """
    products = list_products()
    counts: dict[str, int] = {}
    for product in products:
        counts[product.get("category") or "outros"] = counts.get(product.get("category") or "outros", 0) + 1
    return {"categories": counts}


@app.get("/offers/new")
def get_new_offers(since_id: int = 0):
    """Produtos com ofertas desde a última verificação do cliente.

    ESTUDO (popup): o dashboard guarda o maior id de produto já visto
    (localStorage). A cada refresh, pergunta "tem produto novo desde o id
    X?" — se sim, exibe o popup 'Você tem novas ofertas' com a lista.
    since_id=0 devolve os últimos produtos (usado na primeira visita).
    """
    products = list_products(limit=20)
    fresh = [p for p in products if p["id"] > since_id]
    return {
        "has_new": len(fresh) > 0,
        "count": len(fresh),
        "latest_id": max((p["id"] for p in products), default=0),
        "offers": fresh,
    }


@app.post("/products", status_code=201)
async def create_product(payload: ProductCreate, request: Request):
    """Registra um produto a partir da URL (o coletor busca nome/preço).

    ESTUDO (performance): o scraping é síncrono (requests), então o handler
    é async e o trabalho pesado vai para o threadpool. Sem isso, vários
    cadastros simultâneos travariam o event loop da API.
    ESTUDO (segurança): rate limit por IP + senha admin opcional.
    """
    check_rate_limit(request)
    require_admin(request)
    from app.main import process_product  # import local evita ciclo de imports
    try:
        result = await run_in_threadpool(process_product, str(payload.url))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Falha ao coletar o produto: {exc}") from exc
    return {"product": result["product"], "price": result["price"]}


@app.delete("/products/{product_id}", status_code=204)
def remove_product(product_id: int, request: Request):
    """Remove um produto, seus preços e alertas (204 No Content)."""
    require_admin(request)
    if not delete_product(product_id):
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return None


@app.post("/admin/login")
def admin_login(payload: AdminLogin, response: Response):
    """Valida a senha administrativa e devolve o token para o dashboard.

    ESTUDO: sem sessão de servidor — o dashboard guarda a senha em
    sessionStorage e envia em X-Admin-Token nas rotas de escrita.
    """
    if ADMIN_PASSWORD and payload.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Senha incorreta")
    return {"ok": True, "required": bool(ADMIN_PASSWORD)}


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


@app.post("/cron/monitor")
def cron_monitor(request: Request):
    """Executa UM ciclo completo de coleta + alerta e retorna o resumo.

    ESTUDO (serverless): substitui o while True do worker local. Chamado
    automaticamente pelo cron do vercel.json (ou manualmente com o header
    x-cron-secret). Em dev, sem CRON_SECRET, fica aberto para testes.

    ESTUDO (performance): scraping é síncrono (requests), então roda no
    threadpool — a Vercel permite até 60s por invocação no plano Hobby;
    se a base crescer muito, divida o ciclo em lotes (?limit=N).
    """
    require_cron_secret(request)
    from app.main import process_product  # import local evita ciclo de imports
    from app.workers.price_worker import (
        PRICE_RETENTION_DAYS,
        REQUEST_DELAY_SECONDS,
        fetch_current_price_for_url,
    )
    from app.database.connection import cleanup_old_prices, init_db
    from app.services.monitor_service import monitor_all_products
    from app.services.rate_limit_service import cleanup_rate_limit

    init_db()
    results = monitor_all_products(
        fetch_current_price_for_url,
        delay_seconds=REQUEST_DELAY_SECONDS,
    )
    deleted_prices = cleanup_old_prices(days_to_keep=PRICE_RETENTION_DAYS)
    cleanup_rate_limit()

    triggered = sum(1 for r in results if r.get("alert_triggered"))
    return {
        "status": "ok",
        "processed": len(results),
        "alerts_triggered": triggered,
        "prices_cleaned": deleted_prices,
        "results": results,
    }
