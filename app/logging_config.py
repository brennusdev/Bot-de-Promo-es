import logging
import os
from logging.config import dictConfig
from pathlib import Path


def configure_logging() -> None:
    """Configura logging global do projeto com console e arquivo rotativo."""
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
    }

    # File handler apenas fora de produção (serverless não permite escrita em disco).
    if os.getenv("APP_ENV", "development").lower() != "production":
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
