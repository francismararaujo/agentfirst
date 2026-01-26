"""Integration tests for DynamoDB repositories - Test multiple repositories working together"""

import pytest
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


@pytest.mark.integration
class TestUserSessionIntegration:
    """Integration tests for User and Session repositories"""

    @pytest.fixture
    def user_repo(self):
        return UserRepository()

    @pytest.fixture
    def session_repo(self):
        return SessionRepository()

    @pytest.mark.asyncio
    async def test_create_user_and_session(self, user_repo, session_repo):
        """Test creating a user and then a session for that user"""
        # Create user
        user = User(
            email="test@example.com",
            tier=UserTier.FREE,
            telegram_id=123456789
        )
        
        mock_user_table = MagicMock()
        mock_user_table.put_item.return_value = None
        
        with patch.object(user_repo, 'get_table', return_value=mock_user_table):
            created_user = await user_repo.create(user)
            assert created_user.email == "test@example.com"
        
        # Create session for the user
        session = Session(
            email=created_user.email,
            session_id="sess_123456",
            authenticated=True,
            active_channels=["telegram"]
        )
        
        mock_session_table = MagicMock()
        mock_session_table.put_item.return_value = None
        
        with patch.object(session_repo, 'get_table', return_value=mock_session_table):
            created_session = await session_repo.create(session)
            assert created_session.email == created_user.email
            assert created_session.session_id == "sess_123456"


@pytest.mark.integration
class TestUserMemoryIntegration:
    """Integration tests for User and Memory repositories"""

    @pytest.fixture
    def user_repo(self):
        return UserRepository()

    @pytest.fixture
    def memory_repo(self):
        return MemoryRepository()

    @pytest.mark.asyncio
    async def test_create_user_and_memory(self, user_repo, memory_repo):
        """Test creating a user and then storing memory for that user"""
        # Create user
        user = User(
            email="test@example.com",
            tier=UserTier.FREE,
            telegram_id=123456789
        )
        
        mock_user_table = MagicMock()
        with patch.object(user_repo, 'get_table', return_value=mock_user_table):
            created_user = await user_repo.create(user)
        
        # Create memory for the user
        memory = Memory(
            email=created_user.email,
            domain="retail",
            context={"last_intent": "check_orders", "connector": "ifood"}
        )
        
        mock_memory_table = MagicMock()
        with patch.object(memory_repo, 'get_table', return_value=mock_memory_table):
            created_memory = await memory_repo.create(memory)
            assert created_memory.email == created_user.email
            assert created_memory.domain == "retail"


@pytest.mark.integration
class TestUserUsageIntegration:
    """Integration tests for User and Usage repositories"""

    @pytest.fixture
    def user_repo(self):
        return UserRepository()

    @pytest.fixture
    def usage_repo(self):
        return UsageRepository()

    @pytest.mark.asyncio
    async def test_create_user_and_track_usage(self, user_repo, usage_repo):
        """Test creating a user and then tracking usage for that user"""
        # Create user
        user = User(
            email="test@example.com",
            tier=UserTier.FREE,
            telegram_id=123456789
        )
        
        mock_user_table = MagicMock()
        with patch.object(user_repo, 'get_table', return_value=mock_user_table):
            created_user = await user_repo.create(user)
        
        # Track usage for the user
        now = datetime.utcnow()
        usage = Usage(
            email=created_user.email,
            year=now.year,
            month=now.month,
            message_count=5,
            tier=UserTier.FREE
        )
        
        mock_usage_table = MagicMock()
        with patch.object(usage_repo, 'get_table', return_value=mock_usage_table):
            created_usage = await usage_repo.create(usage)
            assert created_usage.email == created_user.email
            assert created_usage.message_count == 5


@pytest.mark.integration
class TestUserAuditLogIntegration:
    """Integration tests for User and AuditLog repositories"""

    @pytest.fixture
    def user_repo(self):
        return UserRepository()

    @pytest.fixture
    def audit_repo(self):
        return AuditLogRepository()

    @pytest.mark.asyncio
    async def test_create_user_and_audit_log(self, user_repo, audit_repo):
        """Test creating a user and then logging an audit entry for that user"""
        # Create user
        user = User(
            email="test@example.com",
            tier=UserTier.FREE,
            telegram_id=123456789
        )
        
        mock_user_table = MagicMock()
        with patch.object(user_repo, 'get_table', return_value=mock_user_table):
            created_user = await user_repo.create(user)
        
        # Create audit log for the user
        audit_log = AuditLog(
            email=created_user.email,
            timestamp=datetime.utcnow().isoformat(),
            action_id="action_123",
            agent="retail_agent",
            action="check_orders",
            input_data={"connector": "ifood"},
            output_data={"orders": [1, 2, 3]},
            status="success"
        )
        
        mock_audit_table = MagicMock()
        with patch.object(audit_repo, 'get_table', return_value=mock_audit_table):
            created_audit = await audit_repo.create(audit_log)
            assert created_audit.email == created_user.email
            assert created_audit.action == "check_orders"


@pytest.mark.integration
class TestUserEscalationIntegration:
    """Integration tests for User and Escalation repositories"""

    @pytest.fixture
    def user_repo(self):
        return UserRepository()

    @pytest.fixture
    def escalation_repo(self):
        return EscalationRepository()

    @pytest.mark.asyncio
    async def test_create_user_and_escalation(self, user_repo, escalation_repo):
        """Test creating a user and then creating an escalation for that user"""
        # Create user
        user = User(
            email="test@example.com",
            tier=UserTier.FREE,
            telegram_id=123456789
        )
        
        mock_user_table = MagicMock()
        with patch.object(user_repo, 'get_table', return_value=mock_user_table):
            created_user = await user_repo.create(user)
        
        # Create escalation for the user
        escalation = Escalation(
            escalation_id="esc_123",
            email=created_user.email,
            created_at=datetime.utcnow().isoformat(),
            decision_type="order_confirmation",
            context={"order_id": "order_123"}
        )
        
        mock_escalation_table = MagicMock()
        with patch.object(escalation_repo, 'get_table', return_value=mock_escalation_table):
            created_escalation = await escalation_repo.create(escalation)
            assert created_escalation.email == created_user.email
            assert created_escalation.decision_type == "order_confirmation"
