def calculate_promotion(current_price, original_price):
    """Calcula a porcentagem de desconto."""
    if original_price <= 0:
        return 0.0
    return ((original_price - current_price) / original_price) * 100
