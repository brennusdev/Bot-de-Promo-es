from app.analyzer.promotion_score import promotion_score, promotion_summary


def test_promotion_score():
    score = promotion_score(150.0, 250.0)
    assert score == 4


def test_promotion_summary():
    summary = promotion_summary(150.0, 250.0)
    assert summary["score"] == 4
    assert summary["discount_percent"] == 40.0
    assert summary["label"] == "Promoção forte"
