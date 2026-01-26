"""Pytest configuration for end-to-end tests"""

import pytest


@pytest.fixture(scope="session")
def e2e_test_marker():
    """Marker for end-to-end tests"""
    return "e2e"
