#!/usr/bin/env python3
"""
Setup AWS Secrets Manager for AgentFirst2 MVP

This script helps configure secrets in AWS Secrets Manager.
Used by GitHub Actions for secure credential management.

Usage:
    python scripts/setup_secrets.py --list
    python scripts/setup_secrets.py --telegram-token "your_token"
    python scripts/setup_secrets.py --ifood-client-id "id" --ifood-client-secret "secret"
"""

import json
import sys
import argparse
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError


class SecretsSetup:
    """Setup and manage AWS Secrets Manager for AgentFirst2"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.client = boto3.client("secretsmanager", region_name=region)
        
        # Secret names used by the application
        self.secret_names = {
            "telegram": "agentfirst/telegram",
            "ifood": "agentfirst/ifood",
            "bedrock": "agentfirst/bedrock",
        }
    
    def create_or_update_secret(
        self,
        secret_name: str,
        secret_value: Dict[str, Any],
        description: str = ""
    ) -> bool:
        """Create or update a secret in AWS Secrets Manager"""
        try:
            # Try to create the secret
            self.client.create_secret(
                Name=secret_name,
                SecretString=json.dumps(secret_value),
                Description=description,
                Tags=[
                    {"Key": "Project", "Value": "AgentFirst2"},
                    {"Key": "Environment", "Value": "production"},
                    {"Key": "ManagedBy", "Value": "GitHubActions"}
                ]
            )
            print(f"✅ Created secret: {secret_name}")
            return True
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceExistsException":
                # Secret exists, update it
                try:
                    self.client.update_secret(
                        SecretId=secret_name,
                        SecretString=json.dumps(secret_value),
                        Description=description
                    )
                    print(f"✅ Updated secret: {secret_name}")
                    return True
                except ClientError as update_error:
                    print(f"❌ Error updating secret {secret_name}: {update_error}")
                    return False
            else:
                print(f"❌ Error creating secret {secret_name}: {e}")
                return False
    
    def get_secret(self, secret_name: str) -> Optional[Dict[str, Any]]:
        """Get a secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response["SecretString"])
        except ClientError:
            return None
    
    def list_secrets(self) -> None:
        """List all AgentFirst secrets"""
        print("\n📋 AgentFirst2 Secrets Status:")
        print("-" * 60)
        
        for secret_type, secret_name in self.secret_names.items():
            secret = self.get_secret(secret_name)
            if secret:
                print(f"✅ {secret_type.upper()}: {secret_name}")
                # Show keys without values for security
                keys = list(secret.keys())
                print(f"   Keys: {', '.join(keys)}")
            else:
                print(f"❌ {secret_type.upper()}: {secret_name} (not found)")
        print("-" * 60)
    
    def setup_telegram_secret(self, bot_token: str, webhook_url: Optional[str] = None) -> bool:
        """Setup Telegram bot secret"""
        secret_value = {
            "bot_token": bot_token,
            "webhook_url": webhook_url or "https://d7p93u5agk.execute-api.us-east-1.amazonaws.com/prod/webhook/telegram"
        }
        
        return self.create_or_update_secret(
            self.secret_names["telegram"],
            secret_value,
            "Telegram Bot Token and webhook configuration for AgentFirst2"
        )
    
    def setup_ifood_secret(self, client_id: str, client_secret: str) -> bool:
        """Setup iFood OAuth secret"""
        secret_value = {
            "client_id": client_id,
            "client_secret": client_secret,
            "api_url": "https://api.ifood.com.br",
            "polling_interval": 30
        }
        
        return self.create_or_update_secret(
            self.secret_names["ifood"],
            secret_value,
            "iFood OAuth 2.0 credentials and API configuration for AgentFirst2"
        )
    
    def setup_bedrock_secret(
        self,
        region: str = "us-east-1",
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    ) -> bool:
        """Setup Bedrock configuration secret"""
        secret_value = {
            "region": region,
            "model_id": model_id
        }
        
        return self.create_or_update_secret(
            self.secret_names["bedrock"],
            secret_value,
            "AWS Bedrock configuration for Claude 3.5 Sonnet in AgentFirst2"
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Setup AWS Secrets Manager for AgentFirst2 MVP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all secrets
  python scripts/setup_secrets.py --list
  
  # Setup Telegram bot
  python scripts/setup_secrets.py --telegram-token "123456:ABC-DEF..."
  
  # Setup iFood credentials
  python scripts/setup_secrets.py --ifood-client-id "your_id" --ifood-client-secret "your_secret"
  
  # Setup Bedrock configuration
  python scripts/setup_secrets.py --setup-bedrock
        """
    )
    
    parser.add_argument("--region", default="us-east-1", help="AWS region (default: us-east-1)")
    parser.add_argument("--list", action="store_true", help="List all secrets")
    parser.add_argument("--telegram-token", help="Telegram bot token")
    parser.add_argument("--telegram-webhook", help="Telegram webhook URL (optional)")
    parser.add_argument("--ifood-client-id", help="iFood client ID")
    parser.add_argument("--ifood-client-secret", help="iFood client secret")
    parser.add_argument("--setup-bedrock", action="store_true", help="Setup Bedrock configuration")
    
    args = parser.parse_args()
    
    # Initialize secrets setup
    secrets = SecretsSetup(region=args.region)
    
    # List secrets if requested
    if args.list:
        secrets.list_secrets()
        return
    
    # Setup secrets
    success = True
    
    if args.telegram_token:
        print("🤖 Setting up Telegram secret...")
        success &= secrets.setup_telegram_secret(args.telegram_token, args.telegram_webhook)
    
    if args.ifood_client_id and args.ifood_client_secret:
        print("🍔 Setting up iFood secret...")
        success &= secrets.setup_ifood_secret(args.ifood_client_id, args.ifood_client_secret)
    
    if args.setup_bedrock:
        print("🧠 Setting up Bedrock secret...")
        success &= secrets.setup_bedrock_secret()
    
    if not any([args.list, args.telegram_token, args.ifood_client_id, args.setup_bedrock]):
        print("❌ No action specified. Use --help for usage information.")
        sys.exit(1)
    
    if success:
        print("\n✅ Secrets setup completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Verify secrets in AWS Console")
        print("   2. Test application with new secrets")
        print("   3. Deploy via GitHub Actions")
    else:
        print("\n❌ Some secrets failed to setup. Check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
