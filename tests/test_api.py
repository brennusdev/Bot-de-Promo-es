"""Testes de API HTTP com TestClient (banco em arquivo temporário).

ESTUDO: os testes anteriores cobriam apenas serviços e schemas — nenhuma
rota HTTP era exercitada. Com TestClient validamos status codes, payloads
e o comportamento do webhook de ponta a ponta.
"""
import importlib
import os
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Isola cada teste em um banco SQLite temporário próprio."""
    db_file = tmp_path / "test_api.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))

    # Recarrega os módulos para que settings/connection peguem o novo DATABASE_PATH
    import app.config.settings as settings
    importlib.reload(settings)

    import app.database.connection as connection
    importlib.reload(connection)

    from app.database.connection import init_db
    init_db()

    from app.api import app
    with TestClient(app) as test_client:
        yield test_client


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Bot de Promoções" in resp.json()["message"]


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"]["ok"] is True


def test_ready_ok(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_create_and_list_users(client):
    resp = client.post("/users", json={"name": "Ana", "phone": "(11) 98888-7777"})
    assert resp.status_code == 201
    user = resp.json()
    assert user["phone"] == "11988887777"

    # Criação duplicada retorna o mesmo usuário (idempotente por phone)
    resp2 = client.post("/users", json={"name": "Ana", "phone": "11988887777"})
    assert resp2.status_code == 201
    assert resp2.json()["id"] == user["id"]

    resp3 = client.get("/users")
    assert resp3.status_code == 200
    assert len(resp3.json()) == 1


def test_user_phone_required(client):
    resp = client.post("/users", json={"name": "Sem telefone", "phone": ""})
    assert resp.status_code in (400, 422)


def test_create_alert(client):
    user = client.post("/users", json={"name": "Bob", "phone": "11999990000"}).json()
    resp = client.post(
        f"/users/{user['id']}/alerts",
        json={"product_id": 1, "threshold_percent": 15.0},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["threshold_percent"] == 15.0
    assert body["active"] is True

    # Lista alertas do usuário
    resp2 = client.get(f"/users/{user['id']}/alerts")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1


def test_products_endpoint_empty(client):
    resp = client.get("/products")
    assert resp.status_code == 200
    assert resp.json() == []


def test_webhook_verify_rejects_bad_token(client):
    resp = client.get("/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=errado&hub.challenge=123")
    assert resp.status_code == 403


def test_webhook_verify_accepts_good_token(client, monkeypatch):
    import app.api as api
    import app.services.whatsapp_service as wa

    monkeypatch.setattr(wa, "WHATSAPP_WEBHOOK_VERIFY_TOKEN", "meu_token")
    resp = client.get("/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=meu_token&hub.challenge=abc123")
    assert resp.status_code == 200
    assert resp.json() == "abc123"


def test_webhook_post_rejects_garbage_json(client):
    resp = client.post("/webhooks/whatsapp", content=b"not json", headers={"content-type": "application/json"})
    assert resp.status_code == 400
