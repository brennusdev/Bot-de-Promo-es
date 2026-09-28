import logging
from logging.config import dictConfig
from pathlib import Path


def configure_logging() -> None:
    """Configura logging global do projeto com console e arquivo rotativo."""
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "INFO",
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": str(log_dir / "pricebot.log"),
                "when": "midnight",
                "interval": 1,
                "backupCount": 7,
                "formatter": "default",
                "level": "INFO",
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file"],
        },
    })


logger = logging.getLogger("pricebot")
configure_logging()
