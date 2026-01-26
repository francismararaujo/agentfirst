"""Performance tests for DynamoDB repositories - Test latency and throughput"""

import pytest
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.omnichannel.database.models import (
    User, Session, Memory, Usage, AuditLog, Escalation,
    UserTier
)
from app.omnichannel.database.repositories import (
    UserRepository, SessionRepository, MemoryRepository,
    UsageRepository, AuditLogRepository, EscalationRepository
)


@pytest.mark.performance
class TestUserRepositoryPerformance:
    """Performance tests for UserRepository"""

    @pytest.fixture
    def repo(self):
        return UserRepository()

    @pytest.mark.asyncio
    async def test_create_user_latency(self, repo):
        """Test that creating a user completes within SLA (< 100ms)"""
        user = User(
            email="test@example.com",
            tier=UserTier.FREE,
            telegram_id=123456789
        )
        
        mock_table = MagicMock()
        
        with patch.object(repo, 'get_table', return_value=mock_table):
            start = time.time()
            await repo.create(user)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            # Should complete in less than 100ms
            assert elapsed < 100, f"Create user took {elapsed}ms, expected < 100ms"

    @pytest.mark.asyncio
    async def test_get_user_latency(self, repo):
        """Test that getting a user completes within SLA (< 50ms)"""
        user = User(
            email="test@example.com",
            tier=UserTier.FREE,
            telegram_id=123456789
        )
        
        mock_table = MagicMock()
        mock_table.get_item.return_value = {'Item': user.to_dynamodb()}
        
        with patch.object(repo, 'get_table', return_value=mock_table):
            start = time.time()
            await repo.get_by_email("test@example.com")
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            # Should complete in less than 50ms
            assert elapsed < 50, f"Get user took {elapsed}ms, expected < 50ms"

    @pytest.mark.asyncio
    async def test_update_user_latency(self, repo):
        """Test that updating a user completes within SLA (< 100ms)"""
        updated_user = User(
            email="test@example.com",
            tier=UserTier.PRO,
            telegram_id=123456789
        )
        
        mock_table = MagicMock()
        mock_table.update_item.return_value = {'Attributes': updated_user.to_dynamodb()}
        
        with patch.object(repo, 'get_table', return_value=mock_table):
            start = time.time()
            await repo.update("test@example.com", {'tier': 'pro'})
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            # Should complete in less than 100ms
            assert elapsed < 100, f"Update user took {elapsed}ms, expected < 100ms"


@pytest.mark.performance
class TestMemoryRepositoryPerformance:
    """Performance tests for MemoryRepository"""

    @pytest.fixture
    def repo(self):
        return MemoryRepository()

    @pytest.mark.asyncio
    async def test_create_memory_latency(self, repo):
        """Test that creating memory completes within SLA (< 100ms)"""
        memory = Memory(
            email="test@example.com",
            domain="retail",
            context={"last_intent": "check_orders", "connector": "ifood"}
        )
        
        mock_table = MagicMock()
        
        with patch.object(repo, 'get_table', return_value=mock_table):
            start = time.time()
            await repo.create(memory)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            # Should complete in less than 100ms
            assert elapsed < 100, f"Create memory took {elapsed}ms, expected < 100ms"

    @pytest.mark.asyncio
    async def test_get_memory_by_domain_latency(self, repo):
        """Test that getting memory by domain completes within SLA (< 50ms)"""
        memory = Memory(
            email="test@example.com",
            domain="retail",
            context={"last_intent": "check_orders", "connector": "ifood"}
        )
        
        mock_table = MagicMock()
        mock_table.get_item.return_value = {'Item': memory.to_dynamodb()}
        
        with patch.object(repo, 'get_table', return_value=mock_table):
            start = time.time()
            await repo.get_by_email_and_domain("test@example.com", "retail")
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            # Should complete in less than 50ms
            assert elapsed < 50, f"Get memory took {elapsed}ms, expected < 50ms"


@pytest.mark.performance
class TestUsageRepositoryPerformance:
    """Performance tests for UsageRepository"""

    @pytest.fixture
    def repo(self):
        return UsageRepository()

    @pytest.mark.asyncio
    async def test_increment_message_count_latency(self, repo):
        """Test that incrementing message count completes within SLA (< 100ms)"""
        updated_usage = Usage(
            email="test@example.com",
            year=2025,
            month=1,
            message_count=6,
            tier=UserTier.FREE
        )
        
        mock_table = MagicMock()
        mock_table.update_item.return_value = {'Attributes': updated_usage.to_dynamodb()}
        
        with patch.object(repo, 'get_table', return_value=mock_table):
            start = time.time()
            await repo.increment_message_count("test@example.com", 2025, 1)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            # Should complete in less than 100ms
            assert elapsed < 100, f"Increment message count took {elapsed}ms, expected < 100ms"


@pytest.mark.performance
class TestAuditLogRepositoryPerformance:
    """Performance tests for AuditLogRepository"""

    @pytest.fixture
    def repo(self):
        return AuditLogRepository()

    @pytest.mark.asyncio
    async def test_create_audit_log_latency(self, repo):
        """Test that creating audit log completes within SLA (< 100ms)"""
        audit_log = AuditLog(
            email="test@example.com",
            timestamp=datetime.utcnow().isoformat(),
            action_id="action_123",
            agent="retail_agent",
            action="check_orders",
            input_data={"connector": "ifood"},
            output_data={"orders": [1, 2, 3]},
            status="success"
        )
        
        mock_table = MagicMock()
        
        with patch.object(repo, 'get_table', return_value=mock_table):
            start = time.time()
            await repo.create(audit_log)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            # Should complete in less than 100ms
            assert elapsed < 100, f"Create audit log took {elapsed}ms, expected < 100ms"
