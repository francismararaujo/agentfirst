"""AWS CDK Stack for Secrets Manager"""

from aws_cdk import (
    Stack,
    aws_secretsmanager as secretsmanager,
    aws_kms as kms,
    Duration,
)
from constructs import Construct


class SecretsStack(Stack):
    """Stack for managing secrets in AWS Secrets Manager"""

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create KMS key for encrypting secrets
        secrets_key = kms.Key(
            self,
            "SecretsKey",
            enable_key_rotation=True,
            removal_policy=None,  # Keep key on stack deletion
            description="KMS key for encrypting secrets in Secrets Manager",
        )

        # Telegram Bot Token Secret
        telegram_secret = secretsmanager.Secret(
            self,
            "TelegramSecret",
            secret_name="agentfirst/telegram",
            description="Telegram Bot Token and webhook configuration",
            encryption_key=secrets_key,
            removal_policy=None,  # Keep secret on stack deletion
        )

        # iFood OAuth Credentials Secret
        ifood_secret = secretsmanager.Secret(
            self,
            "iFoodSecret",
            secret_name="agentfirst/ifood",
            description="iFood OAuth 2.0 credentials and API endpoints",
            encryption_key=secrets_key,
            removal_policy=None,  # Keep secret on stack deletion
        )

        # Bedrock API Configuration Secret
        bedrock_secret = secretsmanager.Secret(
            self,
            "BedrockSecret",
            secret_name="agentfirst/bedrock",
            description="Bedrock API configuration (region, model ID)",
            encryption_key=secrets_key,
            removal_policy=None,  # Keep secret on stack deletion
        )

        # Database Credentials Secret
        database_secret = secretsmanager.Secret(
            self,
            "DatabaseSecret",
            secret_name="agentfirst/database",
            description="Database connection credentials",
            encryption_key=secrets_key,
            removal_policy=None,  # Keep secret on stack deletion
        )

        # Store references for later use
        self.telegram_secret = telegram_secret
        self.ifood_secret = ifood_secret
        self.bedrock_secret = bedrock_secret
        self.database_secret = database_secret
        self.secrets_key = secrets_key
