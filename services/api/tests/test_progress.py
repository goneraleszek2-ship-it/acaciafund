import pytest
from fastapi.testclient import TestClient
import tempfile
import os
from pathlib import Path

# Import the app and db
try:
    from app.main import app
    from app import db
except Exception:
    try:
        from services.api.app.main import app
        from services.api.app import db
    except Exception:
        # Fallback: load modules directly from file path
        import importlib.util
        from pathlib import Path
        
        # Import app
        app_path = Path(__file__).parent.parent / "app" / "main.py"
        spec = importlib.util.spec_from_file_location("app_main", str(app_path))
        app_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_mod)
        app = app_mod.app
        
        # Import db
        db_path = Path(__file__).parent.parent / "app" / "db.py"
        spec = importlib.util.spec_from_file_location("app_db", str(db_path))
        db_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(db_mod)
        db = db_mod

# Create test client - compatible with starlette 0.26.1
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database(tmp_path):
    """Setup a temporary database for each test"""
    test_db_path = tmp_path / "test.db"
    db.init_db(test_db_path)
    # Also trigger startup event to ensure middleware is properly set up
    from app.main import startup
    startup()
    yield
    # Cleanup happens automatically with tmp_path


def test_health_endpoint():
    """Test the health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data


def test_ping_endpoint():
    """Test the ping endpoint"""
    response = client.get("/ping")
    assert response.status_code == 200
    data = response.json()
    assert data == {"ping": "pong"}


def test_info_endpoint():
    """Test the info endpoint"""
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "debug" in data


def test_progress_store_and_retrieve():
    """Test storing and retrieving progress"""
    # Store progress
    progress_data = {
        "url": "/test/page",
        "done": True,
        "score": 85,
        "ts": 1234567890
    }
    
    response = client.post("/progress", json=progress_data)
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    
    # Retrieve progress
    response = client.get("/progress?url=/test/page")
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["url"] == "/test/page"
    assert data["result"]["done"] is True
    assert data["result"]["score"] == 85
    assert data["result"]["ts"] == 1234567890


def test_progress_store_minimal():
    """Test storing progress with minimal data"""
    progress_data = {
        "url": "/minimal"
    }
    
    response = client.post("/progress", json=progress_data)
    assert response.status_code == 200
    
    # Retrieve and check defaults
    response = client.get("/progress?url=/minimal")
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["url"] == "/minimal"
    assert data["result"]["done"] is False  # Default
    assert data["result"]["score"] == 0     # Default
    assert isinstance(data["result"]["ts"], int)  # Should be set


def test_progress_validation_url_must_start_with_slash():
    """Test that URL must start with slash"""
    progress_data = {
        "url": "invalid-url"  # Missing leading slash
    }
    
    response = client.post("/progress", json=progress_data)
    assert response.status_code == 422  # Validation error


def test_progress_validation_score_bounds():
    """Test score validation (0-100)"""
    # Test score too low
    progress_data = {
        "url": "/score-test",
        "score": -1
    }
    response = client.post("/progress", json=progress_data)
    assert response.status_code == 422
    
    # Test score too high
    progress_data["score"] = 101
    response = client.post("/progress", json=progress_data)
    assert response.status_code == 422
    
    # Test valid scores
    for score in [0, 50, 100]:
        progress_data["score"] = score
        response = client.post("/progress", json=progress_data)
        assert response.status_code == 200


def test_progress_update():
    """Test that updating progress works correctly"""
    # Initial storage
    progress_data = {
        "url": "/update-test",
        "done": False,
        "score": 30,
        "ts": 1000
    }
    client.post("/progress", json=progress_data)
    
    # Update with new values
    progress_data["done"] = True
    progress_data["score"] = 75
    progress_data["ts"] = 2000
    client.post("/progress", json=progress_data)
    
    # Retrieve and verify update
    response = client.get("/progress?url=/update-test")
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["done"] is True
    assert data["result"]["score"] == 75
    assert data["result"]["ts"] == 2000


def test_progress_nonexistent_url():
    """Test retrieving progress for non-existent URL"""
    response = client.get("/progress?url=/non-existent")
    assert response.status_code == 200
    data = response.json()
    assert data["result"] is None


def test_cors_headers():
    """Test that CORS headers are present on actual responses for cross-origin requests"""
    # Simulate a cross-origin request by setting the Origin header to an allowed origin
    response = client.get(
        "/progress?url=/nonexistent", 
        headers={"Origin": "http://localhost:1313"}
    )
    # Note: TestClient may not fully simulate CORS preflight
    # But we can check that the middleware adds CORS headers to responses
    assert response.status_code == 200
    # Check for CORS headers - the middleware should add these
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:1313"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])