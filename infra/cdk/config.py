"""CDK Configuration for different environments"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment"""
    
    environment_name: str
    aws_region: str
    aws_account: str
    
    # Lambda configuration
    lambda_memory_mb: int = 512
    lambda_timeout_seconds: int = 30
    lambda_ephemeral_storage_mb: int = 512
    
    # DynamoDB configuration
    dynamodb_billing_mode: str = "PAY_PER_REQUEST"  # or PROVISIONED
    dynamodb_read_capacity: int = 100
    dynamodb_write_capacity: int = 100
    
    # API Gateway configuration
    api_gateway_throttle_rate_limit: int = 10000
    api_gateway_throttle_burst_limit: int = 5000
    
    # CloudWatch configuration
    log_retention_days: int = 30
    
    # Monitoring configuration
    enable_xray_tracing: bool = True
    enable_detailed_monitoring: bool = True
    
    # Deployment configuration
    enable_blue_green_deployment: bool = True
    enable_auto_rollback: bool = True
    
    # Tags
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        
        # Add default tags
        self.tags.update({
            "Environment": self.environment_name,
            "Project": "AgentFirst2",
            "ManagedBy": "CDK",
            "CreatedAt": "2025-01-25"
        })


# Development environment
DEVELOPMENT_CONFIG = EnvironmentConfig(
    environment_name="development",
    aws_region="us-east-1",
    aws_account="373527788609",
    lambda_memory_mb=512,
    lambda_timeout_seconds=30,
    dynamodb_billing_mode="PAY_PER_REQUEST",
    log_retention_days=7,
    enable_xray_tracing=True,
    enable_detailed_monitoring=False,
    enable_blue_green_deployment=False,
    enable_auto_rollback=False
)

# Staging environment
STAGING_CONFIG = EnvironmentConfig(
    environment_name="staging",
    aws_region="us-east-1",
    aws_account="373527788609",
    lambda_memory_mb=512,
    lambda_timeout_seconds=30,
    dynamodb_billing_mode="PAY_PER_REQUEST",
    log_retention_days=14,
    enable_xray_tracing=True,
    enable_detailed_monitoring=True,
    enable_blue_green_deployment=True,
    enable_auto_rollback=True
)

# Production environment
PRODUCTION_CONFIG = EnvironmentConfig(
    environment_name="production",
    aws_region="us-east-1",
    aws_account="373527788609",
    lambda_memory_mb=512,
    lambda_timeout_seconds=30,
    dynamodb_billing_mode="PAY_PER_REQUEST",
    log_retention_days=30,
    enable_xray_tracing=True,
    enable_detailed_monitoring=True,
    enable_blue_green_deployment=True,
    enable_auto_rollback=True
)

# Configuration map
CONFIGS: Dict[str, EnvironmentConfig] = {
    "development": DEVELOPMENT_CONFIG,
    "staging": STAGING_CONFIG,
    "production": PRODUCTION_CONFIG
}


def get_config(environment: str) -> EnvironmentConfig:
    """Get configuration for environment"""
    if environment not in CONFIGS:
        raise ValueError(f"Unknown environment: {environment}. Must be one of: {list(CONFIGS.keys())}")
    return CONFIGS[environment]
