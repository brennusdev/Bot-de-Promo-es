import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.services.price_service import get_price_history


def plot_product_history(product_id):
    """Gera um gráfico com o histórico de preços de um produto."""
    history = get_price_history(product_id)

    if not history:
        return None

    dates = [item["collected_at"] for item in history]
    values = [float(item["value"]) for item in history]

    plt.figure(figsize=(10, 5))
    plt.plot(dates, values, marker="o", linestyle="-", color="green")
    plt.title("Histórico de preços")
    plt.xlabel("Data")
    plt.ylabel("Preço (R$)")
    plt.grid(True)
    plt.tight_layout()

    return plt
