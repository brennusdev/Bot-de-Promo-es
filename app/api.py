# API principal com FastAPI.
# Serve para expor os dados do projeto para frontend e outras integrações.

from pathlib import Path
import os
import time
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool

from app.health import register_health_checks
from app.logging_config import configure_logging
from app.schemas import AdminLogin, AlertCreate, ProductCreate, UserCreate
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

# ===== Rate limit simples (memória) =====
# ESTUDO (segurança): limita cadastros por IP para evitar abuso do endpoint
# público. Janela deslizante em memória — para uma instância única, isso é
# suficiente sem dependência externa (sem Redis).
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "10"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
_rate_limit_hits: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(request: Request) -> None:
    """Lança 429 se o IP exceder o limite de cadastros na janela."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    hits = _rate_limit_hits[client_ip]
    _rate_limit_hits[client_ip] = [t for t in hits if now - t < RATE_LIMIT_WINDOW_SECONDS]
    if len(_rate_limit_hits[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Muitas requisições. Tente novamente em instantes.")
    _rate_limit_hits[client_ip].append(now)


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
