"""Pytest configuration and fixtures for AgentFirst2 MVP tests"""

import os
import pytest
import asyncio
from unittest.mock import AsyncMock

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"


# Event loop is managed by pytest-asyncio with strict mode
# No need to define it here - pytest-asyncio will create one per test function


@pytest.fixture
async def mock_dynamodb():
    """Mock DynamoDB client for testing"""
    mock_client = AsyncMock()
    return mock_client


@pytest.fixture
async def mock_bedrock():
    """Mock Bedrock client for testing"""
    mock_client = AsyncMock()
    return mock_client


@pytest.fixture
async def mock_sns():
    """Mock SNS client for testing"""
    mock_client = AsyncMock()
    return mock_client


@pytest.fixture
async def mock_sqs():
    """Mock SQS client for testing"""
    mock_client = AsyncMock()
    return mock_client


@pytest.fixture
async def mock_secrets_manager():
    """Mock Secrets Manager client for testing"""
    mock_client = AsyncMock()
    return mock_client


@pytest.fixture
def sample_user_email():
    """Sample user email for testing"""
    return "test@example.com"


@pytest.fixture
def sample_telegram_id():
    """Sample Telegram ID for testing"""
    return 123456789


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "tier": "free",
        "created_at": "2025-01-25T00:00:00Z",
        "channels": {
            "telegram": {
                "telegram_id": 123456789,
                "username": "testuser"
            }
        }
    }


@pytest.fixture
def sample_session_data():
    """Sample session data for testing"""
    return {
        "email": "test@example.com",
        "session_id": "sess_123456",
        "created_at": "2025-01-25T00:00:00Z",
        "expires_at": "2025-01-26T00:00:00Z",
        "context": {
            "last_domain": "retail",
            "last_intent": "check_orders",
            "last_connector": "ifood"
        }
    }


@pytest.fixture
def sample_telegram_message():
    """Sample Telegram message for testing"""
    return {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "date": 1705939200,
            "chat": {
                "id": 123456789,
                "type": "private"
            },
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test"
            },
            "text": "Quantos pedidos tenho?"
        }
    }


@pytest.fixture
def sample_ifood_order():
    """Sample iFood order for testing"""
    return {
        "id": "order_123456",
        "reference": "REF123456",
        "createdAt": "2025-01-25T10:00:00Z",
        "type": "DELIVERY",
        "status": "CONFIRMED",
        "total": 12550,
        "items": [
            {
                "id": "item_1",
                "name": "Hambúrguer",
                "quantity": 1,
                "price": 5000
            }
        ],
        "customer": {
            "id": "cust_123",
            "name": "João Silva",
            "phone": "11999999999"
        },
        "delivery": {
            "address": "Rua A, 123",
            "estimatedTime": 30
        }
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "property: mark test as a property-based test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

