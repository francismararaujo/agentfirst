"""Performance tests for Billing Manager"""

import pytest
import time
from unittest.mock import AsyncMock
from app.billing.billing_manager import BillingManager
from app.billing.usage_tracker import Usage


@pytest.mark.performance
class TestBillingManagerLatency:
    """Tests for billing manager latency"""

    @pytest.mark.asyncio
    async def test_get_billing_info_latency(self):
        """Test get_billing_info latency"""
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

        start = time.time()
        for _ in range(100):
            await manager.get_billing_info("test@example.com")
        elapsed = time.time() - start

        assert elapsed < 0.5

    @pytest.mark.asyncio
    async def test_check_tier_and_limits_latency(self):
        """Test check_tier_and_limits latency"""
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

        start = time.time()
        for _ in range(100):
            await manager.check_tier_and_limits("test@example.com")
        elapsed = time.time() - start

        assert elapsed < 0.5

    @pytest.mark.asyncio
    async def test_generate_upgrade_link_latency(self):
        """Test generate_upgrade_link latency"""
        usage_tracker = AsyncMock()
        limit_enforcer = AsyncMock()

        usage_tracker.get_user_tier.return_value = "free"

        manager = BillingManager(usage_tracker, limit_enforcer)

        start = time.time()
        for _ in range(100):
            await manager.generate_upgrade_link("test@example.com", "pro")
        elapsed = time.time() - start

        assert elapsed < 0.5

    @pytest.mark.asyncio
    async def test_update_tier_after_payment_latency(self):
        """Test update_tier_after_payment latency"""
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

        start = time.time()
        for i in range(10):
            await manager.update_tier_after_payment(
                "test@example.com", "pro", f"payment_{i}"
            )
        elapsed = time.time() - start

        assert elapsed < 0.5


@pytest.mark.performance
class TestBillingManagerThroughput:
    """Tests for billing manager throughput"""

    @pytest.mark.asyncio
    async def test_get_billing_info_throughput(self):
        """Test get_billing_info throughput"""
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

        start = time.time()
        count = 0
        while time.time() - start < 1.0:
            await manager.get_billing_info("test@example.com")
            count += 1

        assert count > 100

    @pytest.mark.asyncio
    async def test_check_tier_and_limits_throughput(self):
        """Test check_tier_and_limits throughput"""
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

        start = time.time()
        count = 0
        while time.time() - start < 1.0:
            await manager.check_tier_and_limits("test@example.com")
            count += 1

        assert count > 100


@pytest.mark.performance
class TestBillingManagerScalability:
    """Tests for billing manager scalability"""

    @pytest.mark.asyncio
    async def test_multiple_users_scalability(self):
        """Test scalability with multiple users"""
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

        start = time.time()
        for i in range(100):
            email = f"user{i}@example.com"
            await manager.get_billing_info(email)
        elapsed = time.time() - start

        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_concurrent_operations_scalability(self):
        """Test scalability with concurrent operations"""
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

        start = time.time()
        for _ in range(50):
            await manager.get_billing_info("test@example.com")
            await manager.check_tier_and_limits("test@example.com")
        elapsed = time.time() - start

        assert elapsed < 1.0
