"""Pytest configuration for unit tests"""

import pytest


@pytest.fixture(scope="session")
def unit_test_marker():
    """Marker for unit tests"""
    return "unit"
