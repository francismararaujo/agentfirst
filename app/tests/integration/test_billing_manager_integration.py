"""Integration tests for Billing Manager"""

import pytest
from unittest.mock import AsyncMock
from app.billing.billing_manager import BillingManager, BillingStatus
from app.billing.usage_tracker import Usage


@pytest.mark.integration
class TestBillingManagerWorkflows:
    """Tests for billing manager workflows"""

    @pytest.mark.asyncio
    async def test_complete_upgrade_workflow(self):
        """Test complete upgrade workflow"""
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

        # Check initial billing info
        info = await manager.get_billing_info("test@example.com")
        assert info.tier == "free"
        assert info.messages_limit == 100

        # Generate upgrade link
        link = await manager.generate_upgrade_link("test@example.com", "pro")
        assert "pro" in link

        # Update tier after payment
        result = await manager.update_tier_after_payment(
            "test@example.com", "pro", "payment_123"
        )
        assert result["status"] == "success"
        assert result["new_tier"] == "pro"

    @pytest.mark.asyncio
    async def test_multiple_tier_upgrades(self):
        """Test multiple tier upgrades"""
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

        # Upgrade free to pro
        result1 = await manager.update_tier_after_payment(
            "test@example.com", "pro", "payment_1"
        )
        assert result1["new_tier"] == "pro"

        # Update mock for next upgrade
        usage_tracker.get_user_tier.return_value = "pro"

        # Upgrade pro to enterprise
        result2 = await manager.update_tier_after_payment(
            "test@example.com", "enterprise", "payment_2"
        )
        assert result2["new_tier"] == "enterprise"

    @pytest.mark.asyncio
    async def test_billing_info_consistency(self):
        """Test billing info consistency"""
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

        # Get billing info multiple times
        info1 = await manager.get_billing_info("test@example.com")
        info2 = await manager.get_billing_info("test@example.com")

        # Should be consistent
        assert info1.tier == info2.tier
        assert info1.messages_used == info2.messages_used
        assert info1.messages_limit == info2.messages_limit
        assert info1.messages_remaining == info2.messages_remaining


@pytest.mark.integration
class TestBillingManagerErrorHandling:
    """Tests for billing manager error handling"""

    @pytest.mark.asyncio
    async def test_invalid_tier_upgrade(self):
        """Test invalid tier upgrade"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        usage_tracker.get_user_tier.return_value = "pro"

        manager = BillingManager(usage_tracker, limit_enforcer)

        with pytest.raises(ValueError):
            await manager.generate_upgrade_link("test@example.com", "free")

    @pytest.mark.asyncio
    async def test_invalid_tier_in_update(self):
        """Test invalid tier in update"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        manager = BillingManager(usage_tracker, limit_enforcer)

        with pytest.raises(ValueError):
            await manager.update_tier_after_payment(
                "test@example.com", "invalid", "payment_123"
            )


@pytest.mark.integration
class TestBillingManagerStatusTransitions:
    """Tests for billing manager status transitions"""

    @pytest.mark.asyncio
    async def test_status_transition_trial_to_active(self):
        """Test status transition from trial to active"""
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

        # Initial status should be trial
        info1 = await manager.get_billing_info("test@example.com")
        assert info1.status == BillingStatus.TRIAL

        # Upgrade to pro
        await manager.update_tier_after_payment(
            "test@example.com", "pro", "payment_123"
        )

        # Update mock for pro tier
        usage_tracker.get_user_tier.return_value = "pro"

        # Status should now be active
        info2 = await manager.get_billing_info("test@example.com")
        assert info2.status == BillingStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_status_transition_to_suspended(self):
        """Test status transition to suspended"""
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

        # Status should be suspended when limit reached
        info = await manager.get_billing_info("test@example.com")
        assert info.status == BillingStatus.SUSPENDED
        assert info.messages_remaining == 0
