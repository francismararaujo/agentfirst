"""AWS Secrets Manager integration for secure credential storage"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SecretsManager:
    """Manages secrets stored in AWS Secrets Manager with caching and rotation support"""

    def __init__(self, region_name: str = "us-east-1"):
        """Initialize Secrets Manager client
        
        Args:
            region_name: AWS region for Secrets Manager
        """
        self.client = boto3.client("secretsmanager", region_name=region_name)
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self._cache_ttl = timedelta(hours=1)

    def get_secret(self, secret_name: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Retrieve secret from Secrets Manager
        
        Args:
            secret_name: Name of the secret
            use_cache: Whether to use cached value if available
            
        Returns:
            Secret value as dictionary, or None if not found
        """
        # Check cache
        if use_cache and secret_name in self._cache:
            value, timestamp = self._cache[secret_name]
            if datetime.utcnow() - timestamp < self._cache_ttl:
                logger.debug(f"Retrieved {secret_name} from cache")
                return value

        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            
            # Parse secret value
            if "SecretString" in response:
                secret_value = json.loads(response["SecretString"])
            else:
                secret_value = response["SecretBinary"]
            
            # Cache the value
            self._cache[secret_name] = (secret_value, datetime.utcnow())
            logger.info(f"Retrieved secret: {secret_name}")
            return secret_value
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.warning(f"Secret not found: {secret_name}")
                return None
            elif e.response["Error"]["Code"] == "InvalidRequestException":
                logger.error(f"Invalid request for secret: {secret_name}")
                return None
            elif e.response["Error"]["Code"] == "InvalidParameterException":
                logger.error(f"Invalid parameter for secret: {secret_name}")
                return None
            else:
                logger.error(f"Error retrieving secret {secret_name}: {str(e)}")
                raise

    def create_secret(
        self,
        secret_name: str,
        secret_value: Dict[str, Any],
        description: str = "",
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        """Create a new secret in Secrets Manager
        
        Args:
            secret_name: Name of the secret
            secret_value: Secret value as dictionary
            description: Description of the secret
            tags: Tags to apply to the secret
            
        Returns:
            ARN of the created secret
        """
        try:
            response = self.client.create_secret(
                Name=secret_name,
                Description=description,
                SecretString=json.dumps(secret_value),
                Tags=[{"Key": k, "Value": v} for k, v in (tags or {}).items()],
            )
            logger.info(f"Created secret: {secret_name}")
            return response["ARN"]
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceExistsException":
                logger.warning(f"Secret already exists: {secret_name}")
                return ""
            else:
                logger.error(f"Error creating secret {secret_name}: {str(e)}")
                raise

    def update_secret(
        self,
        secret_name: str,
        secret_value: Dict[str, Any],
    ) -> str:
        """Update an existing secret
        
        Args:
            secret_name: Name of the secret
            secret_value: New secret value as dictionary
            
        Returns:
            ARN of the updated secret
        """
        try:
            response = self.client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(secret_value),
            )
            # Invalidate cache
            if secret_name in self._cache:
                del self._cache[secret_name]
            logger.info(f"Updated secret: {secret_name}")
            return response["ARN"]
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.warning(f"Secret not found: {secret_name}")
                return ""
            else:
                logger.error(f"Error updating secret {secret_name}: {str(e)}")
                raise

    def delete_secret(
        self,
        secret_name: str,
        recovery_window_in_days: int = 7,
    ) -> str:
        """Delete a secret (with recovery window)
        
        Args:
            secret_name: Name of the secret
            recovery_window_in_days: Days before permanent deletion (7-30)
            
        Returns:
            ARN of the deleted secret
        """
        try:
            response = self.client.delete_secret(
                SecretId=secret_name,
                RecoveryWindowInDays=recovery_window_in_days,
            )
            # Invalidate cache
            if secret_name in self._cache:
                del self._cache[secret_name]
            logger.info(f"Deleted secret: {secret_name}")
            return response["ARN"]
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.warning(f"Secret not found: {secret_name}")
                return ""
            else:
                logger.error(f"Error deleting secret {secret_name}: {str(e)}")
                raise

    def rotate_secret(
        self,
        secret_name: str,
        rotation_lambda_arn: str,
        rotation_rules: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Enable automatic rotation for a secret
        
        Args:
            secret_name: Name of the secret
            rotation_lambda_arn: ARN of Lambda function for rotation
            rotation_rules: Rotation rules (e.g., {"AutomaticallyAfterDays": 30})
            
        Returns:
            ARN of the secret
        """
        try:
            rules = rotation_rules or {"AutomaticallyAfterDays": 30}
            response = self.client.rotate_secret(
                SecretId=secret_name,
                RotationLambdaARN=rotation_lambda_arn,
                RotationRules=rules,
            )
            logger.info(f"Enabled rotation for secret: {secret_name}")
            return response["ARN"]
        except ClientError as e:
            logger.error(f"Error rotating secret {secret_name}: {str(e)}")
            raise

    def clear_cache(self, secret_name: Optional[str] = None) -> None:
        """Clear cache for a specific secret or all secrets
        
        Args:
            secret_name: Name of the secret to clear, or None to clear all
        """
        if secret_name:
            if secret_name in self._cache:
                del self._cache[secret_name]
                logger.debug(f"Cleared cache for secret: {secret_name}")
        else:
            self._cache.clear()
            logger.debug("Cleared all cached secrets")
