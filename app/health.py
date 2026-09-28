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


def register_health_checks(app: FastAPI) -> None:
    """Registra endpoints de saúde para monitoramento."""

    @app.get("/health")
    def health_check():
        db_ok, db_detail = _database_ok()
        redis_ok, redis_detail = _redis_ok()

        if not db_ok or not redis_ok:
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
