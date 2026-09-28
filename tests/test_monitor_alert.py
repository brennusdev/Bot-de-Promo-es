from app.services.alert_service import should_alert


def test_should_alert_when_drop_is_large_enough():
    triggered, percent = should_alert(300.00, 500.00, threshold_percent=10.0)
    assert triggered is True
    assert percent == 40.0


def test_should_not_alert_when_drop_is_small():
    triggered, percent = should_alert(470.00, 500.00, threshold_percent=10.0)
    assert triggered is False
    assert percent == 6.0
