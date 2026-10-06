import logging
import os
from logging.config import dictConfig
from pathlib import Path


def configure_logging() -> None:
    """Configura logging global do projeto com console e arquivo rotativo."""
    log_dir = Path(__file__).resolve().parent.parent / "logs"

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
    }

    # File handler SÓ quando explicitamente pedido via LOG_TO_FILE=1.
    # Antes o critério era "APP_ENV != production", o que ativava escrita em
    # disco na Vercel (/var/task é somente leitura) e derrubava o import da
    # API com 500 FUNCTION_INVOCATION_FAILED. No serverless, os logs já vão
    # para o console (visible no painel da Vercel), então o padrão é desligado.
    if os.getenv("LOG_TO_FILE", "").lower() in ("1", "true", "yes"):
        log_dir.mkdir(exist_ok=True)
        handlers["file"] = {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(log_dir / "pricebot.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
            "formatter": "default",
            "level": "INFO",
        }

    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            }
        },
        "handlers": handlers,
        "root": {
            "level": "INFO",
            "handlers": list(handlers.keys()),
        },
    })


logger = logging.getLogger("pricebot")
configure_logging()
