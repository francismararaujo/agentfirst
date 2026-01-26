"""Integration tests for User Repository"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from app.omnichannel.authentication import (
    UserRepository,
    UserRepositoryConfig,
)


@pytest.mark.integration
class TestUserRepositoryIntegration:
    """Integration tests for user repository"""

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
    async def test_complete_user_lifecycle(self, repository):
        """Test complete user lifecycle"""
        email = "user@example.com"

        # Mock DynamoDB responses
        repository.table.put_item = MagicMock()
        repository.table.get_item = MagicMock(return_value={})
        repository.table.update_item = MagicMock()
        repository.table.delete_item = MagicMock()

        # 1. Create user
        user = await repository.create_user(email, tier="free")
        assert user.email == email
        assert user.tier == "free"
        assert user.payment_status == "active"

        # 2. Get user
        repository.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": email,
                    "tier": "free",
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                    "payment_status": "active",
                    "usage_month": 0,
                    "usage_total": 0,
                    "metadata": {},
                }
            }
        )

        retrieved_user = await repository.get_user(email)
        assert retrieved_user is not None
        assert retrieved_user.email == email

        # 3. Update tier
        repository.table.update_item = MagicMock()
        updated_user = await repository.update_tier(email, "pro")
        assert updated_user is not None

        # 4. Increment usage
        repository.table.update_item = MagicMock()
        updated_user = await repository.increment_usage_month(email, count=10)
        assert updated_user is not None

        # 5. Delete user
        repository.table.delete_item = MagicMock(
            return_value={"Attributes": {"email": email}}
        )
        result = await repository.delete_user(email)
        assert result is True

    @pytest.mark.asyncio
    async def test_multiple_users_management(self, repository):
        """Test managing multiple users"""
        email1 = "user1@example.com"
        email2 = "user2@example.com"

        repository.table.put_item = MagicMock()
        repository.table.get_item = MagicMock(return_value={})

        # Create first user
        user1 = await repository.create_user(email1, tier="free")
        assert user1.email == email1

        # Create second user
        user2 = await repository.create_user(email2, tier="pro")
        assert user2.email == email2

        # Get all users
        repository.table.scan = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": email1,
                        "tier": "free",
                        "created_at": user1.created_at,
                        "updated_at": user1.updated_at,
                        "payment_status": "active",
                        "usage_month": 0,
                        "usage_total": 0,
                        "metadata": {},
                    },
                    {
                        "email": email2,
                        "tier": "pro",
                        "created_at": user2.created_at,
                        "updated_at": user2.updated_at,
                        "payment_status": "active",
                        "usage_month": 0,
                        "usage_total": 0,
                        "metadata": {},
                    },
                ]
            }
        )

        users = await repository.get_all_users()
        assert len(users) == 2

    @pytest.mark.asyncio
    async def test_user_tier_upgrade_workflow(self, repository):
        """Test user tier upgrade workflow"""
        email = "user@example.com"

        repository.table.put_item = MagicMock()
        repository.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": email,
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

        # Create user with free tier
        user = await repository.create_user(email, tier="free")
        assert user.tier == "free"

        # Get tier limit
        limit = await repository.get_user_tier_limit(email)
        assert limit == 100

        # Upgrade to pro
        repository.table.update_item = MagicMock()
        upgraded_user = await repository.update_tier(email, "pro")
        assert upgraded_user is not None

        # Get new tier limit
        repository.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": email,
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

        new_limit = await repository.get_user_tier_limit(email)
        assert new_limit == 10000

    @pytest.mark.asyncio
    async def test_user_usage_tracking(self, repository):
        """Test user usage tracking"""
        email = "user@example.com"

        repository.table.put_item = MagicMock()
        repository.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": email,
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

        # Create user
        user = await repository.create_user(email, tier="free")
        assert user.usage_month == 0

        # Increment usage
        repository.table.update_item = MagicMock()
        updated_user = await repository.increment_usage_month(email, count=25)
        assert updated_user is not None

        # Reset usage
        repository.table.update_item = MagicMock()
        reset_user = await repository.reset_monthly_usage(email)
        assert reset_user is not None

    @pytest.mark.asyncio
    async def test_user_trial_workflow(self, repository):
        """Test user trial workflow"""
        email = "user@example.com"
        trial_end = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

        repository.table.put_item = MagicMock()
        repository.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": email,
                    "tier": "pro",
                    "created_at": "2024-01-01T10:00:00+00:00",
                    "updated_at": "2024-01-01T10:00:00+00:00",
                    "payment_status": "active",
                    "trial_ends_at": None,
                    "usage_month": 0,
                    "usage_total": 0,
                    "metadata": {},
                }
            }
        )

        # Create user with pro tier
        user = await repository.create_user(email, tier="pro")
        assert user.payment_status == "active"

        # Update to trial status
        repository.table.update_item = MagicMock()
        trial_user = await repository.update_payment_status(email, "trial")
        assert trial_user is not None

    @pytest.mark.asyncio
    async def test_get_users_by_tier_filter(self, repository):
        """Test filtering users by tier"""
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
    async def test_get_users_by_payment_status_filter(self, repository):
        """Test filtering users by payment status"""
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


@pytest.mark.integration
class TestUserRepositoryErrorHandling:
    """Integration tests for user repository error handling"""

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
    async def test_invalid_email_formats(self, repository):
        """Test with various invalid email formats"""
        invalid_emails = [
            "invalid",  # No @
            "user",  # No @
            "example.com",  # No @
        ]

        for email in invalid_emails:
            repository.table.put_item = MagicMock()
            with pytest.raises(ValueError):
                await repository.create_user(email, tier="free")

    @pytest.mark.asyncio
    async def test_invalid_tier_values(self, repository):
        """Test with invalid tier values"""
        invalid_tiers = ["invalid", "basic", "premium", ""]

        for tier in invalid_tiers:
            repository.table.put_item = MagicMock()
            with pytest.raises(ValueError):
                await repository.create_user("user@example.com", tier=tier)

    @pytest.mark.asyncio
    async def test_update_nonexistent_user(self, repository):
        """Test updating non-existent user"""
        repository.table.get_item = MagicMock(return_value={})

        with pytest.raises(ValueError):
            await repository.update_user("user@example.com", tier="pro")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user(self, repository):
        """Test deleting non-existent user"""
        repository.table.delete_item = MagicMock(return_value={})

        result = await repository.delete_user("user@example.com")

        assert result is False

    @pytest.mark.asyncio
    async def test_invalid_payment_status(self, repository):
        """Test with invalid payment status"""
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

        with pytest.raises(ValueError):
            await repository.update_payment_status("user@example.com", "invalid")
