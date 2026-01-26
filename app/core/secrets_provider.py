"""Provider for accessing secrets from AWS Secrets Manager or environment variables"""

import logging
from typing import Optional, Dict, Any

from app.core.secrets_manager import SecretsManager
from app.core.secrets_config import (
    SECRET_NAMES,
    TelegramSecret,
    iFoodSecret,
    BedrockSecret,
    DatabaseSecret,
)

logger = logging.getLogger(__name__)


class SecretsProvider:
    """Provides access to secrets with fallback to environment variables"""

    def __init__(self, use_secrets_manager: bool = True, region_name: str = "us-east-1"):
        """Initialize secrets provider
        
        Args:
            use_secrets_manager: Whether to use AWS Secrets Manager
            region_name: AWS region for Secrets Manager
        """
        self.use_secrets_manager = use_secrets_manager
        self.secrets_manager = SecretsManager(region_name) if use_secrets_manager else None

    def get_telegram_secret(self) -> Optional[TelegramSecret]:
        """Get Telegram credentials
        
        Returns:
            TelegramSecret or None if not found
        """
        secret_data = self._get_secret(SECRET_NAMES["telegram"])
        if not secret_data:
            return None
        
        try:
            return TelegramSecret(
                bot_token=secret_data.get("bot_token"),
                webhook_url=secret_data.get("webhook_url"),
            )
        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing Telegram secret: {str(e)}")
            return None

    def get_ifood_secret(self) -> Optional[iFoodSecret]:
        """Get iFood OAuth credentials
        
        Returns:
            iFoodSecret or None if not found
        """
        secret_data = self._get_secret(SECRET_NAMES["ifood"])
        if not secret_data:
            return None
        
        try:
            return iFoodSecret(
                client_id=secret_data.get("client_id"),
                client_secret=secret_data.get("client_secret"),
                auth_url=secret_data.get("auth_url", "https://auth.ifood.com.br/oauth/authorize"),
                token_url=secret_data.get("token_url", "https://auth.ifood.com.br/oauth/token"),
                api_url=secret_data.get("api_url", "https://merchant-api.ifood.com.br"),
            )
        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing iFood secret: {str(e)}")
            return None

    def get_bedrock_secret(self) -> Optional[BedrockSecret]:
        """Get Bedrock credentials
        
        Returns:
            BedrockSecret or None if not found
        """
        secret_data = self._get_secret(SECRET_NAMES["bedrock"])
        if not secret_data:
            return None
        
        try:
            return BedrockSecret(
                region=secret_data.get("region", "us-east-1"),
                model_id=secret_data.get("model_id", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
            )
        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing Bedrock secret: {str(e)}")
            return None

    def get_database_secret(self) -> Optional[DatabaseSecret]:
        """Get database credentials
        
        Returns:
            DatabaseSecret or None if not found
        """
        secret_data = self._get_secret(SECRET_NAMES["database"])
        if not secret_data:
            return None
        
        try:
            return DatabaseSecret(
                host=secret_data.get("host"),
                port=secret_data.get("port"),
                username=secret_data.get("username"),
                password=secret_data.get("password"),
                database=secret_data.get("database"),
            )
        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing database secret: {str(e)}")
            return None

    def _get_secret(self, secret_name: str) -> Optional[Dict[str, Any]]:
        """Get secret from Secrets Manager or environment
        
        Args:
            secret_name: Name of the secret
            
        Returns:
            Secret data as dictionary or None if not found
        """
        if self.use_secrets_manager and self.secrets_manager:
            try:
                return self.secrets_manager.get_secret(secret_name)
            except Exception as e:
                logger.warning(f"Failed to get secret from Secrets Manager: {str(e)}")
                return None
        
        return None

    def clear_cache(self, secret_name: Optional[str] = None) -> None:
        """Clear cache for secrets
        
        Args:
            secret_name: Name of the secret to clear, or None to clear all
        """
        if self.secrets_manager:
            self.secrets_manager.clear_cache(secret_name)
