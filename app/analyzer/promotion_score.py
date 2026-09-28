def promotion_score(current_price, original_price):
    """Gera um score baseado no percentual de desconto."""
    if original_price <= 0:
        return 0

    discount = ((original_price - current_price) / original_price) * 100
    if discount >= 30:
        return 4
    if discount >= 20:
        return 3
    if discount >= 10:
        return 2
    if discount >= 5:
        return 1
    return 0


def promotion_summary(current_price, reference_price):
    """Resumo textual da promoção em relação ao preço de referência."""
    if reference_price is None or reference_price <= 0:
        return {
            "discount_percent": 0.0,
            "score": 0,
            "label": "Sem referência",
        }

    discount = ((reference_price - current_price) / reference_price) * 100
    score = promotion_score(current_price, reference_price)

    if discount >= 30:
        label = "Promoção forte"
    elif discount >= 20:
        label = "Boa promoção"
    elif discount >= 10:
        label = "Promoção moderada"
    elif discount >= 5:
        label = "Pequeno desconto"
    else:
        label = "Sem promoção relevante"

    return {
        "discount_percent": round(discount, 2),
        "score": score,
        "label": label,
    }
