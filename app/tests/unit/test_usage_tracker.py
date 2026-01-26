"""Unit tests for Usage Tracker - Test message counting and monthly tracking"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
from botocore.exceptions import ClientError

from app.billing.usage_tracker import Usage, UsageTrackerConfig, UsageTracker


@pytest.mark.unit
class TestUsageModel:
    """Tests for Usage model"""

    def test_usage_creation(self):
        """Test creating Usage instance"""
        usage = Usage(
            email="test@example.com",
            year=2024,
            month=1,
            message_count=50,
            tier="pro"
        )
        assert usage.email == "test@example.com"
        assert usage.year == 2024
        assert usage.month == 1
        assert usage.message_count == 50
        assert usage.tier == "pro"

    def test_usage_to_dict(self):
        """Test converting Usage to dictionary"""
        usage = Usage(
            email="test@example.com",
            year=2024,
            month=1,
            message_count=50,
            tier="pro"
        )
        data = usage.to_dict()
        assert data['email'] == "test@example.com"
        assert data['year'] == 2024
        assert data['month'] == 1
        assert data['message_count'] == 50
        assert data['tier'] == "pro"

    def test_usage_from_dict(self):
        """Test creating Usage from dictionary"""
        data = {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 50,
            'tier': "pro"
        }
        usage = Usage.from_dict(data)
        assert usage.email == "test@example.com"
        assert usage.year == 2024
        assert usage.month == 1
        assert usage.message_count == 50
        assert usage.tier == "pro"

    def test_usage_is_reset_due_false(self):
        """Test is_reset_due returns False when not due"""
        future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        usage = Usage(
            email="test@example.com",
            year=2024,
            month=1,
            reset_at=future_time
        )
        assert usage.is_reset_due() is False

    def test_usage_is_reset_due_true(self):
        """Test is_reset_due returns True when due"""
        past_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        usage = Usage(
            email="test@example.com",
            year=2024,
            month=1,
            reset_at=past_time
        )
        assert usage.is_reset_due() is True


@pytest.mark.unit
class TestUsageTrackerConfig:
    """Tests for UsageTrackerConfig"""

    def test_config_defaults(self):
        """Test default configuration"""
        config = UsageTrackerConfig()
        assert config.region == "us-east-1"
        assert config.usage_table == "usage"
        assert config.email_index == "email-index"

    def test_config_custom(self):
        """Test custom configuration"""
        config = UsageTrackerConfig(
            region="us-west-2",
            usage_table="custom_usage",
            email_index="custom_index"
        )
        assert config.region == "us-west-2"
        assert config.usage_table == "custom_usage"
        assert config.email_index == "custom_index"


@pytest.mark.unit
class TestUsageTrackerStaticMethods:
    """Tests for UsageTracker static methods"""

    def test_get_current_month(self):
        """Test getting current month"""
        year, month = UsageTracker._get_current_month()
        now = datetime.now(timezone.utc)
        assert year == now.year
        assert month == now.month

    def test_calculate_next_month_reset_not_december(self):
        """Test calculating next month reset (not December)"""
        with patch('app.billing.usage_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            reset_time = UsageTracker._calculate_next_month_reset()
            expected = datetime(2024, 2, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat()
            assert reset_time == expected

    def test_calculate_next_month_reset_december(self):
        """Test calculating next month reset (December)"""
        with patch('app.billing.usage_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 12, 15, 10, 30, 0, tzinfo=timezone.utc)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            reset_time = UsageTracker._calculate_next_month_reset()
            expected = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat()
            assert reset_time == expected


@pytest.mark.unit
class TestUsageTrackerValidation:
    """Tests for UsageTracker validation"""

    @pytest.fixture
    def tracker(self):
        """Create tracker with mock DynamoDB"""
        config = UsageTrackerConfig()
        tracker = UsageTracker(config)
        tracker.table = MagicMock()
        return tracker

    @pytest.mark.asyncio
    async def test_get_or_create_usage_invalid_email_no_at(self, tracker):
        """Test get_or_create_usage with invalid email (no @)"""
        with pytest.raises(ValueError, match="Invalid email format"):
            await tracker.get_or_create_usage("invalidemail")

    @pytest.mark.asyncio
    async def test_get_or_create_usage_invalid_email_empty(self, tracker):
        """Test get_or_create_usage with empty email"""
        with pytest.raises(ValueError, match="Invalid email format"):
            await tracker.get_or_create_usage("")

    @pytest.mark.asyncio
    async def test_get_or_create_usage_invalid_tier(self, tracker):
        """Test get_or_create_usage with invalid tier"""
        with pytest.raises(ValueError, match="Invalid tier"):
            await tracker.get_or_create_usage("test@example.com", tier="invalid")

    @pytest.mark.asyncio
    async def test_get_usage_invalid_email(self, tracker):
        """Test get_usage with invalid email"""
        with pytest.raises(ValueError, match="Invalid email format"):
            await tracker.get_usage("invalidemail")

    @pytest.mark.asyncio
    async def test_increment_usage_invalid_email(self, tracker):
        """Test increment_usage with invalid email"""
        with pytest.raises(ValueError, match="Invalid email format"):
            await tracker.increment_usage("invalidemail")

    @pytest.mark.asyncio
    async def test_increment_usage_invalid_count(self, tracker):
        """Test increment_usage with invalid count"""
        with pytest.raises(ValueError, match="Count must be positive"):
            await tracker.increment_usage("test@example.com", count=0)

    @pytest.mark.asyncio
    async def test_get_usage_percentage_invalid_tier(self, tracker):
        """Test get_usage_percentage with invalid tier"""
        with pytest.raises(ValueError, match="Invalid tier"):
            await tracker.get_usage_percentage("test@example.com", tier="invalid")

    @pytest.mark.asyncio
    async def test_get_remaining_messages_invalid_tier(self, tracker):
        """Test get_remaining_messages with invalid tier"""
        with pytest.raises(ValueError, match="Invalid tier"):
            await tracker.get_remaining_messages("test@example.com", tier="invalid")

    @pytest.mark.asyncio
    async def test_get_usage_history_invalid_months_zero(self, tracker):
        """Test get_usage_history with invalid months (0)"""
        with pytest.raises(ValueError, match="Months must be between 1 and 24"):
            await tracker.get_usage_history("test@example.com", months=0)

    @pytest.mark.asyncio
    async def test_get_usage_history_invalid_months_too_many(self, tracker):
        """Test get_usage_history with invalid months (> 24)"""
        with pytest.raises(ValueError, match="Months must be between 1 and 24"):
            await tracker.get_usage_history("test@example.com", months=25)

    @pytest.mark.asyncio
    async def test_delete_usage_invalid_month(self, tracker):
        """Test delete_usage with invalid month"""
        with pytest.raises(ValueError, match="Month must be between 1 and 12"):
            await tracker.delete_usage("test@example.com", 2024, 13)


@pytest.mark.unit
class TestUsageTrackerMethods:
    """Tests for UsageTracker methods"""

    @pytest.fixture
    def tracker(self):
        """Create tracker with mock DynamoDB"""
        config = UsageTrackerConfig()
        tracker = UsageTracker(config)
        tracker.table = MagicMock()
        return tracker

    @pytest.mark.asyncio
    async def test_get_or_create_usage_new(self, tracker):
        """Test creating new usage record"""
        tracker.table.get_item = MagicMock(return_value={})
        tracker.table.put_item = MagicMock()

        usage = await tracker.get_or_create_usage("test@example.com", tier="free")

        assert usage.email == "test@example.com"
        assert usage.tier == "free"
        assert usage.message_count == 0
        tracker.table.put_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_usage_existing(self, tracker):
        """Test getting existing usage record"""
        existing_usage = {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 50,
            'tier': "pro",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        tracker.table.get_item = MagicMock(return_value={'Item': existing_usage})

        usage = await tracker.get_or_create_usage("test@example.com", tier="pro")

        assert usage.email == "test@example.com"
        assert usage.message_count == 50
        assert usage.tier == "pro"

    @pytest.mark.asyncio
    async def test_get_usage_not_found(self, tracker):
        """Test getting usage when not found"""
        tracker.table.get_item = MagicMock(return_value={})

        usage = await tracker.get_usage("test@example.com")

        assert usage is None

    @pytest.mark.asyncio
    async def test_increment_usage(self, tracker):
        """Test incrementing usage"""
        existing_usage = {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 50,
            'tier': "pro",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        tracker.table.get_item = MagicMock(return_value={'Item': existing_usage})
        tracker.table.update_item = MagicMock()

        usage = await tracker.increment_usage("test@example.com", count=5)

        tracker.table.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_usage(self, tracker):
        """Test resetting usage"""
        tracker.table.put_item = MagicMock()

        usage = await tracker.reset_usage("test@example.com", tier="free")

        assert usage.email == "test@example.com"
        assert usage.message_count == 0
        assert usage.tier == "free"
        tracker.table.put_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_usage_count_zero(self, tracker):
        """Test getting usage count when zero"""
        tracker.table.get_item = MagicMock(return_value={})

        count = await tracker.get_usage_count("test@example.com")

        assert count == 0

    @pytest.mark.asyncio
    async def test_get_usage_count_with_value(self, tracker):
        """Test getting usage count with value"""
        existing_usage = {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 75,
            'tier': "pro",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        tracker.table.get_item = MagicMock(return_value={'Item': existing_usage})

        count = await tracker.get_usage_count("test@example.com")

        assert count == 75

    @pytest.mark.asyncio
    async def test_get_usage_percentage_free_tier(self, tracker):
        """Test getting usage percentage for free tier"""
        existing_usage = {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 50,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        tracker.table.get_item = MagicMock(return_value={'Item': existing_usage})

        percentage = await tracker.get_usage_percentage("test@example.com", tier="free")

        assert percentage == 50.0  # 50/100 * 100

    @pytest.mark.asyncio
    async def test_get_usage_percentage_pro_tier(self, tracker):
        """Test getting usage percentage for pro tier"""
        existing_usage = {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 5000,
            'tier': "pro",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        tracker.table.get_item = MagicMock(return_value={'Item': existing_usage})

        percentage = await tracker.get_usage_percentage("test@example.com", tier="pro")

        assert percentage == 50.0  # 5000/10000 * 100

    @pytest.mark.asyncio
    async def test_get_usage_percentage_enterprise_tier(self, tracker):
        """Test getting usage percentage for enterprise tier"""
        existing_usage = {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 1000000,
            'tier': "enterprise",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        tracker.table.get_item = MagicMock(return_value={'Item': existing_usage})

        percentage = await tracker.get_usage_percentage("test@example.com", tier="enterprise")

        assert percentage == 0.0  # Enterprise has no limit

    @pytest.mark.asyncio
    async def test_get_remaining_messages_free_tier(self, tracker):
        """Test getting remaining messages for free tier"""
        existing_usage = {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 30,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        tracker.table.get_item = MagicMock(return_value={'Item': existing_usage})

        remaining = await tracker.get_remaining_messages("test@example.com", tier="free")

        assert remaining == 70  # 100 - 30

    @pytest.mark.asyncio
    async def test_get_remaining_messages_pro_tier(self, tracker):
        """Test getting remaining messages for pro tier"""
        existing_usage = {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 3000,
            'tier': "pro",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        tracker.table.get_item = MagicMock(return_value={'Item': existing_usage})

        remaining = await tracker.get_remaining_messages("test@example.com", tier="pro")

        assert remaining == 7000  # 10000 - 3000

    @pytest.mark.asyncio
    async def test_get_remaining_messages_enterprise_tier(self, tracker):
        """Test getting remaining messages for enterprise tier"""
        existing_usage = {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 1000000,
            'tier': "enterprise",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        tracker.table.get_item = MagicMock(return_value={'Item': existing_usage})

        remaining = await tracker.get_remaining_messages("test@example.com", tier="enterprise")

        # Enterprise has unlimited messages, check it returns a very large number
        assert isinstance(remaining, int)
        assert remaining > 0

    @pytest.mark.asyncio
    async def test_get_usage_history(self, tracker):
        """Test getting usage history"""
        items = [
            {
                'email': "test@example.com",
                'year': 2024,
                'month': 1,
                'message_count': 50,
                'tier': "free",
                'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            },
            {
                'email': "test@example.com",
                'year': 2024,
                'month': 2,
                'message_count': 75,
                'tier': "free",
                'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            }
        ]
        tracker.table.query = MagicMock(return_value={'Items': items})

        history = await tracker.get_usage_history("test@example.com", months=12)

        assert len(history) == 2
        assert history[0].month == 2  # Most recent first
        assert history[1].month == 1

    @pytest.mark.asyncio
    async def test_get_total_usage(self, tracker):
        """Test getting total usage"""
        items = [
            {'email': "test@example.com", 'message_count': 50},
            {'email': "test@example.com", 'message_count': 75},
            {'email': "test@example.com", 'message_count': 100}
        ]
        tracker.table.query = MagicMock(return_value={'Items': items})

        total = await tracker.get_total_usage("test@example.com")

        assert total == 225

    @pytest.mark.asyncio
    async def test_get_average_monthly_usage(self, tracker):
        """Test getting average monthly usage"""
        items = [
            {'email': "test@example.com", 'message_count': 50},
            {'email': "test@example.com", 'message_count': 75},
            {'email': "test@example.com", 'message_count': 100}
        ]
        tracker.table.query = MagicMock(return_value={'Items': items})

        average = await tracker.get_average_monthly_usage("test@example.com")

        assert average == 75.0  # (50 + 75 + 100) / 3

    @pytest.mark.asyncio
    async def test_get_average_monthly_usage_no_data(self, tracker):
        """Test getting average monthly usage with no data"""
        tracker.table.query = MagicMock(return_value={'Items': []})

        average = await tracker.get_average_monthly_usage("test@example.com")

        assert average == 0.0

    @pytest.mark.asyncio
    async def test_delete_usage(self, tracker):
        """Test deleting usage record"""
        tracker.table.delete_item = MagicMock(return_value={'Attributes': {'email': "test@example.com"}})

        result = await tracker.delete_usage("test@example.com", 2024, 1)

        assert result is True
        tracker.table.delete_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_usage_not_found(self, tracker):
        """Test deleting usage record that doesn't exist"""
        tracker.table.delete_item = MagicMock(return_value={})

        result = await tracker.delete_usage("test@example.com", 2024, 1)

        assert result is False


