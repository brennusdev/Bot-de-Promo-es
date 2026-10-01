import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config.settings import REDIS_URL
from app.database.connection import get_connection


def _database_ok():
    conn = get_connection()
    try:
        conn.execute("SELECT 1")
        return True, "ok"
    except Exception as exc:
        return False, str(exc)
    finally:
        conn.close()


def _redis_ok():
    try:
        import redis

        client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        client.ping()
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


# NOTA DE ESTUDO (revisão do projeto):
# Antes, o /health retornava 503 se QUALQUER dependência (banco OU redis) falhasse.
# Problema: em desenvolvimento (e em alguns deploys serverless) o Redis não roda,
# o que fazia o healthcheck do provedor derrubar a aplicação mesmo com o banco OK.
#
# CORREÇÃO: o banco de dados é a dependência CRÍTICA (sem ele nada funciona).
# O Redis aqui é apenas cache/opcional — se estiver fora, avisamos com status
# "degraded" (200), mas não derrubamos o serviço. Em produção, se você quiser
# voltar a exigir Redis, basta definir REDIS_REQUIRED=true no .env.
REDIS_REQUIRED = os.getenv("REDIS_REQUIRED", "false").lower() == "true"


def register_health_checks(app: FastAPI) -> None:
    """Registra endpoints de saúde para monitoramento."""

    @app.get("/health")
    def health_check():
        # CORREÇÃO (revisão): banco é crítico, Redis é opcional.
        # - Banco fora  -> 503 (provedor deve reiniciar/subir alerta)
        # - Redis fora  -> 200 com status "degraded" (serviço segue de pé)
        # - REDIS_REQUIRED=true no .env restaura o comportamento antigo.
        db_ok, db_detail = _database_ok()
        redis_ok, redis_detail = _redis_ok()

        if not db_ok:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "database": {"ok": db_ok, "detail": db_detail},
                    "redis": {"ok": redis_ok, "detail": redis_detail},
                },
            )

        # Banco OK mas Redis fora (e não obrigatório): degraded, porém saudável.
        if not redis_ok and not REDIS_REQUIRED:
            return {
                "status": "degraded",
                "database": {"ok": db_ok, "detail": db_detail},
                "redis": {"ok": redis_ok, "detail": redis_detail},
            }

        # Redis obrigatório em produção e fora do ar -> 503.
        if not redis_ok and REDIS_REQUIRED:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "database": {"ok": db_ok, "detail": db_detail},
                    "redis": {"ok": redis_ok, "detail": redis_detail},
                },
            )

        return {
            "status": "ok",
            "database": {"ok": db_ok, "detail": db_detail},
            "redis": {"ok": redis_ok, "detail": redis_detail},
        }

    @app.get("/ready")
    def readiness_check():
        db_ok, _ = _database_ok()
        if not db_ok:
            return JSONResponse(status_code=503, content={"status": "not_ready", "database": "unavailable"})
        return {"status": "ready", "database": "available"}
