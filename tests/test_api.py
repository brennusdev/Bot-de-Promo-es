"""Testes de API HTTP com TestClient (banco em arquivo temporário).

ESTUDO: os testes anteriores cobriam apenas serviços e schemas — nenhuma
rota HTTP era exercitada. Com TestClient validamos status codes e payloads.
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


def test_categories_endpoint(client, monkeypatch):
    """Categorias aparecem com contagem após cadastrar produtos."""
    from unittest.mock import patch

    fake_data = {
        "name": "Notebook Dell Inspiron 15 8GB",
        "price": 2500.0,
        "url": "https://www.mercadolivre.com.br/notebook-dell",
        "store": "Mercado Livre",
        "market": "mercado_livre",
        "specifications": {},
        "reference_price": 2500.0,
        "promotion_score": 0,
    }
    with patch("app.main.get_product_data_for_url", return_value=fake_data):
        client.post("/products", json={"url": "https://www.mercadolivre.com.br/notebook-dell"})

    resp = client.get("/categories")
    assert resp.status_code == 200
    cats = resp.json()["categories"]
    assert cats.get("notebook") == 1

    # Filtro por categoria no /products
    resp2 = client.get("/products?category=notebook")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1
    resp3 = client.get("/products?category=monitor")
    assert resp3.json() == []


def test_delete_product(client, monkeypatch):
    """DELETE remove produto (e 404 em id inexistente)."""
    from unittest.mock import patch

    fake_data = {
        "name": "Fone JBL Tune 510BT",
        "price": 299.0,
        "url": "https://www.pichau.com.br/fone-jbl",
        "store": "Pichau",
        "market": "pichau",
        "specifications": {},
        "reference_price": 299.0,
        "promotion_score": 0,
    }
    url = "https://www.pichau.com.br/fone-jbl"
    with patch("app.main.get_product_data_for_url", return_value=fake_data):
        created = client.post("/products", json={"url": url}).json()

    product_id = created["product"]["id"]

    resp = client.delete(f"/products/{product_id}")
    assert resp.status_code == 204

    # Produto sumiu da listagem
    resp2 = client.get("/products")
    assert resp2.json() == []

    # Remover de novo dá 404
    resp3 = client.delete(f"/products/{product_id}")
    assert resp3.status_code == 404


def test_delete_product_cascade(client, monkeypatch):
    """Remover produto apaga também preços e alertas vinculados."""
    from unittest.mock import patch

    from app.database.connection import get_connection
    from app.services.price_service import save_price

    fake_data = {
        "name": "Monitor AOC 24",
        "price": 700.0,
        "url": "https://www.kabum.com.br/monitor-aoc-2",
        "store": "KaBuM",
        "market": "kabum",
        "specifications": {},
        "reference_price": 700.0,
        "promotion_score": 0,
    }
    with patch("app.main.get_product_data_for_url", return_value=fake_data):
        created = client.post("/products", json={"url": fake_data["url"]}).json()
    product_id = created["product"]["id"]

    save_price(product_id, 700.0)
    user = client.post("/users", json={"name": "Ana", "phone": "11988776655"}).json()
    client.post(f"/users/{user['id']}/alerts", json={"product_id": product_id, "threshold_percent": 10})

    resp = client.delete(f"/products/{product_id}")
    assert resp.status_code == 204

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM prices WHERE product_id = ?", (product_id,))
    assert cursor.fetchone()[0] == 0
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE product_id = ?", (product_id,))
    assert cursor.fetchone()[0] == 0
    conn.close()


def test_offers_new_endpoint(client, monkeypatch):
    """Endpoint do popup: detecta produtos novos desde um id."""
    from unittest.mock import patch

    fake_data = {
        "name": "Monitor AOC 24 75Hz",
        "price": 700.0,
        "url": "https://www.kabum.com.br/monitor-aoc",
        "store": "KaBuM",
        "market": "kabum",
        "specifications": {},
        "reference_price": 700.0,
        "promotion_score": 0,
    }
    with patch("app.main.get_product_data_for_url", return_value=fake_data):
        client.post("/products", json={"url": "https://www.kabum.com.br/monitor-aoc"})

    resp = client.get("/offers/new?since_id=0")
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_new"] is True
    latest = body["latest_id"]
    assert body["offers"][0]["category"] == "monitor"

    # Sem produtos novos desde o último id visto
    resp2 = client.get(f"/offers/new?since_id={latest}")
    assert resp2.json()["has_new"] is False
