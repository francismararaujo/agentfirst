"""Unit tests for Billing Manager"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.billing.billing_manager import (
    BillingManager,
    BillingManagerConfig,
    BillingStatus,
    BillingInfo,
)
from app.billing.usage_tracker import Usage


@pytest.mark.unit
class TestBillingManagerConfig:
    """Tests for BillingManagerConfig"""

    def test_config_creation_default(self):
        """Test creating config with defaults"""
        config = BillingManagerConfig()
        assert config.upgrade_base_url == "https://agentfirst.com/upgrade"
        assert config.trial_duration_days == 14

    def test_config_creation_custom(self):
        """Test creating config with custom values"""
        config = BillingManagerConfig(
            upgrade_base_url="https://custom.com/upgrade",
            trial_duration_days=30,
        )
        assert config.upgrade_base_url == "https://custom.com/upgrade"
        assert config.trial_duration_days == 30


@pytest.mark.unit
class TestBillingStatus:
    """Tests for BillingStatus enum"""

    def test_billing_status_active(self):
        """Test ACTIVE status"""
        assert BillingStatus.ACTIVE.value == "active"

    def test_billing_status_inactive(self):
        """Test INACTIVE status"""
        assert BillingStatus.INACTIVE.value == "inactive"

    def test_billing_status_trial(self):
        """Test TRIAL status"""
        assert BillingStatus.TRIAL.value == "trial"

    def test_billing_status_suspended(self):
        """Test SUSPENDED status"""
        assert BillingStatus.SUSPENDED.value == "suspended"


@pytest.mark.unit
class TestBillingInfo:
    """Tests for BillingInfo dataclass"""

    def test_billing_info_creation(self):
        """Test creating BillingInfo"""
        info = BillingInfo(
            email="test@example.com",
            tier="free",
            status=BillingStatus.TRIAL,
            messages_used=50,
            messages_limit=100,
            messages_remaining=50,
            upgrade_url="https://example.com/upgrade",
        )
        assert info.email == "test@example.com"
        assert info.tier == "free"
        assert info.status == BillingStatus.TRIAL
        assert info.messages_used == 50
        assert info.messages_limit == 100
        assert info.messages_remaining == 50
        assert info.upgrade_url == "https://example.com/upgrade"


@pytest.mark.unit
class TestBillingManagerGetBillingInfo:
    """Tests for get_billing_info method"""

    @pytest.mark.asyncio
    async def test_get_billing_info_free_tier(self):
        """Test getting billing info for free tier user"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        usage_tracker.get_user_tier.return_value = "free"
        usage_tracker.get_usage.return_value = Usage(
            email="test@example.com",
            year=2025,
            month=1,
            message_count=50,
        )

        manager = BillingManager(usage_tracker, limit_enforcer)
        info = await manager.get_billing_info("test@example.com")

        assert info.email == "test@example.com"
        assert info.tier == "free"
        assert info.messages_used == 50
        assert info.messages_limit == 100
        assert info.messages_remaining == 50
        assert info.status == BillingStatus.TRIAL

    @pytest.mark.asyncio
    async def test_get_billing_info_pro_tier(self):
        """Test getting billing info for pro tier user"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        usage_tracker.get_user_tier.return_value = "pro"
        usage_tracker.get_usage.return_value = Usage(
            email="test@example.com",
            year=2025,
            month=1,
            message_count=5000,
        )

        manager = BillingManager(usage_tracker, limit_enforcer)
        info = await manager.get_billing_info("test@example.com")

        assert info.tier == "pro"
        assert info.messages_used == 5000
        assert info.messages_limit == 10000
        assert info.messages_remaining == 5000
        assert info.status == BillingStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_billing_info_enterprise_tier(self):
        """Test getting billing info for enterprise tier user"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        usage_tracker.get_user_tier.return_value = "enterprise"
        usage_tracker.get_usage.return_value = Usage(
            email="test@example.com",
            year=2025,
            month=1,
            message_count=1000000,
        )

        manager = BillingManager(usage_tracker, limit_enforcer)
        info = await manager.get_billing_info("test@example.com")

        assert info.tier == "enterprise"
        assert info.messages_limit == 999999999
        assert info.status == BillingStatus.ACTIVE
        assert info.upgrade_url is None

    @pytest.mark.asyncio
    async def test_get_billing_info_limit_exceeded(self):
        """Test getting billing info when limit exceeded"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        usage_tracker.get_user_tier.return_value = "free"
        usage_tracker.get_usage.return_value = Usage(
            email="test@example.com",
            year=2025,
            month=1,
            message_count=100,
        )

        manager = BillingManager(usage_tracker, limit_enforcer)
        info = await manager.get_billing_info("test@example.com")

        assert info.messages_remaining == 0
        assert info.status == BillingStatus.SUSPENDED


@pytest.mark.unit
class TestBillingManagerCheckTierAndLimits:
    """Tests for check_tier_and_limits method"""

    @pytest.mark.asyncio
    async def test_check_tier_and_limits_free(self):
        """Test checking tier and limits for free user"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        usage_tracker.get_user_tier.return_value = "free"
        usage_tracker.get_usage.return_value = Usage(
            email="test@example.com",
            year=2025,
            month=1,
            message_count=50,
        )

        manager = BillingManager(usage_tracker, limit_enforcer)
        result = await manager.check_tier_and_limits("test@example.com")

        assert result["tier"] == "free"
        assert result["messages_used"] == 50
        assert result["messages_limit"] == 100
        assert result["messages_remaining"] == 50
        assert result["can_send_messages"] is True
        assert "upgrade_url" in result

    @pytest.mark.asyncio
    async def test_check_tier_and_limits_exceeded(self):
        """Test checking tier and limits when exceeded"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        usage_tracker.get_user_tier.return_value = "free"
        usage_tracker.get_usage.return_value = Usage(
            email="test@example.com",
            year=2025,
            month=1,
            message_count=100,
        )

        manager = BillingManager(usage_tracker, limit_enforcer)
        result = await manager.check_tier_and_limits("test@example.com")

        assert result["messages_remaining"] == 0
        assert result["can_send_messages"] is False


@pytest.mark.unit
class TestBillingManagerGenerateUpgradeLink:
    """Tests for generate_upgrade_link method"""

    @pytest.mark.asyncio
    async def test_generate_upgrade_link_free_to_pro(self):
        """Test generating upgrade link from free to pro"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        usage_tracker.get_user_tier.return_value = "free"

        manager = BillingManager(usage_tracker, limit_enforcer)
        link = await manager.generate_upgrade_link("test@example.com", "pro")

        assert "test@example.com" in link
        assert "pro" in link
        assert link.startswith("https://agentfirst.com/upgrade")

    @pytest.mark.asyncio
    async def test_generate_upgrade_link_invalid_tier(self):
        """Test generating upgrade link with invalid tier"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        manager = BillingManager(usage_tracker, limit_enforcer)

        with pytest.raises(ValueError, match="Invalid tier"):
            await manager.generate_upgrade_link("test@example.com", "invalid")

    @pytest.mark.asyncio
    async def test_generate_upgrade_link_invalid_upgrade(self):
        """Test generating upgrade link for invalid upgrade"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        usage_tracker.get_user_tier.return_value = "pro"

        manager = BillingManager(usage_tracker, limit_enforcer)

        with pytest.raises(ValueError, match="Cannot upgrade"):
            await manager.generate_upgrade_link("test@example.com", "free")


