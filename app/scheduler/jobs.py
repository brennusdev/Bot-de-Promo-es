from datetime import datetime

from app.database.connection import init_db
from app.main import process_product


def check_prices_periodically(urls):
    """Executa a rotina de coleta em lote para vários links."""
    init_db()

    for url in urls:
        try:
            result = process_product(url)
            print(f"[{datetime.utcnow()}] Produto atualizado: {result['product']['name']}")
        except Exception as exc:
            print(f"Erro ao processar {url}: {exc}")
