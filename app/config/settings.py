import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
APP_ENV = os.getenv("APP_ENV", "development").lower()
IS_PRODUCTION = APP_ENV == "production"

DB_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "price_bot.db")))
DATABASE_URL = os.getenv("DATABASE_URL", "") or os.getenv("POSTGRES_URL", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")

CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
API_PORT = int(os.getenv("API_PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

if IS_PRODUCTION and not DATABASE_URL:
    raise RuntimeError("DATABASE_URL é obrigatória em produção.")
