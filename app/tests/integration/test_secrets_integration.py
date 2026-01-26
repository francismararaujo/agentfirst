"""Integration tests for Secrets Manager - Test multiple secret types working together"""

import pytest
from unittest.mock import MagicMock, patch

from app.core.secrets_manager import SecretsManager
from app.core.secrets_provider import SecretsProvider
from app.core.secrets_config import (
    TelegramSecret,
    iFoodSecret,
    BedrockSecret,
    DatabaseSecret,
    SECRET_NAMES,
)


@pytest.mark.integration
class TestSecretsProviderIntegration:
    """Integration tests for SecretsProvider with multiple secret types"""

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

    def test_retrieve_all_secrets(self, provider, mock_secrets_manager):
        """Test retrieving all secret types in sequence"""
        # Setup mock responses
        telegram_data = {
            "bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            "webhook_url": "https://example.com/webhook"
        }
        ifood_data = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "auth_url": "https://auth.ifood.com.br/oauth/authorize",
            "token_url": "https://auth.ifood.com.br/oauth/token",
            "api_url": "https://merchant-api.ifood.com.br"
        }
        bedrock_data = {
            "region": "us-east-1",
            "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0"
        }
        database_data = {
            "host": "localhost",
            "port": 5432,
            "username": "admin",
            "password": "password123",
            "database": "agentfirst"
        }
        
        # Configure mock to return different data based on secret name
        def get_secret_side_effect(secret_name):
            if secret_name == SECRET_NAMES["telegram"]:
                return telegram_data
            elif secret_name == SECRET_NAMES["ifood"]:
                return ifood_data
            elif secret_name == SECRET_NAMES["bedrock"]:
                return bedrock_data
            elif secret_name == SECRET_NAMES["database"]:
                return database_data
            return None
        
        mock_secrets_manager.get_secret.side_effect = get_secret_side_effect
        
        # Retrieve all secrets
        telegram = provider.get_telegram_secret()
        ifood = provider.get_ifood_secret()
        bedrock = provider.get_bedrock_secret()
        database = provider.get_database_secret()
        
        # Verify all secrets were retrieved correctly
        assert isinstance(telegram, TelegramSecret)
        assert telegram.bot_token == telegram_data["bot_token"]
        
        assert isinstance(ifood, iFoodSecret)
        assert ifood.client_id == ifood_data["client_id"]
        
        assert isinstance(bedrock, BedrockSecret)
        assert bedrock.region == bedrock_data["region"]
        
        assert isinstance(database, DatabaseSecret)
        assert database.host == database_data["host"]


@pytest.mark.integration
class TestSecretsManagerCaching:
    """Integration tests for SecretsManager caching behavior"""

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

    def test_cache_multiple_secrets(self, secrets_manager, mock_client):
        """Test caching behavior with multiple secrets"""
        import json
        
        secret1_data = {"bot_token": "token1"}
        secret2_data = {"client_id": "id2"}
        
        mock_client.get_secret_value.side_effect = [
            {"SecretString": json.dumps(secret1_data)},
            {"SecretString": json.dumps(secret2_data)},
        ]
        
        # Retrieve first secret
        result1 = secrets_manager.get_secret("secret1")
        assert result1 == secret1_data
        
        # Retrieve second secret
        result2 = secrets_manager.get_secret("secret2")
        assert result2 == secret2_data
        
        # Verify both are cached
        assert len(secrets_manager._cache) == 2
        
        # Retrieve first secret again (should use cache)
        result1_cached = secrets_manager.get_secret("secret1")
        assert result1_cached == secret1_data
        
        # Should only have called client twice (not three times)
        assert mock_client.get_secret_value.call_count == 2

    def test_clear_specific_cache_preserves_others(self, secrets_manager, mock_client):
        """Test that clearing one cached secret preserves others"""
        import json
        
        secret1_data = {"bot_token": "token1"}
        secret2_data = {"client_id": "id2"}
        
        mock_client.get_secret_value.side_effect = [
            {"SecretString": json.dumps(secret1_data)},
            {"SecretString": json.dumps(secret2_data)},
        ]
        
        # Retrieve both secrets
        secrets_manager.get_secret("secret1")
        secrets_manager.get_secret("secret2")
        
        # Clear only first secret
        secrets_manager.clear_cache("secret1")
        
        # Verify first is cleared but second is still cached
        assert "secret1" not in secrets_manager._cache
        assert "secret2" in secrets_manager._cache
