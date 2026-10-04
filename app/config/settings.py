import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
APP_ENV = os.getenv("APP_ENV", "development").lower()
IS_PRODUCTION = APP_ENV == "production"

DB_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "price_bot.db")))
DATABASE_URL = os.getenv("DATABASE_URL", "") or os.getenv("POSTGRES_URL", "")

# NOTA: Redis foi removido — nenhum código o utilizava. Se reintroduzir um
# cache, volte com REDIS_URL aqui e no docker-compose.

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")
# ESTUDO: a Meta assina cada POST do webhook com HMAC-SHA256 usando o App Secret.
# Sem verificar, qualquer pessoa pode forjar mensagens no seu webhook (spoofing).
# Em desenvolvimento o secret pode ficar vazio (verificação desativada);
# em produção, sem secret configurado, o POST é rejeitado.
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")

CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
API_PORT = int(os.getenv("API_PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

if IS_PRODUCTION and not DATABASE_URL:
    raise RuntimeError("DATABASE_URL é obrigatória em produção.")
