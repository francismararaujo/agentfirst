"""Integration tests for Limit Enforcer - Test limit enforcement workflows"""

import pytest
from unittest.mock import AsyncMock
from app.billing.limit_enforcer import (
    LimitEnforcer,
    LimitEnforcerConfig,
    LimitExceededError,
)


@pytest.mark.integration
class TestLimitEnforcerIntegration:
    """Integration tests for LimitEnforcer with mocked UsageTracker"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return LimitEnforcerConfig(
            region="us-east-1",
            usage_table="usage",
            upgrade_url_template="https://test.com/upgrade?email={email}&tier={tier}"
        )

    @pytest.fixture
    def enforcer(self, config):
        """Create enforcer with mocked tracker"""
        enforcer = LimitEnforcer(config)
        enforcer.tracker = AsyncMock()
        return enforcer

    @pytest.mark.asyncio
    async def test_free_tier_workflow(self, enforcer):
        """Test complete free tier workflow"""
        email = "test_free@example.com"

        # User starts with 0 usage
        enforcer.tracker.get_usage_count = AsyncMock(return_value=0)
        status = await enforcer.get_limit_status(email, "free")
        assert status['current_usage'] == 0
        assert status['remaining'] == 100
        assert status['exceeded'] is False

        # User at 50 usage
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)
        can_send = await enforcer.check_limit(email, "free")
        assert can_send is True

        # User at limit
        enforcer.tracker.get_usage_count = AsyncMock(return_value=100)
        can_send = await enforcer.check_limit(email, "free")
        assert can_send is False

        # Enforce limit - should raise
        with pytest.raises(LimitExceededError):
            await enforcer.enforce_limit(email, "free")

    @pytest.mark.asyncio
    async def test_pro_tier_workflow(self, enforcer):
        """Test complete pro tier workflow"""
        email = "test_pro@example.com"

        # User starts with 0 usage
        enforcer.tracker.get_usage_count = AsyncMock(return_value=0)
        status = await enforcer.get_limit_status(email, "pro")
        assert status['current_usage'] == 0
        assert status['remaining'] == 10000
        assert status['exceeded'] is False

        # User at 5000 usage
        enforcer.tracker.get_usage_count = AsyncMock(return_value=5000)
        can_send = await enforcer.check_limit(email, "pro")
        assert can_send is True

        # User at limit
        enforcer.tracker.get_usage_count = AsyncMock(return_value=10000)
        can_send = await enforcer.check_limit(email, "pro")
        assert can_send is False

    @pytest.mark.asyncio
    async def test_enterprise_tier_no_limits(self, enforcer):
        """Test enterprise tier has no limits"""
        email = "test_enterprise@example.com"

        # Check limit - should always pass
        can_send = await enforcer.check_limit(email, "enterprise")
        assert can_send is True

        # Enforce limit - should not raise
        await enforcer.enforce_limit(email, "enterprise")

        # Get available - should be unlimited
        available = await enforcer.get_messages_available(email, "enterprise")
        assert available == 999999999

    @pytest.mark.asyncio
    async def test_warning_threshold_workflow(self, enforcer):
        """Test warning threshold workflow"""
        email = "test_warning@example.com"

        # Below threshold
        enforcer.tracker.get_usage_count = AsyncMock(return_value=70)
        warning = await enforcer.get_warning_status(email, "free", warning_threshold=80.0)
        assert warning['is_warning'] is False

        # At threshold
        enforcer.tracker.get_usage_count = AsyncMock(return_value=80)
        warning = await enforcer.get_warning_status(email, "free", warning_threshold=80.0)
        assert warning['is_warning'] is True

    @pytest.mark.asyncio
    async def test_can_send_multiple_messages(self, enforcer):
        """Test checking if user can send multiple messages"""
        email = "test_multi@example.com"

        # User can send 50 messages
        enforcer.tracker.get_usage_count = AsyncMock(return_value=0)
        can_send = await enforcer.can_send_messages(email, "free", count=50)
        assert can_send is True

        # User at 95, can send 5 more
        enforcer.tracker.get_usage_count = AsyncMock(return_value=95)
        can_send = await enforcer.can_send_messages(email, "free", count=5)
        assert can_send is True

        # User at 95, cannot send 10 more
        can_send = await enforcer.can_send_messages(email, "free", count=10)
        assert can_send is False

    @pytest.mark.asyncio
    async def test_multiple_users_independent(self, enforcer):
        """Test that multiple users have independent limits"""
        email1 = "user1@example.com"
        email2 = "user2@example.com"

        # User 1 at 50
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)
        can_send1 = await enforcer.check_limit(email1, "free")
        assert can_send1 is True

        # User 2 at 100
        enforcer.tracker.get_usage_count = AsyncMock(return_value=100)
        can_send2 = await enforcer.check_limit(email2, "free")
        assert can_send2 is False

    @pytest.mark.asyncio
    async def test_limit_status_complete_info(self, enforcer):
        """Test that limit status returns complete information"""
        email = "test_status@example.com"

        enforcer.tracker.get_usage_count = AsyncMock(return_value=30)
        status = await enforcer.get_limit_status(email, "free")

        # Verify all fields
        assert 'email' in status
        assert 'tier' in status
        assert 'current_usage' in status
        assert 'limit' in status
        assert 'remaining' in status
        assert 'percentage' in status
        assert 'exceeded' in status
        assert 'upgrade_url' in status

        # Verify values
        assert status['email'] == email
        assert status['tier'] == "free"
        assert status['current_usage'] == 30
        assert status['limit'] == 100
        assert status['remaining'] == 70
        assert status['percentage'] == 30.0
        assert status['exceeded'] is False

    @pytest.mark.asyncio
    async def test_upgrade_url_generation(self, enforcer):
        """Test that upgrade URL is generated correctly"""
        email = "test_url@example.com"

        enforcer.tracker.get_usage_count = AsyncMock(return_value=100)
        status = await enforcer.get_limit_status(email, "free")

        # Verify upgrade URL
        assert status['upgrade_url'] is not None
        assert email in status['upgrade_url']
        assert "free" in status['upgrade_url']
        assert "test.com" in status['upgrade_url']

    @pytest.mark.asyncio
    async def test_tier_upgrade_scenario(self, enforcer):
        """Test tier upgrade scenario"""
        email = "test_upgrade@example.com"

        # User on free tier at limit
        enforcer.tracker.get_usage_count = AsyncMock(return_value=100)
        can_send_free = await enforcer.check_limit(email, "free")
        assert can_send_free is False

        # User upgrades to pro tier
        can_send_pro = await enforcer.check_limit(email, "pro")
        assert can_send_pro is True

        # User can send more messages on pro tier
        available_pro = await enforcer.get_messages_available(email, "pro")
        assert available_pro == 9900  # 10000 - 100 already used

    @pytest.mark.asyncio
    async def test_error_message_contains_upgrade_url(self, enforcer):
        """Test that LimitExceededError contains upgrade URL"""
        email = "test_error@example.com"

        enforcer.tracker.get_usage_count = AsyncMock(return_value=100)

        with pytest.raises(LimitExceededError) as exc_info:
            await enforcer.enforce_limit(email, "free")

        error = exc_info.value
        assert error.upgrade_url is not None
        assert email in error.upgrade_url

    @pytest.mark.asyncio
    async def test_all_tiers_status(self, enforcer):
        """Test getting status for all tiers"""
        email = "test_all_tiers@example.com"

        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        # Free tier
        status_free = await enforcer.get_limit_status(email, "free")
        assert status_free['limit'] == 100
        assert status_free['remaining'] == 50

        # Pro tier
        status_pro = await enforcer.get_limit_status(email, "pro")
        assert status_pro['limit'] == 10000
        assert status_pro['remaining'] == 9950

        # Enterprise tier
        status_enterprise = await enforcer.get_limit_status(email, "enterprise")
        assert status_enterprise['limit'] == 999999999



