"""Performance tests for Usage Tracker - Test latency, throughput, and memory"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from app.billing.usage_tracker import Usage, UsageTrackerConfig, UsageTracker


@pytest.mark.performance
class TestUsageTrackerLatency:
    """Tests for Usage Tracker latency"""

    @pytest.fixture
    def tracker(self):
        """Create tracker with mock DynamoDB"""
        config = UsageTrackerConfig()
        tracker = UsageTracker(config)
        tracker.table = MagicMock()
        return tracker

    @pytest.mark.asyncio
    async def test_get_or_create_usage_latency(self, tracker):
        """Test get_or_create_usage latency < 100ms"""
        tracker.table.get_item = MagicMock(return_value={})
        tracker.table.put_item = MagicMock()

        start = time.time()
        await tracker.get_or_create_usage("test@example.com", tier="free")
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert elapsed < 100, f"get_or_create_usage took {elapsed}ms (expected < 100ms)"

    @pytest.mark.asyncio
    async def test_get_usage_latency(self, tracker):
        """Test get_usage latency < 50ms"""
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 50,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})

        start = time.time()
        await tracker.get_usage("test@example.com")
        elapsed = (time.time() - start) * 1000

        assert elapsed < 50, f"get_usage took {elapsed}ms (expected < 50ms)"

    @pytest.mark.asyncio
    async def test_increment_usage_latency(self, tracker):
        """Test increment_usage latency < 100ms"""
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 50,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})
        tracker.table.update_item = MagicMock()

        start = time.time()
        await tracker.increment_usage("test@example.com", count=1)
        elapsed = (time.time() - start) * 1000

        assert elapsed < 100, f"increment_usage took {elapsed}ms (expected < 100ms)"

    @pytest.mark.asyncio
    async def test_get_usage_count_latency(self, tracker):
        """Test get_usage_count latency < 50ms"""
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 50,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})

        start = time.time()
        await tracker.get_usage_count("test@example.com")
        elapsed = (time.time() - start) * 1000

        assert elapsed < 50, f"get_usage_count took {elapsed}ms (expected < 50ms)"

    @pytest.mark.asyncio
    async def test_get_usage_percentage_latency(self, tracker):
        """Test get_usage_percentage latency < 50ms"""
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 50,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})

        start = time.time()
        await tracker.get_usage_percentage("test@example.com", tier="free")
        elapsed = (time.time() - start) * 1000

        assert elapsed < 50, f"get_usage_percentage took {elapsed}ms (expected < 50ms)"

    @pytest.mark.asyncio
    async def test_get_remaining_messages_latency(self, tracker):
        """Test get_remaining_messages latency < 50ms"""
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 50,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})

        start = time.time()
        await tracker.get_remaining_messages("test@example.com", tier="free")
        elapsed = (time.time() - start) * 1000

        assert elapsed < 50, f"get_remaining_messages took {elapsed}ms (expected < 50ms)"

    @pytest.mark.asyncio
    async def test_get_usage_history_latency(self, tracker):
        """Test get_usage_history latency < 200ms"""
        items = [
            {
                'email': "test@example.com",
                'year': 2024,
                'month': i,
                'message_count': i * 10,
                'tier': "pro",
                'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            }
            for i in range(1, 13)
        ]
        tracker.table.query = MagicMock(return_value={'Items': items})

        start = time.time()
        await tracker.get_usage_history("test@example.com", months=12)
        elapsed = (time.time() - start) * 1000

        assert elapsed < 200, f"get_usage_history took {elapsed}ms (expected < 200ms)"

    @pytest.mark.asyncio
    async def test_get_total_usage_latency(self, tracker):
        """Test get_total_usage latency < 200ms"""
        items = [{'email': "test@example.com", 'message_count': i * 10} for i in range(12)]
        tracker.table.query = MagicMock(return_value={'Items': items})

        start = time.time()
        await tracker.get_total_usage("test@example.com")
        elapsed = (time.time() - start) * 1000

        assert elapsed < 200, f"get_total_usage took {elapsed}ms (expected < 200ms)"

    @pytest.mark.asyncio
    async def test_get_average_monthly_usage_latency(self, tracker):
        """Test get_average_monthly_usage latency < 200ms"""
        items = [{'email': "test@example.com", 'message_count': i * 10} for i in range(12)]
        tracker.table.query = MagicMock(return_value={'Items': items})

        start = time.time()
        await tracker.get_average_monthly_usage("test@example.com")
        elapsed = (time.time() - start) * 1000

        assert elapsed < 200, f"get_average_monthly_usage took {elapsed}ms (expected < 200ms)"


@pytest.mark.performance
class TestUsageTrackerThroughput:
    """Tests for Usage Tracker throughput"""

    @pytest.fixture
    def tracker(self):
        """Create tracker with mock DynamoDB"""
        config = UsageTrackerConfig()
        tracker = UsageTracker(config)
        tracker.table = MagicMock()
        return tracker

    @pytest.mark.asyncio
    async def test_increment_usage_throughput(self, tracker):
        """Test increment_usage throughput (100+ ops/sec)"""
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 0,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})
        tracker.table.update_item = MagicMock()

        start = time.time()
        for i in range(100):
            await tracker.increment_usage("test@example.com", count=1)
        elapsed = time.time() - start

        throughput = 100 / elapsed
        assert throughput > 100, f"Throughput {throughput} ops/sec (expected > 100)"

    @pytest.mark.asyncio
    async def test_get_usage_throughput(self, tracker):
        """Test get_usage throughput (200+ ops/sec)"""
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 50,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})

        start = time.time()
        for i in range(100):
            await tracker.get_usage("test@example.com")
        elapsed = time.time() - start

        throughput = 100 / elapsed
        assert throughput > 200, f"Throughput {throughput} ops/sec (expected > 200)"

    @pytest.mark.asyncio
    async def test_get_usage_count_throughput(self, tracker):
        """Test get_usage_count throughput (200+ ops/sec)"""
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 50,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})

        start = time.time()
        for i in range(100):
            await tracker.get_usage_count("test@example.com")
        elapsed = time.time() - start

        throughput = 100 / elapsed
        assert throughput > 200, f"Throughput {throughput} ops/sec (expected > 200)"

    @pytest.mark.asyncio
    async def test_multiple_users_throughput(self, tracker):
        """Test throughput with multiple users"""
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 50,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})

        start = time.time()
        for i in range(50):
            email = f"user{i}@example.com"
            await tracker.get_usage(email)
        elapsed = time.time() - start

        throughput = 50 / elapsed
        assert throughput > 100, f"Throughput {throughput} ops/sec (expected > 100)"


@pytest.mark.performance
class TestUsageTrackerMemory:
    """Tests for Usage Tracker memory usage"""

    @pytest.fixture
    def tracker(self, mock_dynamodb):
        """Create tracker with mock DynamoDB"""
        config = UsageTrackerConfig()
        tracker = UsageTracker(config)
        tracker.table = mock_dynamodb
        return tracker

    def test_usage_model_memory(self):
        """Test Usage model memory footprint"""
        usage = Usage(
            email="test@example.com",
            year=2024,
            month=1,
            message_count=50,
            tier="pro"
        )
        
        # Usage object should be small (< 1KB)
        import sys
        size = sys.getsizeof(usage)
        assert size < 1024, f"Usage object size {size} bytes (expected < 1024)"

    def test_usage_dict_memory(self):
        """Test Usage dict memory footprint"""
        usage = Usage(
            email="test@example.com",
            year=2024,
            month=1,
            message_count=50,
            tier="pro"
        )
        data = usage.to_dict()
        
        # Dict should be small (< 2KB)
        import sys
        size = sys.getsizeof(data)
        assert size < 2048, f"Usage dict size {size} bytes (expected < 2048)"

    def test_usage_history_memory(self):
        """Test usage history memory with large dataset"""
        items = [
            {
                'email': "test@example.com",
                'year': 2024,
                'month': i,
                'message_count': i * 100,
                'tier': "pro",
                'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            }
            for i in range(1, 13)
        ]
        
        # History list should be reasonable size
        import sys
        history = [Usage.from_dict(item) for item in items]
        size = sys.getsizeof(history)
        assert size < 10240, f"History list size {size} bytes (expected < 10KB)"

    def test_large_message_count_handling(self):
        """Test handling of large message counts"""
        usage = Usage(
            email="test@example.com",
            year=2024,
            month=1,
            message_count=999999999,  # Very large number
            tier="enterprise"
        )
        assert usage.message_count == 999999999


@pytest.mark.performance
class TestUsageTrackerScalability:
    """Tests for Usage Tracker scalability"""

    @pytest.fixture
    def tracker(self):
        """Create tracker with mock DynamoDB"""
        config = UsageTrackerConfig()
        tracker = UsageTracker(config)
        tracker.table = MagicMock()
        return tracker

    @pytest.mark.asyncio
    async def test_many_users_concurrent_access(self, tracker):
        """Test handling many users"""
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 50,
            'tier': "free",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})

        # Simulate 1000 users
        start = time.time()
        for i in range(1000):
            email = f"user{i}@example.com"
            await tracker.get_usage(email)
        elapsed = time.time() - start

        # Should complete in reasonable time (< 10 seconds)
        assert elapsed < 10, f"1000 users took {elapsed}s (expected < 10s)"

    @pytest.mark.asyncio
    async def test_large_history_query(self, tracker):
        """Test querying large history"""
        # Simulate 24 months of history
        items = [
            {
                'email': "test@example.com",
                'year': 2024 if i < 12 else 2025,
                'month': (i % 12) + 1,
                'message_count': i * 100,
                'tier': "pro",
                'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            }
            for i in range(24)
        ]
        tracker.table.query = MagicMock(return_value={'Items': items})

        start = time.time()
        history = await tracker.get_usage_history("test@example.com", months=24)
        elapsed = time.time() - start

        assert len(history) == 24
        assert elapsed < 1, f"24 months query took {elapsed}s (expected < 1s)"

    @pytest.mark.asyncio
    async def test_batch_increment_performance(self, tracker):
        """Test batch increment performance"""
        tracker.table.get_item = MagicMock(return_value={'Item': {
            'email': "test@example.com",
            'year': 2024,
            'month': 1,
            'message_count': 0,
            'tier': "pro",
            'reset_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }})
        tracker.table.update_item = MagicMock()

        start = time.time()
        # Simulate 500 increments
        for i in range(500):
            await tracker.increment_usage("test@example.com", count=1)
        elapsed = time.time() - start

        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5, f"500 increments took {elapsed}s (expected < 5s)"
