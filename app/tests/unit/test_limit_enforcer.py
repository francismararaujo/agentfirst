"""Unit tests for Limit Enforcer - Test limit checking and enforcement"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from app.billing.limit_enforcer import (
    LimitEnforcer,
    LimitEnforcerConfig,
    LimitExceededError,
)


@pytest.mark.unit
class TestLimitExceededError:
    """Tests for LimitExceededError"""

    def test_error_creation(self):
        """Test creating LimitExceededError"""
        error = LimitExceededError(
            email="test@example.com",
            tier="free",
            current_usage=100,
            limit=100,
            remaining=0
        )
        assert error.email == "test@example.com"
        assert error.tier == "free"
        assert error.current_usage == 100
        assert error.limit == 100
        assert error.remaining == 0

    def test_error_message_free_tier(self):
        """Test error message for free tier"""
        error = LimitExceededError(
            email="test@example.com",
            tier="free",
            current_usage=100,
            limit=100,
            remaining=0
        )
        message = str(error)
        assert "Free tier" in message
        assert "100" in message
        assert "Pro" in message

    def test_error_message_pro_tier(self):
        """Test error message for pro tier"""
        error = LimitExceededError(
            email="test@example.com",
            tier="pro",
            current_usage=10000,
            limit=10000,
            remaining=0
        )
        message = str(error)
        assert "Pro tier" in message
        assert "10000" in message
        assert "Enterprise" in message


@pytest.mark.unit
class TestLimitEnforcerConfig:
    """Tests for LimitEnforcerConfig"""

    def test_config_defaults(self):
        """Test default configuration"""
        config = LimitEnforcerConfig()
        assert config.region == "us-east-1"
        assert config.usage_table == "usage"
        assert "agentfirst.app" in config.upgrade_url_template

    def test_config_custom(self):
        """Test custom configuration"""
        config = LimitEnforcerConfig(
            region="us-west-2",
            usage_table="custom_usage",
            upgrade_url_template="https://custom.com/upgrade?email={email}"
        )
        assert config.region == "us-west-2"
        assert config.usage_table == "custom_usage"
        assert "custom.com" in config.upgrade_url_template


@pytest.mark.unit
class TestLimitEnforcerStaticMethods:
    """Tests for LimitEnforcer static methods"""

    def test_get_tier_limit_free(self):
        """Test getting free tier limit"""
        limit = LimitEnforcer._get_tier_limit("free")
        assert limit == 100

    def test_get_tier_limit_pro(self):
        """Test getting pro tier limit"""
        limit = LimitEnforcer._get_tier_limit("pro")
        assert limit == 10000

    def test_get_tier_limit_enterprise(self):
        """Test getting enterprise tier limit"""
        limit = LimitEnforcer._get_tier_limit("enterprise")
        assert limit == 999999999

    def test_get_tier_limit_invalid(self):
        """Test getting invalid tier limit"""
        limit = LimitEnforcer._get_tier_limit("invalid")
        assert limit == 0


@pytest.mark.unit
class TestLimitEnforcerValidation:
    """Tests for LimitEnforcer validation"""

    @pytest.fixture
    def enforcer(self):
        """Create enforcer with mock tracker"""
        config = LimitEnforcerConfig()
        enforcer = LimitEnforcer(config)
        enforcer.tracker = MagicMock()
        return enforcer

    @pytest.mark.asyncio
    async def test_check_limit_invalid_email(self, enforcer):
        """Test check_limit with invalid email"""
        with pytest.raises(ValueError, match="Invalid email format"):
            await enforcer.check_limit("invalidemail", "free")

    @pytest.mark.asyncio
    async def test_check_limit_invalid_tier(self, enforcer):
        """Test check_limit with invalid tier"""
        with pytest.raises(ValueError, match="Invalid tier"):
            await enforcer.check_limit("test@example.com", "invalid")

    @pytest.mark.asyncio
    async def test_enforce_limit_invalid_email(self, enforcer):
        """Test enforce_limit with invalid email"""
        with pytest.raises(ValueError, match="Invalid email format"):
            await enforcer.enforce_limit("invalidemail", "free")

    @pytest.mark.asyncio
    async def test_enforce_limit_invalid_tier(self, enforcer):
        """Test enforce_limit with invalid tier"""
        with pytest.raises(ValueError, match="Invalid tier"):
            await enforcer.enforce_limit("test@example.com", "invalid")

    @pytest.mark.asyncio
    async def test_get_limit_status_invalid_email(self, enforcer):
        """Test get_limit_status with invalid email"""
        with pytest.raises(ValueError, match="Invalid email format"):
            await enforcer.get_limit_status("invalidemail", "free")

    @pytest.mark.asyncio
    async def test_get_limit_status_invalid_tier(self, enforcer):
        """Test get_limit_status with invalid tier"""
        with pytest.raises(ValueError, match="Invalid tier"):
            await enforcer.get_limit_status("test@example.com", "invalid")

    @pytest.mark.asyncio
    async def test_get_warning_status_invalid_threshold(self, enforcer):
        """Test get_warning_status with invalid threshold"""
        with pytest.raises(ValueError, match="Warning threshold must be between 0 and 100"):
            await enforcer.get_warning_status("test@example.com", "free", warning_threshold=150)

    @pytest.mark.asyncio
    async def test_can_send_messages_invalid_email(self, enforcer):
        """Test can_send_messages with invalid email"""
        with pytest.raises(ValueError, match="Invalid email format"):
            await enforcer.can_send_messages("invalidemail", "free")

    @pytest.mark.asyncio
    async def test_can_send_messages_invalid_tier(self, enforcer):
        """Test can_send_messages with invalid tier"""
        with pytest.raises(ValueError, match="Invalid tier"):
            await enforcer.can_send_messages("test@example.com", "invalid")

    @pytest.mark.asyncio
    async def test_can_send_messages_invalid_count(self, enforcer):
        """Test can_send_messages with invalid count"""
        with pytest.raises(ValueError, match="Count must be positive"):
            await enforcer.can_send_messages("test@example.com", "free", count=0)


@pytest.mark.unit
class TestLimitEnforcerMethods:
    """Tests for LimitEnforcer methods"""

    @pytest.fixture
    def enforcer(self):
        """Create enforcer with mock tracker"""
        config = LimitEnforcerConfig()
        enforcer = LimitEnforcer(config)
        enforcer.tracker = MagicMock()
        return enforcer

    @pytest.mark.asyncio
    async def test_check_limit_free_tier_under_limit(self, enforcer):
        """Test check_limit for free tier under limit"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        result = await enforcer.check_limit("test@example.com", "free")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_limit_free_tier_at_limit(self, enforcer):
        """Test check_limit for free tier at limit"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=100)

        result = await enforcer.check_limit("test@example.com", "free")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_limit_pro_tier_under_limit(self, enforcer):
        """Test check_limit for pro tier under limit"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=5000)

        result = await enforcer.check_limit("test@example.com", "pro")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_limit_enterprise_tier(self, enforcer):
        """Test check_limit for enterprise tier"""
        result = await enforcer.check_limit("test@example.com", "enterprise")

        assert result is True

    @pytest.mark.asyncio
    async def test_enforce_limit_free_tier_under_limit(self, enforcer):
        """Test enforce_limit for free tier under limit"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        # Should not raise
        await enforcer.enforce_limit("test@example.com", "free")

    @pytest.mark.asyncio
    async def test_enforce_limit_free_tier_at_limit(self, enforcer):
        """Test enforce_limit for free tier at limit"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=100)

        with pytest.raises(LimitExceededError) as exc_info:
            await enforcer.enforce_limit("test@example.com", "free")

        error = exc_info.value
        assert error.email == "test@example.com"
        assert error.tier == "free"
        assert error.current_usage == 100
        assert error.limit == 100

    @pytest.mark.asyncio
    async def test_enforce_limit_pro_tier_at_limit(self, enforcer):
        """Test enforce_limit for pro tier at limit"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=10000)

        with pytest.raises(LimitExceededError) as exc_info:
            await enforcer.enforce_limit("test@example.com", "pro")

        error = exc_info.value
        assert error.tier == "pro"
        assert error.limit == 10000

    @pytest.mark.asyncio
    async def test_enforce_limit_enterprise_tier(self, enforcer):
        """Test enforce_limit for enterprise tier"""
        # Should not raise
        await enforcer.enforce_limit("test@example.com", "enterprise")

    @pytest.mark.asyncio
    async def test_get_limit_status_free_tier(self, enforcer):
        """Test get_limit_status for free tier"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        status = await enforcer.get_limit_status("test@example.com", "free")

        assert status['email'] == "test@example.com"
        assert status['tier'] == "free"
        assert status['current_usage'] == 50
        assert status['limit'] == 100
        assert status['remaining'] == 50
        assert status['percentage'] == 50.0
        assert status['exceeded'] is False

    @pytest.mark.asyncio
    async def test_get_limit_status_at_limit(self, enforcer):
        """Test get_limit_status when at limit"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=100)

        status = await enforcer.get_limit_status("test@example.com", "free")

        assert status['exceeded'] is True
        assert status['upgrade_url'] is not None

    @pytest.mark.asyncio
    async def test_get_warning_status_below_threshold(self, enforcer):
        """Test get_warning_status below threshold"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        status = await enforcer.get_warning_status("test@example.com", "free", warning_threshold=80.0)

        assert status['percentage'] == 50.0
        assert status['is_warning'] is False

    @pytest.mark.asyncio
    async def test_get_warning_status_at_threshold(self, enforcer):
        """Test get_warning_status at threshold"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=80)

        status = await enforcer.get_warning_status("test@example.com", "free", warning_threshold=80.0)

        assert status['percentage'] == 80.0
        assert status['is_warning'] is True

    @pytest.mark.asyncio
    async def test_get_warning_status_above_threshold(self, enforcer):
        """Test get_warning_status above threshold"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=90)

        status = await enforcer.get_warning_status("test@example.com", "free", warning_threshold=80.0)

        assert status['percentage'] == 90.0
        assert status['is_warning'] is True

    @pytest.mark.asyncio
    async def test_can_send_messages_free_tier_yes(self, enforcer):
        """Test can_send_messages for free tier - yes"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        result = await enforcer.can_send_messages("test@example.com", "free", count=50)

        assert result is True

    @pytest.mark.asyncio
    async def test_can_send_messages_free_tier_no(self, enforcer):
        """Test can_send_messages for free tier - no"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=95)

        result = await enforcer.can_send_messages("test@example.com", "free", count=10)

        assert result is False

    @pytest.mark.asyncio
    async def test_can_send_messages_enterprise_tier(self, enforcer):
        """Test can_send_messages for enterprise tier"""
        result = await enforcer.can_send_messages("test@example.com", "enterprise", count=1000000)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_messages_available_free_tier(self, enforcer):
        """Test get_messages_available for free tier"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=30)

        available = await enforcer.get_messages_available("test@example.com", "free")

        assert available == 70

    @pytest.mark.asyncio
    async def test_get_messages_available_pro_tier(self, enforcer):
        """Test get_messages_available for pro tier"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=3000)

        available = await enforcer.get_messages_available("test@example.com", "pro")

        assert available == 7000

    @pytest.mark.asyncio
    async def test_get_messages_available_enterprise_tier(self, enforcer):
        """Test get_messages_available for enterprise tier"""
        available = await enforcer.get_messages_available("test@example.com", "enterprise")

        assert available == 999999999

    @pytest.mark.asyncio
    async def test_get_messages_available_at_limit(self, enforcer):
        """Test get_messages_available when at limit"""
        enforcer.tracker.get_usage_count = AsyncMock(return_value=100)

        available = await enforcer.get_messages_available("test@example.com", "free")

        assert available == 0

    def test_generate_upgrade_url(self):
        """Test generating upgrade URL"""
        config = LimitEnforcerConfig()
        enforcer = LimitEnforcer(config)

        url = enforcer._generate_upgrade_url("test@example.com", "free")

        assert "test@example.com" in url
        assert "free" in url
        assert "agentfirst.app" in url
