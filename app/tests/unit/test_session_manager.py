"""Unit tests for Session Manager Service"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from app.omnichannel.authentication import (
    SessionManager,
    Session,
    SessionConfig,
)


@pytest.mark.unit
class TestSessionConfig:
    """Tests for SessionConfig"""

    def test_config_creation_with_defaults(self):
        """Test creating config with default values"""
        config = SessionConfig()

        assert config.region == "us-east-1"
        assert config.sessions_table == "sessions"
        assert config.ttl_hours == 24
        assert config.email_index == "email-index"

    def test_config_creation_with_custom_values(self):
        """Test creating config with custom values"""
        config = SessionConfig(
            region="eu-west-1",
            sessions_table="custom_sessions",
            ttl_hours=12,
            email_index="custom_index",
        )

        assert config.region == "eu-west-1"
        assert config.sessions_table == "custom_sessions"
        assert config.ttl_hours == 12
        assert config.email_index == "custom_index"


@pytest.mark.unit
class TestSession:
    """Tests for Session model"""

    def test_session_creation(self):
        """Test creating session"""
        session = Session(
            session_id="session-123",
            email="user@example.com",
            channel="telegram",
            channel_id="123456",
        )

        assert session.session_id == "session-123"
        assert session.email == "user@example.com"
        assert session.channel == "telegram"
        assert session.channel_id == "123456"
        assert session.created_at is not None
        assert session.updated_at is not None
        assert session.expires_at is not None

    def test_session_to_dict(self):
        """Test converting session to dictionary"""
        session = Session(
            session_id="session-123",
            email="user@example.com",
            channel="telegram",
            channel_id="123456",
        )
        session_dict = session.to_dict()

        assert session_dict["session_id"] == "session-123"
        assert session_dict["email"] == "user@example.com"
        assert session_dict["channel"] == "telegram"
        assert session_dict["channel_id"] == "123456"

    def test_session_from_dict(self):
        """Test creating session from dictionary"""
        data = {
            "session_id": "session-123",
            "email": "user@example.com",
            "channel": "telegram",
            "channel_id": "123456",
            "created_at": "2024-01-01T10:00:00+00:00",
            "updated_at": "2024-01-01T10:00:00+00:00",
            "expires_at": "2024-01-02T10:00:00+00:00",
            "context": {"key": "value"},
            "metadata": {"meta": "data"},
        }

        session = Session.from_dict(data)

        assert session.session_id == "session-123"
        assert session.email == "user@example.com"
        assert session.context["key"] == "value"
        assert session.metadata["meta"] == "data"

    def test_session_is_valid(self):
        """Test session validity check"""
        # Valid session (expires in future)
        future_expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        session = Session(
            session_id="session-123",
            email="user@example.com",
            channel="telegram",
            channel_id="123456",
            expires_at=future_expires,
        )

        assert session.is_valid() is True
        assert session.is_expired() is False

    def test_session_is_expired(self):
        """Test session expiration check"""
        # Expired session (expired in past)
        past_expires = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        session = Session(
            session_id="session-123",
            email="user@example.com",
            channel="telegram",
            channel_id="123456",
            expires_at=past_expires,
        )

        assert session.is_valid() is False
        assert session.is_expired() is True

    def test_session_with_context(self):
        """Test session with context"""
        context = {"last_intent": "check_orders", "domain": "retail"}
        session = Session(
            session_id="session-123",
            email="user@example.com",
            channel="telegram",
            channel_id="123456",
            context=context,
        )

        assert session.context["last_intent"] == "check_orders"
        assert session.context["domain"] == "retail"


@pytest.mark.unit
class TestSessionManager:
    """Tests for SessionManager"""

    @pytest.fixture
    def config(self):
        """Create config"""
        return SessionConfig()

    @pytest.fixture
    def manager(self, config):
        """Create manager"""
        with patch("boto3.resource"):
            return SessionManager(config)

    def test_generate_session_id(self):
        """Test session ID generation"""
        session_id_1 = SessionManager._generate_session_id()
        session_id_2 = SessionManager._generate_session_id()

        assert session_id_1 != session_id_2
        assert len(session_id_1) > 0
        assert len(session_id_2) > 0

    def test_calculate_ttl(self):
        """Test TTL calculation"""
        ttl = SessionManager._calculate_ttl()

        # TTL should be a timestamp in the future
        now = int(datetime.now(timezone.utc).timestamp())
        assert ttl > now

    @pytest.mark.asyncio
    async def test_create_session_success(self, manager):
        """Test creating session successfully"""
        manager.table.put_item = MagicMock()

        session = await manager.create_session(
            "user@example.com", "telegram", "123456"
        )

        assert session.email == "user@example.com"
        assert session.channel == "telegram"
        assert session.channel_id == "123456"
        assert session.session_id is not None
        manager.table.put_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_invalid_email(self, manager):
        """Test creating session with invalid email"""
        with pytest.raises(ValueError):
            await manager.create_session("invalid-email", "telegram", "123456")

    @pytest.mark.asyncio
    async def test_create_session_missing_channel(self, manager):
        """Test creating session without channel"""
        with pytest.raises(ValueError):
            await manager.create_session("user@example.com", "", "123456")

    @pytest.mark.asyncio
    async def test_get_session_success(self, manager):
        """Test getting session successfully"""
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

        session = await manager.get_session("session-123")

        assert session is not None
        assert session.session_id == "session-123"
        assert session.email == "user@example.com"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, manager):
        """Test getting session that doesn't exist"""
        manager.table.get_item = MagicMock(return_value={})

        session = await manager.get_session("session-999")

        assert session is None

    @pytest.mark.asyncio
    async def test_get_session_expired(self, manager):
        """Test getting expired session"""
        past_expires = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        manager.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "session_id": "session-123",
                    "email": "user@example.com",
                    "channel": "telegram",
                    "channel_id": "123456",
                    "created_at": "2024-01-01T10:00:00+00:00",
                    "updated_at": "2024-01-01T10:00:00+00:00",
                    "expires_at": past_expires,
                    "context": {},
                    "metadata": {},
                }
            }
        )
        manager.table.delete_item = MagicMock()

        session = await manager.get_session("session-123")

        assert session is None
        manager.table.delete_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_by_email_success(self, manager):
        """Test getting session by email"""
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

        session = await manager.get_session_by_email("user@example.com")

        assert session is not None
        assert session.email == "user@example.com"

    @pytest.mark.asyncio
    async def test_get_session_by_email_not_found(self, manager):
        """Test getting session by email (not found)"""
        manager.table.query = MagicMock(return_value={"Items": []})

        session = await manager.get_session_by_email("user@example.com")

        assert session is None

    @pytest.mark.asyncio
    async def test_get_all_sessions_for_email(self, manager):
        """Test getting all sessions for email"""
        future_expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        manager.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "session_id": "session-1",
                        "email": "user@example.com",
                        "channel": "telegram",
                        "channel_id": "123456",
                        "created_at": "2024-01-01T10:00:00+00:00",
                        "updated_at": "2024-01-01T10:00:00+00:00",
                        "expires_at": future_expires,
                        "context": {},
                        "metadata": {},
                    },
                    {
                        "session_id": "session-2",
                        "email": "user@example.com",
                        "channel": "whatsapp",
                        "channel_id": "5511999999999",
                        "created_at": "2024-01-01T10:00:00+00:00",
                        "updated_at": "2024-01-01T10:00:00+00:00",
                        "expires_at": future_expires,
                        "context": {},
                        "metadata": {},
                    },
                ]
            }
        )

        sessions = await manager.get_all_sessions_for_email("user@example.com")

        assert len(sessions) == 2
        assert sessions[0].channel == "telegram"
        assert sessions[1].channel == "whatsapp"

    @pytest.mark.asyncio
    async def test_update_session_success(self, manager):
        """Test updating session"""
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

        session = await manager.update_session(
            "session-123", context={"key": "value"}
        )

        assert session is not None
        manager.table.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_session_context(self, manager):
        """Test updating session context"""
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
                    "context": {"existing": "value"},
                    "metadata": {},
                }
            }
        )
        manager.table.update_item = MagicMock()

        session = await manager.update_session_context(
            "session-123", {"new": "value"}
        )

        assert session is not None
        manager.table.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_session_valid(self, manager):
        """Test validating valid session"""
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

        is_valid = await manager.validate_session("session-123")

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_session_invalid(self, manager):
        """Test validating invalid session"""
        manager.table.get_item = MagicMock(return_value={})

        is_valid = await manager.validate_session("session-999")

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_delete_session_success(self, manager):
        """Test deleting session"""
        manager.table.delete_item = MagicMock(
            return_value={"Attributes": {"session_id": "session-123"}}
        )

        result = await manager.delete_session("session-123")

        assert result is True
        manager.table.delete_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, manager):
        """Test deleting session that doesn't exist"""
        manager.table.delete_item = MagicMock(return_value={})

        result = await manager.delete_session("session-999")

        assert result is False

    @pytest.mark.asyncio
    async def test_extend_session_success(self, manager):
        """Test extending session"""
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

        session = await manager.extend_session("session-123")

        assert session is not None
        manager.table.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_context(self, manager):
        """Test getting session context"""
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
                    "context": {"key": "value"},
                    "metadata": {},
                }
            }
        )

        context = await manager.get_session_context("session-123")

        assert context is not None
        assert context["key"] == "value"

    @pytest.mark.asyncio
    async def test_get_session_metadata(self, manager):
        """Test getting session metadata"""
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
                    "metadata": {"meta": "data"},
                }
            }
        )

        metadata = await manager.get_session_metadata("session-123")

        assert metadata is not None
        assert metadata["meta"] == "data"