@pytest.mark.unit
class TestUsageTrackerErrorHandling:
    """Tests for UsageTracker error handling"""

    @pytest.fixture
    def tracker(self):
        """Create tracker with mock DynamoDB"""
        config = UsageTrackerConfig()
        tracker = UsageTracker(config)
        tracker.table = MagicMock()
        return tracker

    @pytest.mark.asyncio
    async def test_get_or_create_usage_dynamodb_error(self, tracker):
        """Test get_or_create_usage with DynamoDB error"""
        tracker.table.get_item = MagicMock(side_effect=ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid request'}},
            'GetItem'
        ))

        with pytest.raises(ValueError, match="Failed to get or create usage"):
            await tracker.get_or_create_usage("test@example.com")

    @pytest.mark.asyncio
    async def test_get_usage_dynamodb_error(self, tracker):
        """Test get_usage with DynamoDB error"""
        tracker.table.get_item = MagicMock(side_effect=ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid request'}},
            'GetItem'
        ))

        with pytest.raises(ValueError, match="Failed to get usage"):
            await tracker.get_usage("test@example.com")

    @pytest.mark.asyncio
    async def test_increment_usage_dynamodb_error(self, tracker):
        """Test increment_usage with DynamoDB error"""
        existing_usage = {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 50,
            'tier': "pro",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        tracker.table.get_item = MagicMock(return_value={'Item': existing_usage})
        tracker.table.update_item = MagicMock(side_effect=ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid request'}},
            'UpdateItem'
        ))

        with pytest.raises(ValueError, match="Failed to increment usage"):
            await tracker.increment_usage("test@example.com")

    @pytest.mark.asyncio
    async def test_get_usage_history_dynamodb_error(self, tracker):
        """Test get_usage_history with DynamoDB error"""
        tracker.table.query = MagicMock(side_effect=ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid request'}},
            'Query'
        ))

        with pytest.raises(ValueError, match="Failed to get usage history"):
            await tracker.get_usage_history("test@example.com")

    @pytest.mark.asyncio
    async def test_get_total_usage_dynamodb_error(self, tracker):
        """Test get_total_usage with DynamoDB error"""
        tracker.table.query = MagicMock(side_effect=ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid request'}},
            'Query'
        ))

        with pytest.raises(ValueError, match="Failed to get total usage"):
            await tracker.get_total_usage("test@example.com")

    @pytest.mark.asyncio
    async def test_get_average_monthly_usage_dynamodb_error(self, tracker):
        """Test get_average_monthly_usage with DynamoDB error"""
        tracker.table.query = MagicMock(side_effect=ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid request'}},
            'Query'
        ))

        with pytest.raises(ValueError, match="Failed to get average usage"):
            await tracker.get_average_monthly_usage("test@example.com")

    @pytest.mark.asyncio
    async def test_delete_usage_dynamodb_error(self, tracker):
        """Test delete_usage with DynamoDB error"""
        tracker.table.delete_item = MagicMock(side_effect=ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid request'}},
            'DeleteItem'
        ))

        with pytest.raises(ValueError, match="Failed to delete usage"):
            await tracker.delete_usage("test@example.com", 2024, 1)
