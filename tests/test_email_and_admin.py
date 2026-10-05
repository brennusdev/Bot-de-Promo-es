"""Testes de notificação por e-mail e autenticação administrativa."""
from unittest.mock import patch, MagicMock

from app.services.email_service import email_enabled, send_email, build_alert_email_html
from app.services.notification_service import send_notification


def test_email_disabled_sem_config(monkeypatch):
    monkeypatch.setattr("app.services.email_service.SMTP_HOST", "")
    assert email_enabled() is False


def test_email_enabled_com_config(monkeypatch):
    monkeypatch.setattr("app.services.email_service.SMTP_HOST", "smtp.test.com")
    monkeypatch.setattr("app.services.email_service.ALERT_EMAIL_FROM", "bot@test.com")
    monkeypatch.setattr("app.services.email_service.ALERT_EMAIL_TO", ["user@test.com"])
    assert email_enabled() is True


def test_send_email_integra_smtp(monkeypatch):
    monkeypatch.setattr("app.services.email_service.SMTP_HOST", "smtp.test.com")
    monkeypatch.setattr("app.services.email_service.ALERT_EMAIL_FROM", "bot@test.com")
    monkeypatch.setattr("app.services.email_service.ALERT_EMAIL_TO", ["user@test.com"])

    with patch("app.services.email_service.smtplib.SMTP") as mock_smtp:
        instance = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=instance)
        result = send_email("Teste", "<p>corpo</p>")
        assert result is True
        instance.starttls.assert_called_once()
        instance.sendmail.assert_called_once()


def test_send_email_falha_nao_levanta(monkeypatch):
    monkeypatch.setattr("app.services.email_service.SMTP_HOST", "smtp.test.com")
    monkeypatch.setattr("app.services.email_service.ALERT_EMAIL_FROM", "bot@test.com")
    monkeypatch.setattr("app.services.email_service.ALERT_EMAIL_TO", ["user@test.com"])

    with patch("app.services.email_service.smtplib.SMTP", side_effect=ConnectionError("erro")):
        assert send_email("Teste", "<p>corpo</p>") is False  # falha é silenciosa


def test_build_alert_email_html():
    html = build_alert_email_html("Produto X", 100.0, 25.5, "https://loja.com/p")
    assert "Produto X" in html
    assert "25.5%" in html or "25,5%" in html
    assert "https://loja.com/p" in html


def test_send_notification_sem_email_config(monkeypatch):
    """Sem SMTP configurado, notificação vai só para o log."""
    monkeypatch.setattr("app.services.email_service.SMTP_HOST", "")
    result = send_notification(1, "msg", product_info={
        "product_name": "P", "current_price": 10, "drop_percent": 5, "product_url": "u",
    })
    assert result["channels"] == ["log"]
    assert result["email_sent"] is None


def test_send_notification_com_email(monkeypatch):
    monkeypatch.setattr("app.services.email_service.SMTP_HOST", "smtp.test.com")
    monkeypatch.setattr("app.services.email_service.ALERT_EMAIL_FROM", "bot@test.com")
    monkeypatch.setattr("app.services.email_service.ALERT_EMAIL_TO", ["user@test.com"])
    monkeypatch.setattr("app.services.email_service.send_email", lambda s, b: True)

    result = send_notification(1, "msg", product_info={
        "product_name": "Produto Y", "current_price": 50, "drop_percent": 12, "product_url": "u",
    })
    assert "email" in result["channels"]
    assert result["email_sent"] is True
