"""Unit tests for AWS Secrets Manager - Test individual secrets manager methods in isolation"""

import pytest
import json
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

from app.core.secrets_manager import SecretsManager
from app.core.secrets_provider import SecretsProvider
from app.core.secrets_config import (
    TelegramSecret,
    iFoodSecret,
    BedrockSecret,
    DatabaseSecret,
    SECRET_NAMES,
)


# ============================================================================
# UNIT TESTS - SecretsManager
# ============================================================================

@pytest.mark.unit
class TestSecretsManager:
    """Tests for SecretsManager"""

    @pytest.fixture
    def mock_client(self):
        """Create mock Secrets Manager client"""
        return MagicMock()

    @pytest.fixture
    def secrets_manager(self, mock_client):
        """Create SecretsManager with mocked client"""
        manager = SecretsManager()
        manager.client = mock_client
        return manager

    def test_get_secret_success(self, secrets_manager, mock_client):
        """Test retrieving a secret successfully"""
        secret_data = {"bot_token": "test_token", "webhook_url": "https://example.com"}
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(secret_data)
        }
        
        result = secrets_manager.get_secret("test-secret")
        
        assert result == secret_data
        mock_client.get_secret_value.assert_called_once_with(SecretId="test-secret")

    def test_get_secret_not_found(self, secrets_manager, mock_client):
        """Test retrieving a non-existent secret"""
        error = ClientError(
            {"Error": {"Code": "ResourceNotFoundException"}},
            "GetSecretValue"
        )
        mock_client.get_secret_value.side_effect = error
        
        result = secrets_manager.get_secret("nonexistent-secret")
        
        assert result is None

    def test_get_secret_invalid_request(self, secrets_manager, mock_client):
        """Test retrieving a secret with invalid request"""
        error = ClientError(
            {"Error": {"Code": "InvalidRequestException"}},
            "GetSecretValue"
        )
        mock_client.get_secret_value.side_effect = error
        
        result = secrets_manager.get_secret("test-secret")
        
        assert result is None

    def test_get_secret_caching(self, secrets_manager, mock_client):
        """Test that secrets are cached"""
        secret_data = {"bot_token": "test_token"}
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(secret_data)
        }
        
        # First call
        result1 = secrets_manager.get_secret("test-secret")
        # Second call (should use cache)
        result2 = secrets_manager.get_secret("test-secret")
        
        assert result1 == result2
        # Should only call client once due to caching
        assert mock_client.get_secret_value.call_count == 1

    def test_get_secret_no_cache(self, secrets_manager, mock_client):
        """Test retrieving a secret without caching"""
        secret_data = {"bot_token": "test_token"}
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(secret_data)
        }
        
        result = secrets_manager.get_secret("test-secret", use_cache=False)
        
        assert result == secret_data

    def test_create_secret_success(self, secrets_manager, mock_client):
        """Test creating a secret successfully"""
        secret_data = {"bot_token": "test_token"}
        mock_client.create_secret.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret"
        }
        
        result = secrets_manager.create_secret(
            "test-secret",
            secret_data,
            description="Test secret",
            tags={"Environment": "test"}
        )
        
        assert "arn:aws:secretsmanager" in result
        mock_client.create_secret.assert_called_once()

    def test_create_secret_already_exists(self, secrets_manager, mock_client):
        """Test creating a secret that already exists"""
        error = ClientError(
            {"Error": {"Code": "ResourceExistsException"}},
            "CreateSecret"
        )
        mock_client.create_secret.side_effect = error
        
        result = secrets_manager.create_secret("test-secret", {})
        
        assert result == ""

    def test_update_secret_success(self, secrets_manager, mock_client):
        """Test updating a secret successfully"""
        secret_data = {"bot_token": "new_token"}
        mock_client.update_secret.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret"
        }
        
        # Pre-populate cache
        secrets_manager._cache["test-secret"] = ({"old": "data"}, __import__("datetime").datetime.utcnow())
        
        result = secrets_manager.update_secret("test-secret", secret_data)
        
        assert "arn:aws:secretsmanager" in result
        # Cache should be cleared
        assert "test-secret" not in secrets_manager._cache

    def test_delete_secret_success(self, secrets_manager, mock_client):
        """Test deleting a secret successfully"""
        mock_client.delete_secret.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret"
        }
        
        result = secrets_manager.delete_secret("test-secret")
        
        assert "arn:aws:secretsmanager" in result
        mock_client.delete_secret.assert_called_once()

    def test_rotate_secret_success(self, secrets_manager, mock_client):
        """Test enabling rotation for a secret"""
        mock_client.rotate_secret.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret"
        }
        
        result = secrets_manager.rotate_secret(
            "test-secret",
            "arn:aws:lambda:us-east-1:123456789:function:rotate-secret"
        )
        
        assert "arn:aws:secretsmanager" in result
        mock_client.rotate_secret.assert_called_once()

    def test_clear_cache_specific(self, secrets_manager):
        """Test clearing cache for a specific secret"""
        secrets_manager._cache["secret1"] = ("data1", __import__("datetime").datetime.utcnow())
        secrets_manager._cache["secret2"] = ("data2", __import__("datetime").datetime.utcnow())
        
        secrets_manager.clear_cache("secret1")
        
        assert "secret1" not in secrets_manager._cache
        assert "secret2" in secrets_manager._cache

    def test_clear_cache_all(self, secrets_manager):
        """Test clearing all cached secrets"""
        secrets_manager._cache["secret1"] = ("data1", __import__("datetime").datetime.utcnow())
        secrets_manager._cache["secret2"] = ("data2", __import__("datetime").datetime.utcnow())
        
        secrets_manager.clear_cache()
        
        assert len(secrets_manager._cache) == 0


