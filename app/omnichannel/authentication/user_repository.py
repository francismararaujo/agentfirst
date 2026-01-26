"""User Repository - CRUD operations for user management"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError


@dataclass
class User:
    """User model"""
    email: str
    tier: str = "free"  # free, pro, enterprise
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payment_status: str = "active"  # active, inactive, trial
    trial_ends_at: Optional[str] = None
    usage_month: int = 0
    usage_total: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'email': self.email,
            'tier': self.tier,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'payment_status': self.payment_status,
            'trial_ends_at': self.trial_ends_at,
            'usage_month': self.usage_month,
            'usage_total': self.usage_total,
            'metadata': self.metadata,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'User':
        """Create from dictionary"""
        return User(
            email=data['email'],
            tier=data.get('tier', 'free'),
            created_at=data.get('created_at', datetime.now(timezone.utc).isoformat()),
            updated_at=data.get('updated_at', datetime.now(timezone.utc).isoformat()),
            payment_status=data.get('payment_status', 'active'),
            trial_ends_at=data.get('trial_ends_at'),
            usage_month=data.get('usage_month', 0),
            usage_total=data.get('usage_total', 0),
            metadata=data.get('metadata', {}),
        )

    def is_trial_active(self) -> bool:
        """Check if trial is still active"""
        if not self.trial_ends_at:
            return False
        trial_end = datetime.fromisoformat(self.trial_ends_at)
        return datetime.now(timezone.utc) < trial_end

    def is_trial_expired(self) -> bool:
        """Check if trial has expired"""
        return not self.is_trial_active()


@dataclass
class UserRepositoryConfig:
    """Configuration for user repository"""
    region: str = "us-east-1"
    users_table: str = "users"
    email_index: str = "email-index"


class UserRepository:
    """Repository for user CRUD operations"""

    def __init__(self, config: UserRepositoryConfig = None):
        """Initialize user repository"""
        self.config = config or UserRepositoryConfig()
        self.dynamodb = boto3.resource('dynamodb', region_name=self.config.region)
        self.table = self.dynamodb.Table(self.config.users_table)

    async def create_user(self, email: str, tier: str = "free",
                         metadata: Dict[str, Any] = None) -> User:
        """Create new user"""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")

        if tier not in ["free", "pro", "enterprise"]:
            raise ValueError("Invalid tier")

        # Create user
        user = User(
            email=email,
            tier=tier,
            payment_status="active",
            metadata=metadata or {}
        )

        try:
            item = user.to_dict()
            self.table.put_item(Item=item)
        except ClientError as e:
            raise ValueError(f"Failed to create user: {str(e)}")

        return user

    async def get_user(self, email: str) -> Optional[User]:
        """Get user by email"""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")

        try:
            response = self.table.get_item(Key={'email': email})

            if 'Item' not in response:
                return None

            return User.from_dict(response['Item'])
        except ClientError as e:
            raise ValueError(f"Failed to get user: {str(e)}")

    async def user_exists(self, email: str) -> bool:
        """Check if user exists"""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")

        try:
            user = await self.get_user(email)
            return user is not None
        except ValueError:
            return False

    async def update_user(self, email: str, **kwargs) -> Optional[User]:
        """Update user attributes"""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")

        # Get existing user
        user = await self.get_user(email)
        if not user:
            raise ValueError("User not found")

        try:
            updates = {
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            # Only allow specific fields to be updated
            allowed_fields = ['tier', 'payment_status', 'trial_ends_at', 'usage_month', 'usage_total', 'metadata']
            for field in allowed_fields:
                if field in kwargs:
                    updates[field] = kwargs[field]

            self.table.update_item(
                Key={'email': email},
                UpdateExpression='SET ' + ', '.join([f'{k} = :{k}' for k in updates.keys()]),
                ExpressionAttributeValues={f':{k}': v for k, v in updates.items()}
            )

            # Fetch updated user
            return await self.get_user(email)
        except ClientError as e:
            raise ValueError(f"Failed to update user: {str(e)}")

    async def update_tier(self, email: str, tier: str) -> Optional[User]:
        """Update user tier"""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")

        if tier not in ["free", "pro", "enterprise"]:
            raise ValueError("Invalid tier")

        return await self.update_user(email, tier=tier)

    async def update_payment_status(self, email: str, status: str) -> Optional[User]:
        """Update payment status"""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")

        if status not in ["active", "inactive", "trial"]:
            raise ValueError("Invalid payment status")

        return await self.update_user(email, payment_status=status)

    async def increment_usage_month(self, email: str, count: int = 1) -> Optional[User]:
        """Increment monthly usage counter"""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")

        if count < 1:
            raise ValueError("Count must be positive")

        try:
            self.table.update_item(
                Key={'email': email},
                UpdateExpression='ADD usage_month :inc, usage_total :inc SET updated_at = :updated',
                ExpressionAttributeValues={
                    ':inc': count,
                    ':updated': datetime.now(timezone.utc).isoformat()
                }
            )

            return await self.get_user(email)
        except ClientError as e:
            raise ValueError(f"Failed to increment usage: {str(e)}")

    async def reset_monthly_usage(self, email: str) -> Optional[User]:
        """Reset monthly usage counter"""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")

        return await self.update_user(email, usage_month=0)

    async def delete_user(self, email: str) -> bool:
        """Delete user"""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")

        try:
            response = self.table.delete_item(
                Key={'email': email},
                ReturnValues='ALL_OLD'
            )

            return 'Attributes' in response
        except ClientError as e:
            raise ValueError(f"Failed to delete user: {str(e)}")

    async def get_tier_limit(self, tier: str) -> int:
        """Get message limit for tier"""
        limits = {
            'free': 100,
            'pro': 10000,
            'enterprise': float('inf')
        }

        if tier not in limits:
            raise ValueError("Invalid tier")

        return limits[tier]

    async def get_user_tier_limit(self, email: str) -> int:
        """Get message limit for user"""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")

        user = await self.get_user(email)
        if not user:
            raise ValueError("User not found")

        return await self.get_tier_limit(user.tier)

    async def get_all_users(self) -> list:
        """Get all users (for admin purposes)"""
        try:
            response = self.table.scan()
            users = []
            for item in response.get('Items', []):
                users.append(User.from_dict(item))
            return users
        except ClientError as e:
            raise ValueError(f"Failed to get all users: {str(e)}")

    async def get_users_by_tier(self, tier: str) -> list:
        """Get all users with specific tier"""
        if tier not in ["free", "pro", "enterprise"]:
            raise ValueError("Invalid tier")

        try:
            response = self.table.scan(
                FilterExpression='tier = :tier',
                ExpressionAttributeValues={':tier': tier}
            )

            users = []
            for item in response.get('Items', []):
                users.append(User.from_dict(item))
            return users
        except ClientError as e:
            raise ValueError(f"Failed to get users by tier: {str(e)}")

    async def get_users_by_payment_status(self, status: str) -> list:
        """Get all users with specific payment status"""
        if status not in ["active", "inactive", "trial"]:
            raise ValueError("Invalid payment status")

        try:
            response = self.table.scan(
                FilterExpression='payment_status = :status',
                ExpressionAttributeValues={':status': status}
            )

            users = []
            for item in response.get('Items', []):
                users.append(User.from_dict(item))
            return users
        except ClientError as e:
            raise ValueError(f"Failed to get users by payment status: {str(e)}")
