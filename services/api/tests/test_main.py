import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from app import main as main_module

app = main_module.app
client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ping():
    r = client.get("/ping")
    assert r.status_code == 200
    assert r.json()["ping"] == "pong"


def test_info():
    r = client.get("/info")
    assert r.status_code == 200
    assert r.json()["app"] == "AcaciaFund API"


def test_set_progress():
    r = client.post("/progress", json={"url": "/test-article", "score": 75, "done": True})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_get_progress():
    client.post("/progress", json={"url": "/test-get", "score": 50, "done": False})
    r = client.get("/progress", params={"url": "/test-get"})
    assert r.status_code == 200
    assert r.json()["result"]["url"] == "/test-get"
    assert r.json()["result"]["score"] == 50