# ============================================================================
# UNIT TESTS - SecretsProvider
# ============================================================================

@pytest.mark.unit
class TestSecretsProvider:
    """Tests for SecretsProvider"""

    @pytest.fixture
    def mock_secrets_manager(self):
        """Create mock SecretsManager"""
        return MagicMock()

    @pytest.fixture
    def provider(self, mock_secrets_manager):
        """Create SecretsProvider with mocked SecretsManager"""
        provider = SecretsProvider(use_secrets_manager=True)
        provider.secrets_manager = mock_secrets_manager
        return provider

    def test_get_telegram_secret_success(self, provider, mock_secrets_manager):
        """Test retrieving Telegram secret successfully"""
        secret_data = {
            "bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            "webhook_url": "https://example.com/webhook"
        }
        mock_secrets_manager.get_secret.return_value = secret_data
        
        result = provider.get_telegram_secret()
        
        assert isinstance(result, TelegramSecret)
        assert result.bot_token == secret_data["bot_token"]
        assert result.webhook_url == secret_data["webhook_url"]

    def test_get_telegram_secret_not_found(self, provider, mock_secrets_manager):
        """Test retrieving Telegram secret when not found"""
        mock_secrets_manager.get_secret.return_value = None
        
        result = provider.get_telegram_secret()
        
        assert result is None

    def test_get_ifood_secret_success(self, provider, mock_secrets_manager):
        """Test retrieving iFood secret successfully"""
        secret_data = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "auth_url": "https://auth.ifood.com.br/oauth/authorize",
            "token_url": "https://auth.ifood.com.br/oauth/token",
            "api_url": "https://merchant-api.ifood.com.br"
        }
        mock_secrets_manager.get_secret.return_value = secret_data
        
        result = provider.get_ifood_secret()
        
        assert isinstance(result, iFoodSecret)
        assert result.client_id == secret_data["client_id"]
        assert result.client_secret == secret_data["client_secret"]

    def test_get_bedrock_secret_success(self, provider, mock_secrets_manager):
        """Test retrieving Bedrock secret successfully"""
        secret_data = {
            "region": "us-east-1",
            "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0"
        }
        mock_secrets_manager.get_secret.return_value = secret_data
        
        result = provider.get_bedrock_secret()
        
        assert isinstance(result, BedrockSecret)
        assert result.region == secret_data["region"]
        assert result.model_id == secret_data["model_id"]

    def test_get_database_secret_success(self, provider, mock_secrets_manager):
        """Test retrieving database secret successfully"""
        secret_data = {
            "host": "localhost",
            "port": 5432,
            "username": "admin",
            "password": "password123",
            "database": "agentfirst"
        }
        mock_secrets_manager.get_secret.return_value = secret_data
        
        result = provider.get_database_secret()
        
        assert isinstance(result, DatabaseSecret)
        assert result.host == secret_data["host"]
        assert result.port == secret_data["port"]

    def test_provider_without_secrets_manager(self):
        """Test provider without Secrets Manager"""
        provider = SecretsProvider(use_secrets_manager=False)
        
        result = provider.get_telegram_secret()
        
        assert result is None

    def test_clear_cache(self, provider, mock_secrets_manager):
        """Test clearing cache through provider"""
        provider.clear_cache("test-secret")
        
        mock_secrets_manager.clear_cache.assert_called_once_with("test-secret")


# ============================================================================
# PROPERTY-BASED TESTS
# ============================================================================

@pytest.mark.property
class TestSecretsManagerProperties:
    """Property-based tests for SecretsManager"""

    def test_secret_data_preserved_through_json(self):
        """Validates: Secret data is preserved through JSON serialization"""
        from hypothesis import given, strategies as st
        
        @given(
            bot_token=st.text(min_size=1),
            webhook_url=st.just("https://example.com")
        )
        def check_preservation(bot_token, webhook_url):
            secret_data = {
                "bot_token": bot_token,
                "webhook_url": webhook_url
            }
            serialized = json.dumps(secret_data)
            deserialized = json.loads(serialized)
            assert deserialized == secret_data
        
        check_preservation()

    def test_telegram_secret_to_dict(self):
        """Validates: TelegramSecret converts to dictionary correctly"""
        secret = TelegramSecret(
            bot_token="test_token",
            webhook_url="https://example.com"
        )
        result = secret.to_dict()
        
        assert isinstance(result, dict)
        assert result["bot_token"] == "test_token"
        assert result["webhook_url"] == "https://example.com"

    def test_ifood_secret_to_dict(self):
        """Validates: iFoodSecret converts to dictionary correctly"""
        secret = iFoodSecret(
            client_id="test_id",
            client_secret="test_secret"
        )
        result = secret.to_dict()
        
        assert isinstance(result, dict)
        assert result["client_id"] == "test_id"
        assert result["client_secret"] == "test_secret"
