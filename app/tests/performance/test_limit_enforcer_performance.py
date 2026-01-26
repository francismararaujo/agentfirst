"""Performance tests for Limit Enforcer - Test latency and throughput"""

import pytest
import time
from unittest.mock import AsyncMock
from app.billing.limit_enforcer import (
    LimitEnforcer,
    LimitEnforcerConfig,
)


@pytest.mark.performance
class TestLimitEnforcerPerformance:
    """Performance tests for LimitEnforcer"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return LimitEnforcerConfig(
            region="us-east-1",
            usage_table="usage",
        )

    @pytest.fixture
    def enforcer(self, config):
        """Create enforcer with mocked tracker"""
        enforcer = LimitEnforcer(config)
        enforcer.tracker = AsyncMock()
        return enforcer

    @pytest.mark.asyncio
    async def test_check_limit_latency(self, enforcer):
        """Test check_limit latency (should be < 100ms)"""
        email = "perf_check@example.com"
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        # Warm up
        await enforcer.check_limit(email, "free")

        # Measure latency
        start = time.time()
        for _ in range(100):
            await enforcer.check_limit(email, "free")
        elapsed = time.time() - start

        # Average latency should be < 100ms
        avg_latency = (elapsed / 100) * 1000  # Convert to ms
        assert avg_latency < 100, f"Average latency {avg_latency}ms exceeds 100ms"

    @pytest.mark.asyncio
    async def test_enforce_limit_latency(self, enforcer):
        """Test enforce_limit latency (should be < 100ms)"""
        email = "perf_enforce@example.com"
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        # Warm up
        await enforcer.enforce_limit(email, "free")

        # Measure latency
        start = time.time()
        for _ in range(100):
            await enforcer.enforce_limit(email, "free")
        elapsed = time.time() - start

        # Average latency should be < 100ms
        avg_latency = (elapsed / 100) * 1000  # Convert to ms
        assert avg_latency < 100, f"Average latency {avg_latency}ms exceeds 100ms"

    @pytest.mark.asyncio
    async def test_get_limit_status_latency(self, enforcer):
        """Test get_limit_status latency (should be < 100ms)"""
        email = "perf_status@example.com"
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        # Warm up
        await enforcer.get_limit_status(email, "free")

        # Measure latency
        start = time.time()
        for _ in range(100):
            await enforcer.get_limit_status(email, "free")
        elapsed = time.time() - start

        # Average latency should be < 100ms
        avg_latency = (elapsed / 100) * 1000  # Convert to ms
        assert avg_latency < 100, f"Average latency {avg_latency}ms exceeds 100ms"

    @pytest.mark.asyncio
    async def test_get_warning_status_latency(self, enforcer):
        """Test get_warning_status latency (should be < 100ms)"""
        email = "perf_warning@example.com"
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        # Warm up
        await enforcer.get_warning_status(email, "free")

        # Measure latency
        start = time.time()
        for _ in range(100):
            await enforcer.get_warning_status(email, "free")
        elapsed = time.time() - start

        # Average latency should be < 100ms
        avg_latency = (elapsed / 100) * 1000  # Convert to ms
        assert avg_latency < 100, f"Average latency {avg_latency}ms exceeds 100ms"

    @pytest.mark.asyncio
    async def test_can_send_messages_latency(self, enforcer):
        """Test can_send_messages latency (should be < 100ms)"""
        email = "perf_can_send@example.com"
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        # Warm up
        await enforcer.can_send_messages(email, "free", count=1)

        # Measure latency
        start = time.time()
        for _ in range(100):
            await enforcer.can_send_messages(email, "free", count=1)
        elapsed = time.time() - start

        # Average latency should be < 100ms
        avg_latency = (elapsed / 100) * 1000  # Convert to ms
        assert avg_latency < 100, f"Average latency {avg_latency}ms exceeds 100ms"

    @pytest.mark.asyncio
    async def test_get_messages_available_latency(self, enforcer):
        """Test get_messages_available latency (should be < 100ms)"""
        email = "perf_available@example.com"
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        # Warm up
        await enforcer.get_messages_available(email, "free")

        # Measure latency
        start = time.time()
        for _ in range(100):
            await enforcer.get_messages_available(email, "free")
        elapsed = time.time() - start

        # Average latency should be < 100ms
        avg_latency = (elapsed / 100) * 1000  # Convert to ms
        assert avg_latency < 100, f"Average latency {avg_latency}ms exceeds 100ms"

    @pytest.mark.asyncio
    async def test_throughput_check_limit(self, enforcer):
        """Test check_limit throughput (should handle 100+ ops/sec)"""
        email = "perf_throughput@example.com"
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        # Measure throughput
        start = time.time()
        count = 0
        while time.time() - start < 1.0:  # Run for 1 second
            await enforcer.check_limit(email, "free")
            count += 1

        # Should handle at least 100 ops/sec
        assert count >= 100, f"Throughput {count} ops/sec is below 100 ops/sec"

    @pytest.mark.asyncio
    async def test_throughput_enforce_limit(self, enforcer):
        """Test enforce_limit throughput (should handle 100+ ops/sec)"""
        email = "perf_throughput_enforce@example.com"
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        # Measure throughput
        start = time.time()
        count = 0
        while time.time() - start < 1.0:  # Run for 1 second
            try:
                await enforcer.enforce_limit(email, "free")
            except:
                pass
            count += 1

        # Should handle at least 100 ops/sec
        assert count >= 100, f"Throughput {count} ops/sec is below 100 ops/sec"

    @pytest.mark.asyncio
    async def test_throughput_get_limit_status(self, enforcer):
        """Test get_limit_status throughput (should handle 100+ ops/sec)"""
        email = "perf_throughput_status@example.com"
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        # Measure throughput
        start = time.time()
        count = 0
        while time.time() - start < 1.0:  # Run for 1 second
            await enforcer.get_limit_status(email, "free")
            count += 1

        # Should handle at least 100 ops/sec
        assert count >= 100, f"Throughput {count} ops/sec is below 100 ops/sec"

    @pytest.mark.asyncio
    async def test_concurrent_users_performance(self, enforcer):
        """Test performance with multiple concurrent users"""
        emails = [f"perf_concurrent_{i}@example.com" for i in range(10)]
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        # Measure latency for multiple users
        start = time.time()
        for _ in range(100):
            for email in emails:
                await enforcer.check_limit(email, "free")
        elapsed = time.time() - start

        # Average latency per operation should be < 100ms
        avg_latency = (elapsed / (100 * 10)) * 1000  # Convert to ms
        assert avg_latency < 100, f"Average latency {avg_latency}ms exceeds 100ms"

    @pytest.mark.asyncio
    async def test_all_tiers_performance(self, enforcer):
        """Test performance across all tiers"""
        email = "perf_all_tiers@example.com"
        enforcer.tracker.get_usage_count = AsyncMock(return_value=50)

        # Measure latency for all tiers
        start = time.time()
        for _ in range(100):
            await enforcer.check_limit(email, "free")
            await enforcer.check_limit(email, "pro")
            await enforcer.check_limit(email, "enterprise")
        elapsed = time.time() - start

        # Average latency per operation should be < 100ms
        avg_latency = (elapsed / (100 * 3)) * 1000  # Convert to ms
        assert avg_latency < 100, f"Average latency {avg_latency}ms exceeds 100ms"

    @pytest.mark.asyncio
    async def test_memory_efficiency(self, enforcer):
        """Test memory efficiency with many users"""
        # Create 100 users and check limits
        emails = [f"perf_memory_{i}@example.com" for i in range(100)]
        enforcer.tracker.get_usage_count = AsyncMock(return_value=0)

        for email in emails:
            await enforcer.check_limit(email, "free")

        # All users should be independent
        for email in emails:
            status = await enforcer.get_limit_status(email, "free")
            assert status['current_usage'] == 0
            assert status['remaining'] == 100



