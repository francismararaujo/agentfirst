"""Unit tests for DynamoDB repositories - Test individual repository methods in isolation"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from hypothesis import given, strategies as st

from app.omnichannel.database.models import (
    User, Session, Memory, Usage, AuditLog, Escalation,
    UserTier
)
from app.omnichannel.database.repositories import (
    UserRepository, SessionRepository, MemoryRepository,
    UsageRepository, AuditLogRepository, EscalationRepository
)


# ============================================================================
# UNIT TESTS - UserRepository
# ============================================================================

@pytest.mark.unit
class TestUserRepository:
    """Tests for UserRepository"""

    @pytest.fixture
    def repo(self):
        """Create repository instance"""
        return UserRepository()

    @pytest.fixture
    def sample_user(self):
        """Create sample user"""
        return User(
            email="test@example.com",
            tier=UserTier.FREE,
            telegram_id=123456789
        )

    @pytest.mark.asyncio
    async def test_create_user(self, repo, sample_user):
        """Test creating a user"""
        mock_table = MagicMock()
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.create(sample_user)
            assert result.email == sample_user.email
            assert result.tier == UserTier.FREE
            mock_table.put_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, repo, sample_user):
        """Test getting user by email"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {'Item': sample_user.to_dynamodb()}
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.get_by_email("test@example.com")
            assert result is not None
            assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, repo):
        """Test getting non-existent user"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.get_by_email("nonexistent@example.com")
            assert result is None

    @pytest.mark.asyncio
    async def test_update_user(self, repo):
        """Test updating user"""
        mock_table = MagicMock()
        updated_user = User(
            email="test@example.com",
            tier=UserTier.PRO,
            telegram_id=123456789
        )
        mock_table.update_item.return_value = {'Attributes': updated_user.to_dynamodb()}
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.update("test@example.com", {'tier': 'pro'})
            assert result.tier == UserTier.PRO

    @pytest.mark.asyncio
    async def test_delete_user(self, repo):
        """Test deleting user"""
        mock_table = MagicMock()
        with patch.object(repo, 'get_table', return_value=mock_table):
            await repo.delete("test@example.com")
            mock_table.delete_item.assert_called_once()


# ============================================================================
# UNIT TESTS - SessionRepository
# ============================================================================

@pytest.mark.unit
class TestSessionRepository:
    """Tests for SessionRepository"""

    @pytest.fixture
    def repo(self):
        """Create repository instance"""
        return SessionRepository()

    @pytest.fixture
    def sample_session(self):
        """Create sample session"""
        return Session(
            email="test@example.com",
            session_id="sess_123456",
            authenticated=True,
            active_channels=["telegram"]
        )

    @pytest.mark.asyncio
    async def test_create_session(self, repo, sample_session):
        """Test creating a session"""
        mock_table = MagicMock()
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.create(sample_session)
            assert result.email == sample_session.email
            assert result.session_id == sample_session.session_id

    @pytest.mark.asyncio
    async def test_get_session_by_email(self, repo, sample_session):
        """Test getting session by email"""
        mock_table = MagicMock()
        mock_table.query.return_value = {'Items': [sample_session.to_dynamodb()]}
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.get_by_email("test@example.com")
            assert result is not None
            assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_update_session(self, repo):
        """Test updating session"""
        mock_table = MagicMock()
        updated_session = Session(
            email="test@example.com",
            session_id="sess_123456",
            active_channels=["telegram", "whatsapp"]
        )
        mock_table.update_item.return_value = {'Attributes': updated_session.to_dynamodb()}
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.update("test@example.com", "sess_123456", {'active_channels': ["telegram", "whatsapp"]})
            assert len(result.active_channels) == 2


# ============================================================================
# UNIT TESTS - MemoryRepository
# ============================================================================

@pytest.mark.unit
class TestMemoryRepository:
    """Tests for MemoryRepository"""

    @pytest.fixture
    def repo(self):
        """Create repository instance"""
        return MemoryRepository()

    @pytest.fixture
    def sample_memory(self):
        """Create sample memory"""
        return Memory(
            email="test@example.com",
            domain="retail",
            context={"last_intent": "check_orders", "connector": "ifood"}
        )

    @pytest.mark.asyncio
    async def test_create_memory(self, repo, sample_memory):
        """Test creating memory entry"""
        mock_table = MagicMock()
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.create(sample_memory)
            assert result.email == sample_memory.email
            assert result.domain == sample_memory.domain

    @pytest.mark.asyncio
    async def test_get_memory_by_email_and_domain(self, repo, sample_memory):
        """Test getting memory by email and domain"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {'Item': sample_memory.to_dynamodb()}
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.get_by_email_and_domain("test@example.com", "retail")
            assert result is not None
            assert result.domain == "retail"

    @pytest.mark.asyncio
    async def test_get_memory_by_email(self, repo, sample_memory):
        """Test getting all memory entries for email"""
        mock_table = MagicMock()
        mock_table.query.return_value = {'Items': [sample_memory.to_dynamodb()]}
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.get_by_email("test@example.com")
            assert len(result) == 1
            assert result[0].domain == "retail"

    @pytest.mark.asyncio
    async def test_update_memory(self, repo):
        """Test updating memory"""
        mock_table = MagicMock()
        updated_memory = Memory(
            email="test@example.com",
            domain="retail",
            context={"last_intent": "confirm_order", "connector": "ifood"}
        )
        mock_table.update_item.return_value = {'Attributes': updated_memory.to_dynamodb()}
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.update("test@example.com", "retail", {"last_intent": "confirm_order"})
            assert result.context["last_intent"] == "confirm_order"


