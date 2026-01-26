"""Integration tests for Email-Based Authentication"""

import pytest
from unittest.mock import patch, MagicMock
from app.omnichannel.authentication import AuthService, AuthConfig


@pytest.mark.integration
class TestAuthIntegration:
    """Integration tests for authentication"""

    @pytest.fixture
    def config(self):
        """Create config"""
        return AuthConfig()

    @pytest.fixture
    def auth_service(self, config):
        """Create auth service"""
        with patch("boto3.resource"):
            return AuthService(config)

    @pytest.mark.asyncio
    async def test_complete_user_lifecycle(self, auth_service):
        """Test complete user lifecycle"""
        email = "user@example.com"

        # Mock DynamoDB responses
        auth_service.table.get_item = MagicMock(return_value={})
        auth_service.table.put_item = MagicMock()
        auth_service.table.update_item = MagicMock()
        auth_service.table.delete_item = MagicMock()

        # 1. Create user
        user = await auth_service.create_user(email)
        assert user.email == email
        assert user.tier == "free"

        # 2. Get user
        auth_service.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": email,
                    "tier": "free",
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                    "metadata": {},
                }
            }
        )

        retrieved_user = await auth_service.get_user(email)
        assert retrieved_user.email == email

        # 3. Update tier
        updated_user = await auth_service.update_user_tier(email, "pro")
        assert updated_user.email == email

        # 4. Get tier limit (after update, mock should return pro tier)
        auth_service.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": email,
                    "tier": "pro",
                    "created_at": user.created_at,
                    "updated_at": updated_user.updated_at,
                    "metadata": {},
                }
            }
        )

        limit = await auth_service.get_user_tier_limit(email)
        assert limit == 10000

        # 5. Delete user
        auth_service.table.get_item = MagicMock(
            return_value={"Item": {"email": email}}
        )
        result = await auth_service.delete_user(email)
        assert result is True

    @pytest.mark.asyncio
    async def test_multiple_users_workflow(self, auth_service):
        """Test workflow with multiple users"""
        users_data = [
            ("user1@example.com", "free"),
            ("user2@example.com", "pro"),
            ("user3@example.com", "free"),
        ]

        auth_service.table.get_item = MagicMock(return_value={})
        auth_service.table.put_item = MagicMock()

        # Create multiple users
        created_users = []
        for email, tier in users_data:
            user = await auth_service.create_user(email, tier=tier)
            created_users.append(user)
            assert user.email == email
            assert user.tier == tier

        assert len(created_users) == 3

    @pytest.mark.asyncio
    async def test_get_or_create_workflow(self, auth_service):
        """Test get or create workflow"""
        email = "user@example.com"

        # First call: user doesn't exist, should create
        auth_service.table.get_item = MagicMock(return_value={})
        auth_service.table.put_item = MagicMock()

        user1 = await auth_service.get_or_create_user(email)
        assert user1.email == email

        # Second call: user exists, should retrieve
        auth_service.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": email,
                    "tier": "free",
                    "created_at": user1.created_at,
                    "updated_at": user1.updated_at,
                    "metadata": {},
                }
            }
        )

        user2 = await auth_service.get_or_create_user(email)
        assert user2.email == email
        assert user2.created_at == user1.created_at

    @pytest.mark.asyncio
    async def test_tier_upgrade_workflow(self, auth_service):
        """Test tier upgrade workflow"""
        email = "user@example.com"

        # Create free user
        auth_service.table.get_item = MagicMock(return_value={})
        auth_service.table.put_item = MagicMock()

        user = await auth_service.create_user(email, tier="free")
        assert user.tier == "free"

        # Get free tier limit
        auth_service.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": email,
                    "tier": "free",
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                    "metadata": {},
                }
            }
        )

        limit_free = await auth_service.get_user_tier_limit(email)
        assert limit_free == 100

        # Upgrade to pro
        auth_service.table.update_item = MagicMock()
        upgraded_user = await auth_service.update_user_tier(email, "pro")
        assert upgraded_user.email == email

        # Get pro tier limit
        auth_service.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": email,
                    "tier": "pro",
                    "created_at": user.created_at,
                    "updated_at": upgraded_user.updated_at,
                    "metadata": {},
                }
            }
        )

        limit_pro = await auth_service.get_user_tier_limit(email)
        assert limit_pro == 10000


@pytest.mark.integration
class TestAuthErrorHandling:
    """Integration tests for authentication error handling"""

    @pytest.fixture
    def config(self):
        """Create config"""
        return AuthConfig()

    @pytest.fixture
    def auth_service(self, config):
        """Create auth service"""
        with patch("boto3.resource"):
            return AuthService(config)

    @pytest.mark.asyncio
    async def test_duplicate_user_creation(self, auth_service):
        """Test creating duplicate user"""
        email = "user@example.com"

        # First creation succeeds
        auth_service.table.get_item = MagicMock(return_value={})
        auth_service.table.put_item = MagicMock()

        user1 = await auth_service.create_user(email)
        assert user1.email == email

        # Second creation fails
        auth_service.table.get_item = MagicMock(
            return_value={"Item": {"email": email}}
        )

        with pytest.raises(ValueError):
            await auth_service.create_user(email)

    @pytest.mark.asyncio
    async def test_update_nonexistent_user(self, auth_service):
        """Test updating non-existent user"""
        auth_service.table.get_item = MagicMock(return_value={})

        with pytest.raises(ValueError):
            await auth_service.update_user_tier("user@example.com", "pro")

    @pytest.mark.asyncio
    async def test_authenticate_invalid_email_formats(self, auth_service):
        """Test authenticating with various invalid email formats"""
        invalid_emails = [
            "invalid",
            "user@",
            "@example.com",
            "user@.com",
            "user @example.com",
        ]

        for email in invalid_emails:
            with pytest.raises(ValueError):
                await auth_service.authenticate_user(email)
