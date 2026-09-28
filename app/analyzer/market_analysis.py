def compare_prices(history):
    """Compara o primeiro e o último preço do histórico."""
    if len(history) < 2:
        return 0.0

    first = float(history[0]["value"])
    last = float(history[-1]["value"])
    return last - first
