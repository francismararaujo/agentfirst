"""Configuration for secrets stored in AWS Secrets Manager"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TelegramSecret:
    """Telegram Bot credentials"""
    bot_token: str
    webhook_url: Optional[str] = None
    
    def to_dict(self):
        return {
            "bot_token": self.bot_token,
            "webhook_url": self.webhook_url,
        }


@dataclass
class iFoodSecret:
    """iFood OAuth credentials"""
    client_id: str
    client_secret: str
    auth_url: str = "https://auth.ifood.com.br/oauth/authorize"
    token_url: str = "https://auth.ifood.com.br/oauth/token"
    api_url: str = "https://merchant-api.ifood.com.br"
    
    def to_dict(self):
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "auth_url": self.auth_url,
            "token_url": self.token_url,
            "api_url": self.api_url,
        }


@dataclass
class BedrockSecret:
    """Bedrock API credentials"""
    region: str = "us-east-1"
    model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    def to_dict(self):
        return {
            "region": self.region,
            "model_id": self.model_id,
        }


@dataclass
class DatabaseSecret:
    """Database credentials (for future use)"""
    host: str
    port: int
    username: str
    password: str
    database: str
    
    def to_dict(self):
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "database": self.database,
        }


# Secret names in AWS Secrets Manager
SECRET_NAMES = {
    "telegram": "agentfirst/telegram",
    "ifood": "agentfirst/ifood",
    "bedrock": "agentfirst/bedrock",
    "database": "agentfirst/database",
}

# Rotation policies
ROTATION_POLICIES = {
    "telegram": {
        "AutomaticallyAfterDays": 90,  # Rotate every 90 days
    },
    "ifood": {
        "AutomaticallyAfterDays": 30,  # Rotate every 30 days
    },
    "bedrock": {
        "AutomaticallyAfterDays": 90,  # Rotate every 90 days
    },
    "database": {
        "AutomaticallyAfterDays": 30,  # Rotate every 30 days
    },
}

# Tags for secrets
SECRET_TAGS = {
    "telegram": {
        "Environment": "production",
        "Service": "omnichannel",
        "Component": "telegram-adapter",
    },
    "ifood": {
        "Environment": "production",
        "Service": "retail",
        "Component": "ifood-connector",
    },
    "bedrock": {
        "Environment": "production",
        "Service": "core",
        "Component": "brain",
    },
    "database": {
        "Environment": "production",
        "Service": "core",
        "Component": "database",
    },
}
