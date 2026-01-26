"""Smoke test configuration"""

import pytest
import os


@pytest.fixture(scope="session")
def aws_region():
    """Get AWS region from environment"""
    return os.getenv("AWS_REGION", "us-east-1")


@pytest.fixture(scope="session")
def environment():
    """Get environment from environment variable"""
    return os.getenv("ENVIRONMENT", "development")


@pytest.fixture(scope="session")
def aws_account_id():
    """Get AWS account ID from environment"""
    return os.getenv("AWS_ACCOUNT_ID", "373527788609")


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "smoke: mark test as a smoke test"
    )
