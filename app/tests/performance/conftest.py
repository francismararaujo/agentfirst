"""Performance test configuration"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="function")
def client():
    """Create test client for performance tests"""
    return TestClient(app)
