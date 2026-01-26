"""Unit tests for Email-Based Authentication Service"""

import pytest
from unittest.mock import patch, MagicMock
from app.omnichannel.authentication import AuthService, AuthConfig, User


@pytest.mark.unit
class TestAuthConfig:
    """Tests for AuthConfig"""

    def test_config_creation_with_defaults(self):
        """Test creating config with default values"""
        config = AuthConfig()

        assert config.region == "us-east-1"
        assert config.users_table == "users"
        assert config.default_tier == "free"
        assert config.free_tier_limit == 100
        assert config.pro_tier_limit == 10000

    def test_config_creation_with_custom_values(self):
        """Test creating config with custom values"""
        config = AuthConfig(
            region="eu-west-1",
            users_table="custom_users",
            default_tier="pro",
            free_tier_limit=50,
            pro_tier_limit=5000,
        )

        assert config.region == "eu-west-1"
        assert config.users_table == "custom_users"
        assert config.default_tier == "pro"
        assert config.free_tier_limit == 50
        assert config.pro_tier_limit == 5000


@pytest.mark.unit
class TestUser:
    """Tests for User class"""

    def test_user_creation(self):
        """Test creating a user"""
        user = User(email="user@example.com", tier="free")

        assert user.email == "user@example.com"
        assert user.tier == "free"
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_to_dict(self):
        """Test converting user to dictionary"""
        user = User(email="user@example.com", tier="pro")
        user_dict = user.to_dict()

        assert user_dict["email"] == "user@example.com"
        assert user_dict["tier"] == "pro"
        assert "created_at" in user_dict
        assert "updated_at" in user_dict

    def test_user_from_dict(self):
        """Test creating user from dictionary"""
        data = {
            "email": "user@example.com",
            "tier": "pro",
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T10:00:00",
            "metadata": {"key": "value"},
        }

        user = User.from_dict(data)

        assert user.email == "user@example.com"
        assert user.tier == "pro"
        assert user.metadata["key"] == "value"

    def test_user_with_metadata(self):
        """Test user with metadata"""
        metadata = {"channel": "telegram", "telegram_id": "123456"}
        user = User(
            email="user@example.com",
            tier="free",
            metadata=metadata,
        )

        assert user.metadata["channel"] == "telegram"
        assert user.metadata["telegram_id"] == "123456"


