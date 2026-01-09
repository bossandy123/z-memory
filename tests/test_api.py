import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "features" in data

def test_get_config():
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "user_memory_enabled" in data
    assert "agent_memory_enabled" in data

@pytest.mark.skipif(not settings.ENABLE_USER_MEMORY, reason="User memory not enabled")
def test_store_user_memory():
    response = client.post(
        "/memory/user/test_user",
        json={
            "content": "Test user memory",
            "metadata": {"source": "test"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "success"

@pytest.mark.skipif(not settings.ENABLE_AGENT_MEMORY, reason="Agent memory not enabled")
def test_store_agent_memory():
    response = client.post(
        "/memory/agent/test_agent",
        json={
            "content": "Test agent memory",
            "metadata": {"source": "test"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "success"

def test_query_memory_without_ids():
    response = client.post(
        "/memory/query",
        json={
            "query": "test query"
        }
    )
    assert response.status_code == 400

@pytest.mark.skipif(not settings.ENABLE_USER_MEMORY, reason="User memory not enabled")
def test_query_user_memory():
    response = client.post(
        "/memory/query",
        json={
            "query": "test query",
            "user_id": "test_user",
            "top_k": 5
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data

def test_query_disabled_memory():
    if not settings.ENABLE_USER_MEMORY:
        response = client.post(
            "/memory/query",
            json={
                "query": "test query",
                "user_id": "test_user",
                "top_k": 5
            }
        )
        assert response.status_code == 400

    if not settings.ENABLE_AGENT_MEMORY:
        response = client.post(
            "/memory/query",
            json={
                "query": "test query",
                "agent_id": "test_agent",
                "top_k": 5
            }
        )
        assert response.status_code == 400
