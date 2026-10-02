"""ESTUDO: testes dos schemas Pydantic (app/schemas.py) e da assinatura HMAC.

Objetivo didático:
- Schemas rejeitam payloads inválidos com 422 (validação declarativa).
- Assinatura do webhook: só a assinatura correta da Meta passa.
"""
import hmac
import hashlib
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import app.services.whatsapp_service as wa
from app.schemas import AlertCreate, UserCreate


# ---------- Schemas ----------

def test_user_create_requires_phone():
    """phone é obrigatório: sem ele, a validação falha (na API viraria 422)."""
    with pytest.raises(Exception):
        UserCreate()


def test_user_create_accepts_name_optional():
    """name é opcional; phone preenchido valida normalmente."""
    user = UserCreate(phone="11999999999")
    assert user.name is None
    assert user.phone == "11999999999"


def test_alert_create_defaults_threshold():
    """threshold_percent tem default 10.0 quando não enviado."""
    alert = AlertCreate(product_id=1)
    assert alert.threshold_percent == 10.0


def test_alert_create_rejects_zero_threshold():
    """threshold_percent <= 0 é inválido (gt=0 no Field)."""
    with pytest.raises(Exception):
        AlertCreate(product_id=1, threshold_percent=0)


# ---------- Assinatura HMAC do webhook ----------

SECRET = "meu-app-secret"
BODY = b'{"entry": []}'
VALID_SIG = "sha256=" + hmac.new(SECRET.encode(), BODY, hashlib.sha256).hexdigest()


def _patch_secret(monkeypatch, secret):
    """Substitui o secret do módulo sem recarregar settings (testes isolados)."""
    monkeypatch.setattr(wa, "WHATSAPP_APP_SECRET", secret)
    monkeypatch.setattr(wa, "IS_PRODUCTION", False)


def test_signature_valid(monkeypatch):
    """Assinatura correta da Meta passa."""
    _patch_secret(monkeypatch, SECRET)
    assert wa.verify_webhook_signature(BODY, VALID_SIG) is True


def test_signature_invalid_rejected(monkeypatch):
    """Assinatura forjada/errada é rejeitada."""
    _patch_secret(monkeypatch, SECRET)
    assert wa.verify_webhook_signature(BODY, "sha256=deadbeef") is False


def test_signature_missing_rejected(monkeypatch):
    """Sem header de assinatura: rejeita quando há secret configurado."""
    _patch_secret(monkeypatch, SECRET)
    assert wa.verify_webhook_signature(BODY, "") is False


def test_signature_dev_without_secret_allows(monkeypatch):
    """Desenvolvimento sem secret: webhook aberto (comportamento dev-friendly)."""
    _patch_secret(monkeypatch, "")
    assert wa.verify_webhook_signature(BODY, "") is True


def test_signature_production_without_secret_fails_closed(monkeypatch):
    """Produção SEM secret: fail-closed (rejeita sempre) — evita webhook aberto."""
    monkeypatch.setattr(wa, "WHATSAPP_APP_SECRET", "")
    monkeypatch.setattr(wa, "IS_PRODUCTION", True)
    assert wa.verify_webhook_signature(BODY, VALID_SIG) is False
