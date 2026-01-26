"""Performance tests for Secrets Manager - Test latency and caching efficiency"""

import pytest
import json
import time
from unittest.mock import MagicMock, patch

from app.core.secrets_manager import SecretsManager
from app.core.secrets_provider import SecretsProvider


@pytest.mark.performance
class TestSecretsManagerPerformance:
    """Performance tests for SecretsManager"""

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

    def test_get_secret_latency(self, secrets_manager, mock_client):
        """Test that getting a secret completes within SLA (< 50ms)"""
        secret_data = {"bot_token": "test_token"}
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(secret_data)
        }
        
        start = time.time()
        result = secrets_manager.get_secret("test-secret")
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        assert result == secret_data
        # Should complete in less than 50ms
        assert elapsed < 50, f"Get secret took {elapsed}ms, expected < 50ms"

    def test_cached_secret_latency(self, secrets_manager, mock_client):
        """Test that cached secret retrieval is very fast (< 5ms)"""
        secret_data = {"bot_token": "test_token"}
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(secret_data)
        }
        
        # First call (not cached)
        secrets_manager.get_secret("test-secret")
        
        # Second call (cached)
        start = time.time()
        result = secrets_manager.get_secret("test-secret")
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        assert result == secret_data
        # Cached retrieval should be very fast (< 5ms)
        assert elapsed < 5, f"Cached get secret took {elapsed}ms, expected < 5ms"

    def test_cache_efficiency(self, secrets_manager, mock_client):
        """Test that caching reduces API calls"""
        secret_data = {"bot_token": "test_token"}
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(secret_data)
        }
        
        # Make 10 calls
        for _ in range(10):
            secrets_manager.get_secret("test-secret")
        
        # Should only call API once due to caching
        assert mock_client.get_secret_value.call_count == 1

    def test_create_secret_latency(self, secrets_manager, mock_client):
        """Test that creating a secret completes within SLA (< 100ms)"""
        secret_data = {"bot_token": "test_token"}
        mock_client.create_secret.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret"
        }
        
        start = time.time()
        result = secrets_manager.create_secret("test-secret", secret_data)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        assert "arn:aws:secretsmanager" in result
        # Should complete in less than 100ms
        assert elapsed < 100, f"Create secret took {elapsed}ms, expected < 100ms"

    def test_update_secret_latency(self, secrets_manager, mock_client):
        """Test that updating a secret completes within SLA (< 100ms)"""
        secret_data = {"bot_token": "new_token"}
        mock_client.update_secret.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret"
        }
        
        start = time.time()
        result = secrets_manager.update_secret("test-secret", secret_data)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        assert "arn:aws:secretsmanager" in result
        # Should complete in less than 100ms
        assert elapsed < 100, f"Update secret took {elapsed}ms, expected < 100ms"


@pytest.mark.performance
class TestSecretsProviderPerformance:
    """Performance tests for SecretsProvider"""

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

    def test_get_telegram_secret_latency(self, provider, mock_secrets_manager):
        """Test that getting Telegram secret completes within SLA (< 50ms)"""
        secret_data = {
            "bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            "webhook_url": "https://example.com/webhook"
        }
        mock_secrets_manager.get_secret.return_value = secret_data
        
        start = time.time()
        result = provider.get_telegram_secret()
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        assert result is not None
        # Should complete in less than 50ms
        assert elapsed < 50, f"Get Telegram secret took {elapsed}ms, expected < 50ms"

    def test_get_ifood_secret_latency(self, provider, mock_secrets_manager):
        """Test that getting iFood secret completes within SLA (< 50ms)"""
        secret_data = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "auth_url": "https://auth.ifood.com.br/oauth/authorize",
            "token_url": "https://auth.ifood.com.br/oauth/token",
            "api_url": "https://merchant-api.ifood.com.br"
        }
        mock_secrets_manager.get_secret.return_value = secret_data
        
        start = time.time()
        result = provider.get_ifood_secret()
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        assert result is not None
        # Should complete in less than 50ms
        assert elapsed < 50, f"Get iFood secret took {elapsed}ms, expected < 50ms"
