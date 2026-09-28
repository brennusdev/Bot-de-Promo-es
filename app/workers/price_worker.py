import logging
import time

from app.config.settings import REDIS_URL
from app.logging_config import configure_logging
from app.services.monitor_service import monitor_all_products
from app.services.product_service import list_products

logger = logging.getLogger("pricebot.worker")


def fetch_current_price_for_url(url: str, fallback_price: float = 0.0):
    """Busca o preço atual de uma URL. Implementação simples para manter o worker robusto."""
    try:
        import requests

        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return float(response.text or fallback_price)
    except Exception:
        logger.warning("Falha ao obter preço da URL %s; usando fallback 0.0", url)
        return fallback_price


def run_worker(loop_seconds: int = 300):
    """Loop principal do worker de monitoramento."""
    configure_logging()
    logger.info("Worker iniciado com Redis %s", REDIS_URL)

    while True:
        try:
            products = list_products()
            logger.info("Processando %s produtos", len(products))
            results = monitor_all_products(fetch_current_price_for_url)
            logger.info("Verificação concluída: %s itens processados", len(results))
        except Exception as exc:
            logger.exception("Erro no worker de monitoramento: %s", exc)
        time.sleep(loop_seconds)


if __name__ == "__main__":
    run_worker()
