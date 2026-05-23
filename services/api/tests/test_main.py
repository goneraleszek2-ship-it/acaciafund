import pytest

# If FastAPI isn't installed in this environment, skip these tests gracefully.
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from app.main import main as main_module
app = main_module.app


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