@pytest.mark.unit
class TestAuthService:
    """Tests for AuthService"""

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
    async def test_user_exists_true(self, auth_service):
        """Test checking if user exists (true)"""
        auth_service.table.get_item = MagicMock(
            return_value={"Item": {"email": "user@example.com"}}
        )

        exists = await auth_service.user_exists("user@example.com")

        assert exists is True

    @pytest.mark.asyncio
    async def test_user_exists_false(self, auth_service):
        """Test checking if user exists (false)"""
        auth_service.table.get_item = MagicMock(return_value={})

        exists = await auth_service.user_exists("user@example.com")

        assert exists is False

    @pytest.mark.asyncio
    async def test_create_user_success(self, auth_service):
        """Test creating user successfully"""
        auth_service.table.get_item = MagicMock(return_value={})
        auth_service.table.put_item = MagicMock()

        user = await auth_service.create_user("user@example.com")

        assert user.email == "user@example.com"
        assert user.tier == "free"
        auth_service.table.put_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_already_exists(self, auth_service):
        """Test creating user that already exists"""
        auth_service.table.get_item = MagicMock(
            return_value={"Item": {"email": "user@example.com"}}
        )

        with pytest.raises(ValueError):
            await auth_service.create_user("user@example.com")

    @pytest.mark.asyncio
    async def test_create_user_with_custom_tier(self, auth_service):
        """Test creating user with custom tier"""
        auth_service.table.get_item = MagicMock(return_value={})
        auth_service.table.put_item = MagicMock()

        user = await auth_service.create_user("user@example.com", tier="pro")

        assert user.tier == "pro"

    @pytest.mark.asyncio
    async def test_get_user_success(self, auth_service):
        """Test retrieving user successfully"""
        auth_service.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": "user@example.com",
                    "tier": "free",
                    "created_at": "2024-01-01T10:00:00",
                    "updated_at": "2024-01-01T10:00:00",
                    "metadata": {},
                }
            }
        )

        user = await auth_service.get_user("user@example.com")

        assert user is not None
        assert user.email == "user@example.com"
        assert user.tier == "free"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, auth_service):
        """Test retrieving user that doesn't exist"""
        auth_service.table.get_item = MagicMock(return_value={})

        user = await auth_service.get_user("user@example.com")

        assert user is None

    @pytest.mark.asyncio
    async def test_get_or_create_user_existing(self, auth_service):
        """Test get or create user (existing)"""
        auth_service.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": "user@example.com",
                    "tier": "free",
                    "created_at": "2024-01-01T10:00:00",
                    "updated_at": "2024-01-01T10:00:00",
                    "metadata": {},
                }
            }
        )

        user = await auth_service.get_or_create_user("user@example.com")

        assert user.email == "user@example.com"

    @pytest.mark.asyncio
    async def test_get_or_create_user_new(self, auth_service):
        """Test get or create user (new)"""
        # First call returns empty (user doesn't exist)
        # Second call returns empty (for get_user check)
        # Third call returns the created user
        auth_service.table.get_item = MagicMock(return_value={})
        auth_service.table.put_item = MagicMock()

        user = await auth_service.get_or_create_user("user@example.com")

        assert user.email == "user@example.com"
        assert user.tier == "free"

    @pytest.mark.asyncio
    async def test_update_user_tier_success(self, auth_service):
        """Test updating user tier successfully"""
        auth_service.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": "user@example.com",
                    "tier": "free",
                    "created_at": "2024-01-01T10:00:00",
                    "updated_at": "2024-01-01T10:00:00",
                    "metadata": {},
                }
            }
        )
        auth_service.table.update_item = MagicMock()

        user = await auth_service.update_user_tier("user@example.com", "pro")

        assert user.email == "user@example.com"
        auth_service.table.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_tier_not_found(self, auth_service):
        """Test updating tier for non-existent user"""
        auth_service.table.get_item = MagicMock(return_value={})

        with pytest.raises(ValueError):
            await auth_service.update_user_tier("user@example.com", "pro")

    @pytest.mark.asyncio
    async def test_get_user_tier_limit_free(self, auth_service):
        """Test getting tier limit for free user"""
        auth_service.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": "user@example.com",
                    "tier": "free",
                    "created_at": "2024-01-01T10:00:00",
                    "updated_at": "2024-01-01T10:00:00",
                    "metadata": {},
                }
            }
        )

        limit = await auth_service.get_user_tier_limit("user@example.com")

        assert limit == 100

    @pytest.mark.asyncio
    async def test_get_user_tier_limit_pro(self, auth_service):
        """Test getting tier limit for pro user"""
        auth_service.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": "user@example.com",
                    "tier": "pro",
                    "created_at": "2024-01-01T10:00:00",
                    "updated_at": "2024-01-01T10:00:00",
                    "metadata": {},
                }
            }
        )

        limit = await auth_service.get_user_tier_limit("user@example.com")

        assert limit == 10000

    @pytest.mark.asyncio
    async def test_get_user_tier_limit_enterprise(self, auth_service):
        """Test getting tier limit for enterprise user"""
        auth_service.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "email": "user@example.com",
                    "tier": "enterprise",
                    "created_at": "2024-01-01T10:00:00",
                    "updated_at": "2024-01-01T10:00:00",
                    "metadata": {},
                }
            }
        )

        limit = await auth_service.get_user_tier_limit("user@example.com")

        assert limit == float("inf")

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service):
        """Test authenticating user successfully"""
        auth_service.table.get_item = MagicMock(return_value={})
        auth_service.table.put_item = MagicMock()

        user = await auth_service.authenticate_user("user@example.com")

        assert user.email == "user@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_email(self, auth_service):
        """Test authenticating with invalid email"""
        with pytest.raises(ValueError):
            await auth_service.authenticate_user("invalid-email")

    def test_is_valid_email_valid(self):
        """Test email validation (valid)"""
        assert AuthService._is_valid_email("user@example.com") is True
        assert AuthService._is_valid_email("user.name@example.co.uk") is True
        assert AuthService._is_valid_email("user+tag@example.com") is True

    def test_is_valid_email_invalid(self):
        """Test email validation (invalid)"""
        assert AuthService._is_valid_email("invalid-email") is False
        assert AuthService._is_valid_email("user@") is False
        assert AuthService._is_valid_email("@example.com") is False
        assert AuthService._is_valid_email("user@.com") is False

    @pytest.mark.asyncio
    async def test_delete_user_success(self, auth_service):
        """Test deleting user successfully"""
        auth_service.table.get_item = MagicMock(
            return_value={"Item": {"email": "user@example.com"}}
        )
        auth_service.table.delete_item = MagicMock()

        result = await auth_service.delete_user("user@example.com")

        assert result is True
        auth_service.table.delete_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, auth_service):
        """Test deleting user that doesn't exist"""
        auth_service.table.get_item = MagicMock(return_value={})

        result = await auth_service.delete_user("user@example.com")

        assert result is False
