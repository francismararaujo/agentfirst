"""Integration tests for Usage Tracker - Test complete workflows"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from app.billing.usage_tracker import Usage, UsageTrackerConfig, UsageTracker


@pytest.mark.integration
class TestUsageTrackerLifecycle:
    """Tests for complete Usage Tracker lifecycle"""

    @pytest.fixture
    def tracker(self):
        """Create tracker with mock DynamoDB"""
        config = UsageTrackerConfig()
        tracker = UsageTracker(config)
        tracker.table = MagicMock()
        return tracker

    @pytest.mark.asyncio
    async def test_complete_user_lifecycle_free_tier(self, tracker):
        """Test complete lifecycle for free tier user"""
        email = "user@example.com"
        
        # 1. Create new usage
        tracker.table.get_item = MagicMock(return_value={})
        tracker.table.put_item = MagicMock()
        
        usage = await tracker.get_or_create_usage(email, tier="free")
        assert usage.message_count == 0
        assert usage.tier == "free"
        
        # 2. Increment usage
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': email,
            'year': 2024,
            'month': 1,
            'message_count': 0,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})
        tracker.table.update_item = MagicMock()
        
        await tracker.increment_usage(email, count=10)
        tracker.table.update_item.assert_called_once()
        
        # 3. Check usage count
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': email,
            'year': 2024,
            'month': 1,
            'message_count': 10,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})
        
        count = await tracker.get_usage_count(email)
        assert count == 10
        
        # 4. Check remaining messages
        remaining = await tracker.get_remaining_messages(email, tier="free")
        assert remaining == 90  # 100 - 10

    @pytest.mark.asyncio
    async def test_complete_user_lifecycle_pro_tier(self, tracker):
        """Test complete lifecycle for pro tier user"""
        email = "user@example.com"
        
        # 1. Create new usage
        tracker.table.get_item = MagicMock(return_value={})
        tracker.table.put_item = MagicMock()
        
        usage = await tracker.get_or_create_usage(email, tier="pro")
        assert usage.message_count == 0
        assert usage.tier == "pro"
        
        # 2. Increment usage multiple times
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': email,
            'year': 2024,
            'month': 1,
            'message_count': 0,
            'tier': "pro",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})
        tracker.table.update_item = MagicMock()
        
        for i in range(5):
            await tracker.increment_usage(email, count=100)
        
        assert tracker.table.update_item.call_count == 5
        
        # 3. Check usage percentage
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': email,
            'year': 2024,
            'month': 1,
            'message_count': 500,
            'tier': "pro",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})
        
        percentage = await tracker.get_usage_percentage(email, tier="pro")
        assert percentage == 5.0  # 500/10000 * 100

    @pytest.mark.asyncio
    async def test_monthly_reset_workflow(self, tracker):
        """Test monthly reset workflow"""
        email = "user@example.com"
        
        # 1. Create usage for current month
        tracker.table.get_item = MagicMock(return_value={})
        tracker.table.put_item = MagicMock()
        
        usage = await tracker.get_or_create_usage(email, tier="free")
        assert usage.message_count == 0
        
        # 2. Simulate reset due
        past_reset = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': email,
            'year': 2024,
            'month': 1,
            'message_count': 100,
            'tier': "free",
            'reset_at': past_reset
        }})
        
        # 3. Get usage should trigger reset
        usage = await tracker.get_usage(email)
        
        # Reset should have been called
        assert tracker.table.put_item.called

    @pytest.mark.asyncio
    async def test_usage_history_tracking(self, tracker):
        """Test tracking usage history across months"""
        email = "user@example.com"
        
        # Mock query to return multiple months
        items = [
            {
                'email': email,
                'year': 2024,
                'month': 3,
                'message_count': 150,
                'tier': "pro",
                'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            },
            {
                'email': email,
                'year': 2024,
                'month': 2,
                'message_count': 200,
                'tier': "pro",
                'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            },
            {
                'email': email,
                'year': 2024,
                'month': 1,
                'message_count': 100,
                'tier': "free",
                'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            }
        ]
        tracker.table.query = MagicMock(return_value={'Items': items})
        
        history = await tracker.get_usage_history(email, months=3)
        
        assert len(history) == 3
        assert history[0].month == 3
        assert history[1].month == 2
        assert history[2].month == 1

    @pytest.mark.asyncio
    async def test_tier_upgrade_workflow(self, tracker):
        """Test tier upgrade workflow"""
        email = "user@example.com"
        
        # 1. Start with free tier
        tracker.table.get_item = MagicMock(return_value={})
        tracker.table.put_item = MagicMock()
        
        usage = await tracker.get_or_create_usage(email, tier="free")
        assert usage.tier == "free"
        
        # 2. Increment to near limit
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': email,
            'year': 2024,
            'month': 1,
            'message_count': 95,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})
        
        remaining = await tracker.get_remaining_messages(email, tier="free")
        assert remaining == 5  # Only 5 messages left
        
        # 3. Upgrade to pro tier
        tracker.table.put_item = MagicMock()
        
        usage = await tracker.reset_usage(email, tier="pro")
        assert usage.tier == "pro"
        assert usage.message_count == 0

    @pytest.mark.asyncio
    async def test_multiple_users_isolation(self, tracker):
        """Test that multiple users are isolated"""
        user1 = "user1@example.com"
        user2 = "user2@example.com"
        
        # Create usage for user1
        tracker.table.get_item = MagicMock(return_value={})
        tracker.table.put_item = MagicMock()
        
        usage1 = await tracker.get_or_create_usage(user1, tier="free")
        assert usage1.email == user1
        
        # Create usage for user2
        usage2 = await tracker.get_or_create_usage(user2, tier="pro")
        assert usage2.email == user2
        
        # Verify they are different
        assert usage1.email != usage2.email
        assert usage1.tier != usage2.tier

    @pytest.mark.asyncio
    async def test_usage_tracking_with_increments(self, tracker):
        """Test usage tracking with multiple increments"""
        email = "user@example.com"
        
        # Create usage
        tracker.table.get_item = MagicMock(return_value={})
        tracker.table.put_item = MagicMock()
        
        await tracker.get_or_create_usage(email, tier="pro")
        
        # Increment multiple times
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': email,
            'year': 2024,
            'month': 1,
            'message_count': 0,
            'tier': "pro",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})
        tracker.table.update_item = MagicMock()
        
        # Increment by 1 ten times
        for i in range(10):
            await tracker.increment_usage(email, count=1)
        
        assert tracker.table.update_item.call_count == 10

    @pytest.mark.asyncio
    async def test_usage_percentage_thresholds(self, tracker):
        """Test usage percentage at different thresholds"""
        email = "user@example.com"
        
        # Test at 0%
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': email,
            'year': 2024,
            'month': 1,
            'message_count': 0,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})
        
        percentage = await tracker.get_usage_percentage(email, tier="free")
        assert percentage == 0.0
        
        # Test at 50%
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': email,
            'year': 2024,
            'month': 1,
            'message_count': 50,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})
        
        percentage = await tracker.get_usage_percentage(email, tier="free")
        assert percentage == 50.0
        
        # Test at 100%
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': email,
            'year': 2024,
            'month': 1,
            'message_count': 100,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})
        
        percentage = await tracker.get_usage_percentage(email, tier="free")
        assert percentage == 100.0

    @pytest.mark.asyncio
    async def test_total_usage_calculation(self, tracker):
        """Test total usage calculation across months"""
        email = "user@example.com"
        
        items = [
            {'email': email, 'message_count': 100},
            {'email': email, 'message_count': 200},
            {'email': email, 'message_count': 300},
            {'email': email, 'message_count': 400}
        ]
        tracker.table.query = MagicMock(return_value={'Items': items})
        
        total = await tracker.get_total_usage(email)
        
        assert total == 1000  # 100 + 200 + 300 + 400

    @pytest.mark.asyncio
    async def test_average_usage_calculation(self, tracker):
        """Test average usage calculation"""
        email = "user@example.com"
        
        items = [
            {'email': email, 'message_count': 100},
            {'email': email, 'message_count': 200},
            {'email': email, 'message_count': 300}
        ]
        tracker.table.query = MagicMock(return_value={'Items': items})
        
        average = await tracker.get_average_monthly_usage(email)
        
        assert average == 200.0  # (100 + 200 + 300) / 3

    @pytest.mark.asyncio
    async def test_delete_and_recreate_usage(self, tracker):
        """Test deleting and recreating usage"""
        email = "user@example.com"
        
        # Create usage
        tracker.table.get_item = MagicMock(return_value={})
        tracker.table.put_item = MagicMock()
        
        usage = await tracker.get_or_create_usage(email, tier="free")
        assert usage.message_count == 0
        
        # Delete usage
        tracker.table.delete_item = MagicMock(return_value={'Attributes': {'email': email}})
        
        result = await tracker.delete_usage(email, 2024, 1)
        assert result is True
        
        # Recreate usage
        tracker.table.get_item = MagicMock(return_value={})
        tracker.table.put_item = MagicMock()
        
        usage = await tracker.get_or_create_usage(email, tier="free")
        assert usage.message_count == 0
