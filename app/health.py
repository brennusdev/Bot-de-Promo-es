import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse

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


# NOTA DE REVISÃO:
# O Redis foi removido do projeto — nenhum código o usava de fato (só constava
# no health check, settings e docker-compose). Se um dia o cache fizer sentido
# (ex.: cachear o dashboard), reintroduza com uma variável REDIS_URL e um
# health check "degraded" como o que existia antes.


def register_health_checks(app: FastAPI) -> None:
    """Registra endpoints de saúde para monitoramento."""

    @app.get("/health")
    def health_check():
        # O banco é a única dependência crítica: sem ele nada funciona.
        # Banco fora -> 503 (o provedor reinicia o serviço / sobe alerta).
        db_ok, db_detail = _database_ok()

        if not db_ok:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "database": {"ok": db_ok, "detail": db_detail},
                },
            )

        return {
            "status": "ok",
            "database": {"ok": db_ok, "detail": db_detail},
        }

    @app.get("/ready")
    def readiness_check():
        db_ok, _ = _database_ok()
        if not db_ok:
            return JSONResponse(status_code=503, content={"status": "not_ready", "database": "unavailable"})
        return {"status": "ready", "database": "available"}
