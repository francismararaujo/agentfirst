"""End-to-end tests for user workflows - Test complete user journeys"""

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


@pytest.mark.e2e
class TestUserRegistrationWorkflow:
    """End-to-end tests for user registration workflow"""

    @pytest.fixture
    def user_repo(self):
        return UserRepository()

    @pytest.fixture
    def session_repo(self):
        return SessionRepository()

    @pytest.fixture
    def usage_repo(self):
        return UsageRepository()

    @pytest.mark.asyncio
    async def test_complete_user_registration_flow(self, user_repo, session_repo, usage_repo):
        """Test complete user registration flow: create user → create session → initialize usage"""
        
        # Step 1: Create user
        user = User(
            email="newuser@example.com",
            tier=UserTier.FREE,
            telegram_id=987654321
        )
        
        mock_user_table = MagicMock()
        with patch.object(user_repo, 'get_table', return_value=mock_user_table):
            created_user = await user_repo.create(user)
            assert created_user.email == "newuser@example.com"
            assert created_user.tier == UserTier.FREE
        
        # Step 2: Create session for user
        session = Session(
            email=created_user.email,
            session_id="sess_new_user",
            authenticated=True,
            active_channels=["telegram"]
        )
        
        mock_session_table = MagicMock()
        with patch.object(session_repo, 'get_table', return_value=mock_session_table):
            created_session = await session_repo.create(session)
            assert created_session.email == created_user.email
            assert created_session.authenticated is True
        
        # Step 3: Initialize usage tracking
        now = datetime.utcnow()
        usage = Usage(
            email=created_user.email,
            year=now.year,
            month=now.month,
            message_count=0,
            tier=UserTier.FREE
        )
        
        mock_usage_table = MagicMock()
        with patch.object(usage_repo, 'get_table', return_value=mock_usage_table):
            created_usage = await usage_repo.create(usage)
            assert created_usage.email == created_user.email
            assert created_usage.message_count == 0


@pytest.mark.e2e
class TestUserMessageProcessingWorkflow:
    """End-to-end tests for user message processing workflow"""

    @pytest.fixture
    def user_repo(self):
        return UserRepository()

    @pytest.fixture
    def session_repo(self):
        return SessionRepository()

    @pytest.fixture
    def memory_repo(self):
        return MemoryRepository()

    @pytest.fixture
    def usage_repo(self):
        return UsageRepository()

    @pytest.fixture
    def audit_repo(self):
        return AuditLogRepository()

    @pytest.mark.asyncio
    async def test_complete_message_processing_flow(
        self, user_repo, session_repo, memory_repo, usage_repo, audit_repo
    ):
        """Test complete message processing flow: authenticate → store context → track usage → audit"""
        
        # Step 1: Authenticate user (get user and session)
        user = User(
            email="user@example.com",
            tier=UserTier.FREE,
            telegram_id=123456789
        )
        
        mock_user_table = MagicMock()
        with patch.object(user_repo, 'get_table', return_value=mock_user_table):
            authenticated_user = await user_repo.create(user)
        
        session = Session(
            email=authenticated_user.email,
            session_id="sess_123",
            authenticated=True,
            active_channels=["telegram"]
        )
        
        mock_session_table = MagicMock()
        with patch.object(session_repo, 'get_table', return_value=mock_session_table):
            active_session = await session_repo.create(session)
            assert active_session.authenticated is True
        
        # Step 2: Store conversation context in memory
        memory = Memory(
            email=authenticated_user.email,
            domain="retail",
            context={"last_intent": "check_orders", "connector": "ifood"}
        )
        
        mock_memory_table = MagicMock()
        with patch.object(memory_repo, 'get_table', return_value=mock_memory_table):
            stored_memory = await memory_repo.create(memory)
            assert stored_memory.context["last_intent"] == "check_orders"
        
        # Step 3: Track usage
        now = datetime.utcnow()
        usage = Usage(
            email=authenticated_user.email,
            year=now.year,
            month=now.month,
            message_count=1,
            tier=UserTier.FREE
        )
        
        mock_usage_table = MagicMock()
        with patch.object(usage_repo, 'get_table', return_value=mock_usage_table):
            tracked_usage = await usage_repo.create(usage)
            assert tracked_usage.message_count == 1
        
        # Step 4: Create audit log
        audit_log = AuditLog(
            email=authenticated_user.email,
            timestamp=datetime.utcnow().isoformat(),
            action_id="action_msg_001",
            agent="retail_agent",
            action="check_orders",
            input_data={"connector": "ifood"},
            output_data={"orders": [1, 2, 3]},
            status="success"
        )
        
        mock_audit_table = MagicMock()
        with patch.object(audit_repo, 'get_table', return_value=mock_audit_table):
            logged_action = await audit_repo.create(audit_log)
            assert logged_action.action == "check_orders"
            assert logged_action.status == "success"


@pytest.mark.e2e
class TestUserUpgradeWorkflow:
    """End-to-end tests for user upgrade workflow"""

    @pytest.fixture
    def user_repo(self):
        return UserRepository()

    @pytest.fixture
    def usage_repo(self):
        return UsageRepository()

    @pytest.mark.asyncio
    async def test_user_upgrade_from_free_to_pro(self, user_repo, usage_repo):
        """Test user upgrade workflow: create free user → upgrade to pro"""
        
        # Step 1: Create free user
        user = User(
            email="user@example.com",
            tier=UserTier.FREE,
            telegram_id=123456789
        )
        
        mock_user_table = MagicMock()
        with patch.object(user_repo, 'get_table', return_value=mock_user_table):
            created_user = await user_repo.create(user)
            assert created_user.tier == UserTier.FREE
        
        # Step 2: Upgrade user to PRO
        updated_user = User(
            email=created_user.email,
            tier=UserTier.PRO,
            telegram_id=created_user.telegram_id
        )
        
        mock_user_table.update_item.return_value = {'Attributes': updated_user.to_dynamodb()}
        with patch.object(user_repo, 'get_table', return_value=mock_user_table):
            upgraded_user = await user_repo.update(created_user.email, {'tier': 'pro'})
            assert upgraded_user.tier == UserTier.PRO
        
        # Step 3: Update usage limits for PRO tier
        now = datetime.utcnow()
        usage = Usage(
            email=upgraded_user.email,
            year=now.year,
            month=now.month,
            message_count=0,
            tier=UserTier.PRO
        )
        
        mock_usage_table = MagicMock()
        with patch.object(usage_repo, 'get_table', return_value=mock_usage_table):
            updated_usage = await usage_repo.create(usage)
            assert updated_usage.tier == UserTier.PRO