# ============================================================================
# UNIT TESTS - UsageRepository
# ============================================================================

@pytest.mark.unit
class TestUsageRepository:
    """Tests for UsageRepository"""

    @pytest.fixture
    def repo(self):
        """Create repository instance"""
        return UsageRepository()

    @pytest.fixture
    def sample_usage(self):
        """Create sample usage"""
        now = datetime.utcnow()
        return Usage(
            email="test@example.com",
            year=now.year,
            month=now.month,
            message_count=5,
            tier=UserTier.FREE
        )

    @pytest.mark.asyncio
    async def test_create_usage(self, repo, sample_usage):
        """Test creating usage entry"""
        mock_table = MagicMock()
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.create(sample_usage)
            assert result.email == sample_usage.email
            assert result.message_count == 5

    @pytest.mark.asyncio
    async def test_increment_message_count(self, repo):
        """Test incrementing message count"""
        mock_table = MagicMock()
        updated_usage = Usage(
            email="test@example.com",
            year=2025,
            month=1,
            message_count=6,
            tier=UserTier.FREE
        )
        mock_table.update_item.return_value = {'Attributes': updated_usage.to_dynamodb()}
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.increment_message_count("test@example.com", 2025, 1)
            assert result.message_count == 6


# ============================================================================
# UNIT TESTS - AuditLogRepository
# ============================================================================

@pytest.mark.unit
class TestAuditLogRepository:
    """Tests for AuditLogRepository"""

    @pytest.fixture
    def repo(self):
        """Create repository instance"""
        return AuditLogRepository()

    @pytest.fixture
    def sample_audit_log(self):
        """Create sample audit log"""
        return AuditLog(
            email="test@example.com",
            timestamp=datetime.utcnow().isoformat(),
            action_id="action_123",
            agent="retail_agent",
            action="check_orders",
            input_data={"connector": "ifood"},
            output_data={"orders": [1, 2, 3]},
            status="success"
        )

    @pytest.mark.asyncio
    async def test_create_audit_log(self, repo, sample_audit_log):
        """Test creating audit log"""
        mock_table = MagicMock()
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.create(sample_audit_log)
            assert result.email == sample_audit_log.email
            assert result.action == "check_orders"

    @pytest.mark.asyncio
    async def test_get_audit_logs_by_email(self, repo, sample_audit_log):
        """Test getting audit logs by email"""
        mock_table = MagicMock()
        mock_table.query.return_value = {'Items': [sample_audit_log.to_dynamodb()]}
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.get_by_email("test@example.com")
            assert len(result) == 1
            assert result[0].action == "check_orders"

    @pytest.mark.asyncio
    async def test_get_audit_logs_by_agent(self, repo, sample_audit_log):
        """Test getting audit logs by agent (GSI)"""
        mock_table = MagicMock()
        mock_table.query.return_value = {'Items': [sample_audit_log.to_dynamodb()]}
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.get_by_agent("retail_agent")
            assert len(result) == 1
            assert result[0].agent == "retail_agent"


# ============================================================================
# UNIT TESTS - EscalationRepository
# ============================================================================

@pytest.mark.unit
class TestEscalationRepository:
    """Tests for EscalationRepository"""

    @pytest.fixture
    def repo(self):
        """Create repository instance"""
        return EscalationRepository()

    @pytest.fixture
    def sample_escalation(self):
        """Create sample escalation"""
        return Escalation(
            escalation_id="esc_123",
            email="test@example.com",
            created_at=datetime.utcnow().isoformat(),
            decision_type="order_confirmation",
            context={"order_id": "order_123"}
        )

    @pytest.mark.asyncio
    async def test_create_escalation(self, repo, sample_escalation):
        """Test creating escalation"""
        mock_table = MagicMock()
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.create(sample_escalation)
            assert result.escalation_id == sample_escalation.escalation_id
            assert result.decision_type == "order_confirmation"

    @pytest.mark.asyncio
    async def test_get_escalation_by_id(self, repo, sample_escalation):
        """Test getting escalation by ID"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {'Item': sample_escalation.to_dynamodb()}
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.get_by_id("esc_123")
            assert result is not None
            assert result.escalation_id == "esc_123"

    @pytest.mark.asyncio
    async def test_get_escalations_by_email(self, repo, sample_escalation):
        """Test getting escalations by email (GSI)"""
        mock_table = MagicMock()
        mock_table.query.return_value = {'Items': [sample_escalation.to_dynamodb()]}
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.get_by_email("test@example.com")
            assert len(result) == 1
            assert result[0].email == "test@example.com"

    @pytest.mark.asyncio
    async def test_update_escalation(self, repo):
        """Test updating escalation"""
        mock_table = MagicMock()
        updated_escalation = Escalation(
            escalation_id="esc_123",
            email="test@example.com",
            created_at=datetime.utcnow().isoformat(),
            decision_type="order_confirmation",
            human_decision="approved",
            resolved_at=datetime.utcnow().isoformat()
        )
        mock_table.update_item.return_value = {'Attributes': updated_escalation.to_dynamodb()}
        with patch.object(repo, 'get_table', return_value=mock_table):
            result = await repo.update("esc_123", {'human_decision': 'approved'})
            assert result.human_decision == "approved"
