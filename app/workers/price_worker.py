import logging
import os
import time

from app.collectors.router import get_product_data_for_url
from app.database.connection import cleanup_old_prices, init_db
from app.logging_config import configure_logging
from app.services.monitor_service import monitor_all_products

logger = logging.getLogger("pricebot.worker")

# ESTUDO (retenção): mantém 90 dias de histórico por padrão; configurável via .env.
PRICE_RETENTION_DAYS = int(os.getenv("PRICE_RETENTION_DAYS", "90"))

# ESTUDO (rate limit): e-commerces bloqueiam IP com muitas requisições seguidas.
# Pequena pausa entre produtos reduz risco de ban e de respostas truncadas.
REQUEST_DELAY_SECONDS = float(os.getenv("REQUEST_DELAY_SECONDS", "1"))


def fetch_current_price_for_url(url: str, fallback_price: float = 0.0):
    """Busca o preço atual de uma URL usando o coletor da loja correspondente."""
    try:
        data = get_product_data_for_url(url)
        return float(data.get("price") or fallback_price)
    except Exception:
        logger.warning("Falha ao obter preço da URL %s; usando fallback %s", url, fallback_price)
        return fallback_price


def run_worker(loop_seconds: int = 300):
    """Loop principal do worker de monitoramento."""
    configure_logging()
    init_db()
    logger.info("Worker iniciado (intervalo: %ss, retenção: %sdias)", loop_seconds, PRICE_RETENTION_DAYS)

    while True:
        try:
            results = monitor_all_products(
                fetch_current_price_for_url,
                delay_seconds=REQUEST_DELAY_SECONDS,
            )
            logger.info("Verificação concluída: %s itens processados", len(results))

            deleted = cleanup_old_prices(days_to_keep=PRICE_RETENTION_DAYS)
            if deleted:
                logger.info("Retenção: %s registros de preço antigos removidos", deleted)
        except Exception as exc:
            logger.exception("Erro no worker de monitoramento: %s", exc)
        time.sleep(loop_seconds)


if __name__ == "__main__":
    run_worker()
