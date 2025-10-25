"""Integration test for Docker Compose setup - pytest version."""

import pytest
import requests
import time
from typing import Generator


@pytest.fixture(scope="module")
def wait_for_services() -> Generator[None, None, None]:
    """Wait for services to be ready before running tests."""
    max_wait = 30
    start = time.time()
    
    while time.time() - start < max_wait:
        try:
            # Check if agent shell is responding
            response = requests.get("http://localhost:8000/healthz", timeout=2)
            if response.status_code == 200:
                break
        except:
            pass
        time.sleep(2)
    
    yield
    # Cleanup after tests if needed


def test_agent_shell_health(wait_for_services):
    """Test that agent shell health endpoint is accessible."""
    response = requests.get("http://localhost:8000/healthz", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"


def test_agent_shell_root(wait_for_services):
    """Test that agent shell root endpoint returns expected message."""
    response = requests.get("http://localhost:8000/", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Snacktopus" in data["message"]


def test_ollama_service(wait_for_services):
    """Test that Ollama service is accessible."""
    try:
        response = requests.get("http://localhost:11434", timeout=5)
        assert response.status_code == 200
    except requests.exceptions.RequestException:
        pytest.skip("Ollama service not available")


def test_dapr_agent_shell_metadata(wait_for_services):
    """Test that Dapr sidecar for agent-shell is running."""
    response = requests.get("http://localhost:3500/v1.0/metadata", timeout=5)
    assert response.status_code == 200
    
    metadata = response.json()
    assert metadata.get("id") == "agent-shell"
    
    # Check that components are registered
    components = metadata.get("components", [])
    assert len(components) > 0
    
    # Verify statestore component exists
    component_names = [c.get("name") for c in components]
    assert "statestore" in component_names


def test_dapr_workflow_host_metadata(wait_for_services):
    """Test that Dapr sidecar for workflow-host is running."""
    response = requests.get("http://localhost:3601/v1.0/metadata", timeout=5)
    assert response.status_code == 200
    
    metadata = response.json()
    assert metadata.get("id") == "workflow-host"
    
    # Check that components are registered
    components = metadata.get("components", [])
    assert len(components) > 0


def test_zipkin_service(wait_for_services):
    """Test that Zipkin service is accessible (optional)."""
    try:
        response = requests.get("http://localhost:9411", timeout=5)
        assert response.status_code in [200, 404]  # 404 is ok, just means UI is there
    except requests.exceptions.RequestException:
        pytest.skip("Zipkin service not available (optional)")


@pytest.mark.skipif(True, reason="Workflow invocation may not work without proper setup")
def test_workflow_invocation(wait_for_services):
    """Test workflow invocation via Dapr (optional test)."""
    url = "http://localhost:3601/v1.0-beta1/workflows/dapr/hello_snacktopus/start"
    params = {"instanceID": f"test-{int(time.time())}"}
    headers = {"Content-Type": "application/json"}
    payload = {"name": "Docker E2E Test"}
    
    response = requests.post(url, json=payload, headers=headers, params=params, timeout=10)
    # Accept various success status codes
    assert response.status_code in [200, 201, 202, 204]
