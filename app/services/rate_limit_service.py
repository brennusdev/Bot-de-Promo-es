# Rate limit persistido no banco de dados.
#
# ESTUDO (serverless): a versão antiga guardava os hits em memória
# (defaultdict). Na Vercel cada invocação tem memória própria, então o
# limite ficava por instância e não global — praticamente inútil lá.
# A tabela rate_limit_hits (criada em init_db) guarda IP, timestamp e
# janela no banco, funcionando igual em qualquer backend (SQLite/Postgres).
import time

from app.database.connection import get_connection, get_database_backend, get_placeholder

# Padrões: 10 cadastros por minuto por IP (mesmos defaults da versão antiga).
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60


def configure_rate_limit(max_requests: int, window_seconds: int) -> None:
    """Aplica configuração vinda de variáveis de ambiente (chamada pela API)."""
    global RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS
    RATE_LIMIT_MAX_REQUESTS = max_requests
    RATE_LIMIT_WINDOW_SECONDS = window_seconds


def check_rate_limit(client_ip: str) -> None:
    """Lança RuntimeError se o IP exceder o limite de cadastros na janela.

    ESTUDO (SQL): a limpeza de registros antigos roda no mesmo commit do
    insert — uma única viagem ao banco. O índice idx_rate_limit_ip deixa
    a contagem O(log n) mesmo com muitos IPs acumulados.
    """
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    ph = get_placeholder()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT COUNT(*) FROM rate_limit_hits WHERE ip = {ph} AND created_at > {ph}",
        (client_ip, cutoff),
    )
    hits = cursor.fetchone()[0]

    if hits >= RATE_LIMIT_MAX_REQUESTS:
        conn.close()
        raise PermissionError(
            f"Muitas requisições. Tente novamente em instantes."
        )

    cursor.execute(
        f"INSERT INTO rate_limit_hits (ip, created_at) VALUES ({ph}, {ph})",
        (client_ip, now),
    )
    cursor.execute(
        f"DELETE FROM rate_limit_hits WHERE created_at < {ph}",
        (cutoff - RATE_LIMIT_WINDOW_SECONDS,),
    )
    conn.commit()
    conn.close()


def cleanup_rate_limit(max_age_seconds: int = 86400) -> int:
    """Remove registros muito antigos (retenção). Chamado pelo cron/worker."""
    cutoff = time.time() - max_age_seconds
    ph = get_placeholder()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM rate_limit_hits WHERE created_at < {ph}", (cutoff,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def backend_name() -> str:
    """Nome do backend ativo (debug/testes)."""
    return get_database_backend()
