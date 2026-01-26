"""Unit tests for User Repository"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from app.omnichannel.authentication import (
    UserRepository,
    User,
    UserRepositoryConfig,
)


@pytest.mark.unit
class TestUserRepositoryConfig:
    """Tests for UserRepositoryConfig"""

    def test_config_creation_with_defaults(self):
        """Test creating config with default values"""
        config = UserRepositoryConfig()

        assert config.region == "us-east-1"
        assert config.users_table == "users"
        assert config.email_index == "email-index"

    def test_config_creation_with_custom_values(self):
        """Test creating config with custom values"""
        config = UserRepositoryConfig(
            region="eu-west-1",
            users_table="custom_users",
            email_index="custom_index",
        )

        assert config.region == "eu-west-1"
        assert config.users_table == "custom_users"
        assert config.email_index == "custom_index"


@pytest.mark.unit
class TestUser:
    """Tests for User model"""

    def test_user_creation_with_defaults(self):
        """Test creating user with default values"""
        user = User(email="user@example.com")

        assert user.email == "user@example.com"
        assert user.tier == "free"
        assert user.payment_status == "active"
        assert user.usage_month == 0
        assert user.usage_total == 0
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_creation_with_custom_values(self):
        """Test creating user with custom values"""
        user = User(
            email="user@example.com",
            tier="pro",
            payment_status="trial",
            usage_month=50,
            usage_total=150,
        )

        assert user.email == "user@example.com"
        assert user.tier == "pro"
        assert user.payment_status == "trial"
        assert user.usage_month == 50
        assert user.usage_total == 150

    def test_user_to_dict(self):
        """Test converting user to dictionary"""
        user = User(email="user@example.com", tier="pro")
        user_dict = user.to_dict()

        assert user_dict["email"] == "user@example.com"
        assert user_dict["tier"] == "pro"
        assert user_dict["payment_status"] == "active"

    def test_user_from_dict(self):
        """Test creating user from dictionary"""
        data = {
            "email": "user@example.com",
            "tier": "pro",
            "created_at": "2024-01-01T10:00:00+00:00",
            "updated_at": "2024-01-01T10:00:00+00:00",
            "payment_status": "active",
            "usage_month": 50,
            "usage_total": 150,
            "metadata": {"key": "value"},
        }

        user = User.from_dict(data)

        assert user.email == "user@example.com"
        assert user.tier == "pro"
        assert user.usage_month == 50
        assert user.metadata["key"] == "value"

    def test_user_is_trial_active(self):
        """Test trial active check"""
        # Active trial
        future_trial_end = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        user = User(
            email="user@example.com",
            payment_status="trial",
            trial_ends_at=future_trial_end,
        )

        assert user.is_trial_active() is True
        assert user.is_trial_expired() is False

    def test_user_is_trial_expired(self):
        """Test trial expired check"""
        # Expired trial
        past_trial_end = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        user = User(
            email="user@example.com",
            payment_status="trial",
            trial_ends_at=past_trial_end,
        )

        assert user.is_trial_active() is False
        assert user.is_trial_expired() is True

    def test_user_no_trial(self):
        """Test user without trial"""
        user = User(email="user@example.com", payment_status="active")

        assert user.is_trial_active() is False
        # When there's no trial_ends_at, is_trial_expired should return False (no trial to expire)
        assert user.trial_ends_at is None


@pytest.mark.unit
class TestUserRepository:
    """Tests for UserRepository"""

    @pytest.fixture
    def config(self):
        """Create config"""
        return UserRepositoryConfig()

    @pytest.fixture
    def repository(self, config):
        """Create repository"""
        with patch("boto3.resource"):
            return UserRepository(config)

    @pytest.mark.asyncio
    async def test_create_user_success(self, repository):
        """Test creating user successfully"""
        repository.table.put_item = MagicMock()

        user = await repository.create_user("user@example.com", tier="free")

        assert user.email == "user@example.com"
        assert user.tier == "free"
        assert user.payment_status == "active"
        repository.table.put_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self, repository):
        """Test creating user with invalid email"""
        with pytest.raises(ValueError):
            await repository.create_user("invalid-email", tier="free")

    @pytest.mark.asyncio
    async def test_create_user_invalid_tier(self, repository):
        """Test creating user with invalid tier"""
        with pytest.raises(ValueError):
            await repository.create_user("user@example.com", tier="invalid")

    @pytest.mark.asyncio
    async def test_get_user_success(self, repository):
        """Test getting user successfully"""
        repository.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": "user@example.com",
                    "tier": "pro",
                    "created_at": "2024-01-01T10:00:00+00:00",
                    "updated_at": "2024-01-01T10:00:00+00:00",
                    "payment_status": "active",
                    "usage_month": 50,
                    "usage_total": 150,
                    "metadata": {},
                }
            }
        )

        user = await repository.get_user("user@example.com")

        assert user is not None
        assert user.email == "user@example.com"
        assert user.tier == "pro"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, repository):
        """Test getting user that doesn't exist"""
        repository.table.get_item = MagicMock(return_value={})

        user = await repository.get_user("user@example.com")

        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_invalid_email(self, repository):
        """Test getting user with invalid email"""
        with pytest.raises(ValueError):
            await repository.get_user("invalid-email")

    @pytest.mark.asyncio
    async def test_user_exists_true(self, repository):
        """Test user exists check (true)"""
        repository.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": "user@example.com",
                    "tier": "free",
                    "created_at": "2024-01-01T10:00:00+00:00",
                    "updated_at": "2024-01-01T10:00:00+00:00",
                    "payment_status": "active",
                    "usage_month": 0,
                    "usage_total": 0,
                    "metadata": {},
                }
            }
        )

        exists = await repository.user_exists("user@example.com")

        assert exists is True

    @pytest.mark.asyncio
    async def test_user_exists_false(self, repository):
        """Test user exists check (false)"""
        repository.table.get_item = MagicMock(return_value={})

        exists = await repository.user_exists("user@example.com")

        assert exists is False

    @pytest.mark.asyncio
    async def test_update_user_success(self, repository):
        """Test updating user"""
        repository.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": "user@example.com",
                    "tier": "free",
                    "created_at": "2024-01-01T10:00:00+00:00",
                    "updated_at": "2024-01-01T10:00:00+00:00",
                    "payment_status": "active",
                    "usage_month": 0,
                    "usage_total": 0,
                    "metadata": {},
                }
            }
        )
        repository.table.update_item = MagicMock()

        user = await repository.update_user("user@example.com", tier="pro")

        assert user is not None
        repository.table.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_tier_success(self, repository):
        """Test updating user tier"""
        repository.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": "user@example.com",
                    "tier": "free",
                    "created_at": "2024-01-01T10:00:00+00:00",
                    "updated_at": "2024-01-01T10:00:00+00:00",
                    "payment_status": "active",
                    "usage_month": 0,
                    "usage_total": 0,
                    "metadata": {},
                }
            }
        )
        repository.table.update_item = MagicMock()

        user = await repository.update_tier("user@example.com", "pro")

        assert user is not None
        repository.table.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_tier_invalid_tier(self, repository):
        """Test updating user with invalid tier"""
        with pytest.raises(ValueError):
            await repository.update_tier("user@example.com", "invalid")

    @pytest.mark.asyncio
    async def test_update_payment_status_success(self, repository):
        """Test updating payment status"""
        repository.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": "user@example.com",
                    "tier": "free",
                    "created_at": "2024-01-01T10:00:00+00:00",
                    "updated_at": "2024-01-01T10:00:00+00:00",
                    "payment_status": "active",
                    "usage_month": 0,
                    "usage_total": 0,
                    "metadata": {},
                }
            }
        )
        repository.table.update_item = MagicMock()

        user = await repository.update_payment_status("user@example.com", "trial")

        assert user is not None
        repository.table.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_usage_month_success(self, repository):
        """Test incrementing monthly usage"""
        repository.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": "user@example.com",
                    "tier": "free",
                    "created_at": "2024-01-01T10:00:00+00:00",
                    "updated_at": "2024-01-01T10:00:00+00:00",
                    "payment_status": "active",
                    "usage_month": 0,
                    "usage_total": 0,
                    "metadata": {},
                }
            }
        )
        repository.table.update_item = MagicMock()

        user = await repository.increment_usage_month("user@example.com", count=5)

        assert user is not None
        repository.table.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_usage_month_invalid_count(self, repository):
        """Test incrementing usage with invalid count"""
        with pytest.raises(ValueError):
            await repository.increment_usage_month("user@example.com", count=0)

    @pytest.mark.asyncio
    async def test_reset_monthly_usage_success(self, repository):
        """Test resetting monthly usage"""
        repository.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": "user@example.com",
                    "tier": "free",
                    "created_at": "2024-01-01T10:00:00+00:00",
                    "updated_at": "2024-01-01T10:00:00+00:00",
                    "payment_status": "active",
                    "usage_month": 50,
                    "usage_total": 150,
                    "metadata": {},
                }
            }
        )
        repository.table.update_item = MagicMock()

        user = await repository.reset_monthly_usage("user@example.com")

        assert user is not None
        repository.table.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_success(self, repository):
        """Test deleting user"""
        repository.table.delete_item = MagicMock(
            return_value={"Attributes": {"email": "user@example.com"}}
        )

        result = await repository.delete_user("user@example.com")

        assert result is True
        repository.table.delete_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, repository):
        """Test deleting user that doesn't exist"""
        repository.table.delete_item = MagicMock(return_value={})

        result = await repository.delete_user("user@example.com")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_tier_limit_free(self, repository):
        """Test getting tier limit for free tier"""
        limit = await repository.get_tier_limit("free")

        assert limit == 100

    @pytest.mark.asyncio
    async def test_get_tier_limit_pro(self, repository):
        """Test getting tier limit for pro tier"""
        limit = await repository.get_tier_limit("pro")

        assert limit == 10000

    @pytest.mark.asyncio
    async def test_get_tier_limit_enterprise(self, repository):
        """Test getting tier limit for enterprise tier"""
        limit = await repository.get_tier_limit("enterprise")

        assert limit == float('inf')

    @pytest.mark.asyncio
    async def test_get_tier_limit_invalid(self, repository):
        """Test getting tier limit for invalid tier"""
        with pytest.raises(ValueError):
            await repository.get_tier_limit("invalid")

    @pytest.mark.asyncio
    async def test_get_user_tier_limit_success(self, repository):
        """Test getting user tier limit"""
        repository.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": "user@example.com",
                    "tier": "pro",
                    "created_at": "2024-01-01T10:00:00+00:00",
                    "updated_at": "2024-01-01T10:00:00+00:00",
                    "payment_status": "active",
                    "usage_month": 0,
                    "usage_total": 0,
                    "metadata": {},
                }
            }
        )

        limit = await repository.get_user_tier_limit("user@example.com")

        assert limit == 10000

    @pytest.mark.asyncio
    async def test_get_all_users(self, repository):
        """Test getting all users"""
        repository.table.scan = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": "user1@example.com",
                        "tier": "free",
                        "created_at": "2024-01-01T10:00:00+00:00",
                        "updated_at": "2024-01-01T10:00:00+00:00",
                        "payment_status": "active",
                        "usage_month": 0,
                        "usage_total": 0,
                        "metadata": {},
                    },
                    {
                        "email": "user2@example.com",
                        "tier": "pro",
                        "created_at": "2024-01-01T10:00:00+00:00",
                        "updated_at": "2024-01-01T10:00:00+00:00",
                        "payment_status": "active",
                        "usage_month": 50,
                        "usage_total": 150,
                        "metadata": {},
                    },
                ]
            }
        )

        users = await repository.get_all_users()

        assert len(users) == 2
        assert users[0].email == "user1@example.com"
        assert users[1].email == "user2@example.com"

    @pytest.mark.asyncio
    async def test_get_users_by_tier(self, repository):
        """Test getting users by tier"""
        repository.table.scan = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": "user1@example.com",
                        "tier": "pro",
                        "created_at": "2024-01-01T10:00:00+00:00",
                        "updated_at": "2024-01-01T10:00:00+00:00",
                        "payment_status": "active",
                        "usage_month": 50,
                        "usage_total": 150,
                        "metadata": {},
                    },
                    {
                        "email": "user2@example.com",
                        "tier": "pro",
                        "created_at": "2024-01-01T10:00:00+00:00",
                        "updated_at": "2024-01-01T10:00:00+00:00",
                        "payment_status": "active",
                        "usage_month": 75,
                        "usage_total": 200,
                        "metadata": {},
                    },
                ]
            }
        )

        users = await repository.get_users_by_tier("pro")

        assert len(users) == 2
        assert all(u.tier == "pro" for u in users)

    @pytest.mark.asyncio
    async def test_get_users_by_payment_status(self, repository):
        """Test getting users by payment status"""
        repository.table.scan = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": "user1@example.com",
                        "tier": "free",
                        "created_at": "2024-01-01T10:00:00+00:00",
                        "updated_at": "2024-01-01T10:00:00+00:00",
                        "payment_status": "trial",
                        "usage_month": 0,
                        "usage_total": 0,
                        "metadata": {},
                    },
                    {
                        "email": "user2@example.com",
                        "tier": "pro",
                        "created_at": "2024-01-01T10:00:00+00:00",
                        "updated_at": "2024-01-01T10:00:00+00:00",
                        "payment_status": "trial",
                        "usage_month": 50,
                        "usage_total": 150,
                        "metadata": {},
                    },
                ]
            }
        )

        users = await repository.get_users_by_payment_status("trial")

        assert len(users) == 2
        assert all(u.payment_status == "trial" for u in users)