@pytest.mark.unit
class TestBillingManagerUpdateTierAfterPayment:
    """Tests for update_tier_after_payment method"""

    @pytest.mark.asyncio
    async def test_update_tier_after_payment_free_to_pro(self):
        """Test updating tier after payment from free to pro"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        usage_tracker.get_user_tier.return_value = "free"
        usage_tracker.get_usage.return_value = Usage(
            email="test@example.com",
            year=2025,
            month=1,
            message_count=50,
        )

        manager = BillingManager(usage_tracker, limit_enforcer)
        result = await manager.update_tier_after_payment(
            "test@example.com", "pro", "payment_123"
        )

        assert result["email"] == "test@example.com"
        assert result["previous_tier"] == "free"
        assert result["new_tier"] == "pro"
        assert result["payment_id"] == "payment_123"
        assert result["status"] == "success"
        assert result["billing_info"]["tier"] == "free"
        usage_tracker.update_user_tier.assert_called_once_with(
            "test@example.com", "pro"
        )

    @pytest.mark.asyncio
    async def test_update_tier_after_payment_invalid_tier(self):
        """Test updating tier with invalid tier"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        manager = BillingManager(usage_tracker, limit_enforcer)

        with pytest.raises(ValueError, match="Invalid tier"):
            await manager.update_tier_after_payment(
                "test@example.com", "invalid", "payment_123"
            )

    @pytest.mark.asyncio
    async def test_update_tier_after_payment_invalid_upgrade(self):
        """Test updating tier for invalid upgrade"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        usage_tracker.get_user_tier.return_value = "pro"

        manager = BillingManager(usage_tracker, limit_enforcer)

        with pytest.raises(ValueError, match="Cannot upgrade"):
            await manager.update_tier_after_payment(
                "test@example.com", "free", "payment_123"
            )


@pytest.mark.unit
class TestBillingManagerDetermineStatus:
    """Tests for _determine_status method"""

    def test_determine_status_free_with_messages(self):
        """Test determining status for free tier with messages remaining"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        manager = BillingManager(usage_tracker, limit_enforcer)
        status = manager._determine_status("free", 50)

        assert status == BillingStatus.TRIAL

    def test_determine_status_free_no_messages(self):
        """Test determining status for free tier with no messages"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        manager = BillingManager(usage_tracker, limit_enforcer)
        status = manager._determine_status("free", 0)

        assert status == BillingStatus.SUSPENDED

    def test_determine_status_pro_with_messages(self):
        """Test determining status for pro tier with messages remaining"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        manager = BillingManager(usage_tracker, limit_enforcer)
        status = manager._determine_status("pro", 5000)

        assert status == BillingStatus.ACTIVE

    def test_determine_status_pro_no_messages(self):
        """Test determining status for pro tier with no messages"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        manager = BillingManager(usage_tracker, limit_enforcer)
        status = manager._determine_status("pro", 0)

        assert status == BillingStatus.SUSPENDED


@pytest.mark.unit
class TestBillingManagerGenerateUpgradeUrl:
    """Tests for _generate_upgrade_url method"""

    def test_generate_upgrade_url_default(self):
        """Test generating upgrade URL with default config"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        manager = BillingManager(usage_tracker, limit_enforcer)
        url = manager._generate_upgrade_url("test@example.com", "pro")

        assert url == "https://agentfirst.com/upgrade?email=test@example.com&tier=pro"

    def test_generate_upgrade_url_custom(self):
        """Test generating upgrade URL with custom config"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()
        config = BillingManagerConfig(upgrade_base_url="https://custom.com/upgrade")

        manager = BillingManager(usage_tracker, limit_enforcer, config)
        url = manager._generate_upgrade_url("test@example.com", "pro")

        assert url == "https://custom.com/upgrade?email=test@example.com&tier=pro"
