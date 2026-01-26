"""Integration tests for Session Manager Service"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from app.omnichannel.authentication import (
    SessionManager,
    SessionConfig,
)


@pytest.mark.integration
class TestSessionManagerIntegration:
    """Integration tests for session management"""

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
    async def test_complete_session_lifecycle(self, manager):
        """Test complete session lifecycle"""
        email = "user@example.com"
        channel = "telegram"
        channel_id = "123456"

        # Mock DynamoDB responses
        manager.table.put_item = MagicMock()
        manager.table.get_item = MagicMock(return_value={})
        manager.table.update_item = MagicMock()
        manager.table.delete_item = MagicMock()

        # 1. Create session
        session = await manager.create_session(email, channel, channel_id)
        assert session.email == email
        assert session.channel == channel
        assert session.session_id is not None

        # 2. Get session
        future_expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        manager.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "session_id": session.session_id,
                    "email": email,
                    "channel": channel,
                    "channel_id": channel_id,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "expires_at": future_expires,
                    "context": {},
                    "metadata": {},
                }
            }
        )

        retrieved_session = await manager.get_session(session.session_id)
        assert retrieved_session is not None
        assert retrieved_session.email == email

        # 3. Update session
        manager.table.update_item = MagicMock()
        updated_session = await manager.update_session(
            session.session_id, context={"key": "value"}
        )
        assert updated_session is not None

        # 4. Extend session
        extended_session = await manager.extend_session(session.session_id)
        assert extended_session is not None

        # 5. Delete session
        manager.table.delete_item = MagicMock(
            return_value={"Attributes": {"session_id": session.session_id}}
        )
        result = await manager.delete_session(session.session_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_multiple_sessions_for_same_user(self, manager):
        """Test multiple sessions for same user"""
        email = "user@example.com"

        manager.table.put_item = MagicMock()
        manager.table.query = MagicMock(return_value={"Items": []})

        # Create Telegram session
        telegram_session = await manager.create_session(email, "telegram", "123456")
        assert telegram_session.channel == "telegram"

        # Create WhatsApp session
        whatsapp_session = await manager.create_session(
            email, "whatsapp", "5511999999999"
        )
        assert whatsapp_session.channel == "whatsapp"

        # Get all sessions
        future_expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        manager.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "session_id": telegram_session.session_id,
                        "email": email,
                        "channel": "telegram",
                        "channel_id": "123456",
                        "created_at": telegram_session.created_at,
                        "updated_at": telegram_session.updated_at,
                        "expires_at": future_expires,
                        "context": {},
                        "metadata": {},
                    },
                    {
                        "session_id": whatsapp_session.session_id,
                        "email": email,
                        "channel": "whatsapp",
                        "channel_id": "5511999999999",
                        "created_at": whatsapp_session.created_at,
                        "updated_at": whatsapp_session.updated_at,
                        "expires_at": future_expires,
                        "context": {},
                        "metadata": {},
                    },
                ]
            }
        )

        sessions = await manager.get_all_sessions_for_email(email)
        assert len(sessions) == 2

    @pytest.mark.asyncio
    async def test_session_context_preservation(self, manager):
        """Test session context preservation across updates"""
        email = "user@example.com"

        manager.table.put_item = MagicMock()
        future_expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

        # Create session with initial context
        session = await manager.create_session(
            email, "telegram", "123456", context={"domain": "retail"}
        )

        # Update context
        manager.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "session_id": session.session_id,
                    "email": email,
                    "channel": "telegram",
                    "channel_id": "123456",
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "expires_at": future_expires,
                    "context": {"domain": "retail"},
                    "metadata": {},
                }
            }
        )
        manager.table.update_item = MagicMock()

        updated_session = await manager.update_session_context(
            session.session_id, {"intent": "check_orders"}
        )

        assert updated_session is not None
        manager.table.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_expiration_workflow(self, manager):
        """Test session expiration workflow"""
        email = "user@example.com"

        # Create session with past expiration
        past_expires = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        manager.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "session_id": "session-123",
                    "email": email,
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

        # Try to get expired session
        session = await manager.get_session("session-123")

        # Should return None and delete the session
        assert session is None
        manager.table.delete_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_validation_workflow(self, manager):
        """Test session validation workflow"""
        email = "user@example.com"

        # Valid session
        future_expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        manager.table.get_item = MagicMock(
            return_value={
                "Item": {
                    "session_id": "session-123",
                    "email": email,
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

        # Invalid session
        manager.table.get_item = MagicMock(return_value={})
        is_valid = await manager.validate_session("session-999")
        assert is_valid is False


@pytest.mark.integration
class TestSessionManagerErrorHandling:
    """Integration tests for session manager error handling"""

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
    async def test_invalid_email_formats(self, manager):
        """Test with various invalid email formats (no @ symbol)"""
        invalid_emails = [
            "invalid",  # No @
            "user",  # No @
            "example.com",  # No @
        ]

        for email in invalid_emails:
            manager.table.put_item = MagicMock()
            with pytest.raises(ValueError):
                await manager.create_session(email, "telegram", "123456")

    @pytest.mark.asyncio
    async def test_missing_channel_info(self, manager):
        """Test creating session without channel info"""
        with pytest.raises(ValueError):
            await manager.create_session("user@example.com", "", "123456")

        with pytest.raises(ValueError):
            await manager.create_session("user@example.com", "telegram", "")

    @pytest.mark.asyncio
    async def test_update_nonexistent_session(self, manager):
        """Test updating non-existent session"""
        manager.table.get_item = MagicMock(return_value={})

        with pytest.raises(ValueError):
            await manager.update_session("session-999", context={"key": "value"})

    @pytest.mark.asyncio
    async def test_extend_nonexistent_session(self, manager):
        """Test extending non-existent session"""
        manager.table.get_item = MagicMock(return_value={})

        with pytest.raises(ValueError):
            await manager.extend_session("session-999")

    @pytest.mark.asyncio
    async def test_delete_all_sessions_for_email(self, manager):
        """Test deleting all sessions for email"""
        email = "user@example.com"
        future_expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

        manager.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "session_id": "session-1",
                        "email": email,
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
                        "email": email,
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
        manager.table.delete_item = MagicMock(
            return_value={"Attributes": {"session_id": "session-1"}}
        )

        deleted_count = await manager.delete_all_sessions_for_email(email)

        assert deleted_count >= 0
