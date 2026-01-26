"""Performance tests for Session Manager Service"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from app.omnichannel.authentication import (
    SessionManager,
    SessionConfig,
)


@pytest.mark.performance
class TestSessionManagerLatency:
    """Performance tests for session manager latency"""

    @pytest.fixture
    def config(self):
        """Create config"""
        return SessionConfig()

    @pytest.fixture
    def manager(self, config):
        """Create manager"""
        with patch("boto3.resource"):
            return SessionManager(config)

    @pytest.mark.asyncio
    async def test_create_session_latency(self, manager):
        """Test that create_session completes within SLA"""
        manager.table.put_item = MagicMock()

        start = time.time()
        await manager.create_session("user@example.com", "telegram", "123456")
        elapsed = time.time() - start

        # Should complete in < 100ms
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_get_session_latency(self, manager):
        """Test that get_session completes within SLA"""
        future_expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        manager.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "session_id": "session-123",
                    "email": "user@example.com",
                    "channel": "telegram",
                    "channel_id": "123456",
                    "created_at": "2024-01-01T10:00:00+00:00",
                    "updated_at": "2024-01-01T10:00:00+00:00",
                    "expires_at": future_expires,
                    "context": {},
                    "metadata": {},
                }
            }
        )

        start = time.time()
        await manager.get_session("session-123")
        elapsed = time.time() - start

        # Should complete in < 100ms
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_get_session_by_email_latency(self, manager):
        """Test that get_session_by_email completes within SLA"""
        future_expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        manager.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "session_id": "session-123",
                        "email": "user@example.com",
                        "channel": "telegram",
                        "channel_id": "123456",
                        "created_at": "2024-01-01T10:00:00+00:00",
                        "updated_at": "2024-01-01T10:00:00+00:00",
                        "expires_at": future_expires,
                        "context": {},
                        "metadata": {},
                    }
                ]
            }
        )

        start = time.time()
        await manager.get_session_by_email("user@example.com")
        elapsed = time.time() - start

        # Should complete in < 100ms
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_get_all_sessions_for_email_latency(self, manager):
        """Test that get_all_sessions_for_email completes within SLA"""
        future_expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        manager.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "session_id": f"session-{i}",
                        "email": "user@example.com",
                        "channel": f"channel-{i}",
                        "channel_id": str(100000 + i),
                        "created_at": "2024-01-01T10:00:00+00:00",
                        "updated_at": "2024-01-01T10:00:00+00:00",
                        "expires_at": future_expires,
                        "context": {},
                        "metadata": {},
                    }
                    for i in range(10)
                ]
            }
        )

        start = time.time()
        await manager.get_all_sessions_for_email("user@example.com")
        elapsed = time.time() - start

        # Should complete in < 100ms
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_update_session_latency(self, manager):
        """Test that update_session completes within SLA"""
        future_expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        manager.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "session_id": "session-123",
                    "email": "user@example.com",
                    "channel": "telegram",
                    "channel_id": "123456",
                    "created_at": "2024-01-01T10:00:00+00:00",
                    "updated_at": "2024-01-01T10:00:00+00:00",
                    "expires_at": future_expires,
                    "context": {},
                    "metadata": {},
                }
            }
        )
        manager.table.update_item = MagicMock()

        start = time.time()
        await manager.update_session("session-123", context={"key": "value"})
        elapsed = time.time() - start

        # Should complete in < 100ms
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_validate_session_latency(self, manager):
        """Test that validate_session completes within SLA"""
        future_expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        manager.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "session_id": "session-123",
                    "email": "user@example.com",
                    "channel": "telegram",
                    "channel_id": "123456",
                    "created_at": "2024-01-01T10:00:00+00:00",
                    "updated_at": "2024-01-01T10:00:00+00:00",
                    "expires_at": future_expires,
                    "context": {},
                    "metadata": {},
                }
            }
        )

        start = time.time()
        await manager.validate_session("session-123")
        elapsed = time.time() - start

        # Should complete in < 100ms
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_extend_session_latency(self, manager):
        """Test that extend_session completes within SLA"""
        future_expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        manager.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "session_id": "session-123",
                    "email": "user@example.com",
                    "channel": "telegram",
                    "channel_id": "123456",
                    "created_at": "2024-01-01T10:00:00+00:00",
                    "updated_at": "2024-01-01T10:00:00+00:00",
                    "expires_at": future_expires,
                    "context": {},
                    "metadata": {},
                }
            }
        )
        manager.table.update_item = MagicMock()

        start = time.time()
        await manager.extend_session("session-123")
        elapsed = time.time() - start

        # Should complete in < 100ms
        assert elapsed < 0.1


@pytest.mark.performance
class TestSessionManagerThroughput:
    """Performance tests for session manager throughput"""

    @pytest.fixture
    def config(self):
        """Create config"""
        return SessionConfig()

    @pytest.fixture
    def manager(self, config):
        """Create manager"""
        with patch("boto3.resource"):
            return SessionManager(config)

    @pytest.mark.asyncio
    async def test_create_multiple_sessions_throughput(self, manager):
        """Test creating multiple sessions"""
        manager.table.put_item = MagicMock()

        start = time.time()
        for i in range(10):
            await manager.create_session(
                f"user{i}@example.com", "telegram", str(100000 + i)
            )
        elapsed = time.time() - start

        # Should create 10 sessions in < 1 second
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_get_sessions_throughput(self, manager):
        """Test getting multiple sessions"""
        future_expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        manager.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "session_id": f"session-{i}",
                        "email": "user@example.com",
                        "channel": f"channel-{i}",
                        "channel_id": str(100000 + i),
                        "created_at": "2024-01-01T10:00:00+00:00",
                        "updated_at": "2024-01-01T10:00:00+00:00",
                        "expires_at": future_expires,
                        "context": {},
                        "metadata": {},
                    }
                    for i in range(10)
                ]
            }
        )

        start = time.time()
        for _ in range(10):
            await manager.get_all_sessions_for_email("user@example.com")
        elapsed = time.time() - start

        # Should get 10 times in < 1 second
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_session_id_generation_throughput(self):
        """Test session ID generation throughput"""
        start = time.time()
        for _ in range(1000):
            SessionManager._generate_session_id()
        elapsed = time.time() - start

        # Should generate 1000 IDs in < 1 second
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_ttl_calculation_throughput(self):
        """Test TTL calculation throughput"""
        start = time.time()
        for _ in range(1000):
            SessionManager._calculate_ttl()
        elapsed = time.time() - start

        # Should calculate 1000 TTLs in < 1 second
        assert elapsed < 1.0


@pytest.mark.performance
class TestSessionManagerMemory:
    """Performance tests for session manager memory usage"""

    @pytest.fixture
    def config(self):
        """Create config"""
        return SessionConfig()

    @pytest.fixture
    def manager(self, config):
        """Create manager"""
        with patch("boto3.resource"):
            return SessionManager(config)

    @pytest.mark.asyncio
    async def test_large_context_handling(self, manager):
        """Test handling large context"""
        manager.table.put_item = MagicMock()

        # Create session with large context
        large_context = {f"key_{i}": f"value_{i}" * 100 for i in range(100)}

        session = await manager.create_session(
            "user@example.com",
            "telegram",
            "123456",
            context=large_context,
        )

        assert len(session.context) == 100
        manager.table.put_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_many_sessions_per_user(self, manager):
        """Test handling many sessions per user"""
        future_expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        manager.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "session_id": f"session-{i}",
                        "email": "user@example.com",
                        "channel": f"channel-{i}",
                        "channel_id": str(100000 + i),
                        "created_at": "2024-01-01T10:00:00+00:00",
                        "updated_at": "2024-01-01T10:00:00+00:00",
                        "expires_at": future_expires,
                        "context": {},
                        "metadata": {},
                    }
                    for i in range(50)
                ]
            }
        )

        sessions = await manager.get_all_sessions_for_email("user@example.com")

        assert len(sessions) == 50
