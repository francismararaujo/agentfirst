"""Unit tests for Telegram Service"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.omnichannel.telegram_service import TelegramService


@pytest.mark.unit
class TestTelegramService:
    """Tests for TelegramService"""

    @pytest.fixture
    def service(self):
        """Create TelegramService instance"""
        return TelegramService(bot_token="test_token_123")

    def test_service_initialization(self, service):
        """Test service initialization"""
        assert service.bot_token == "test_token_123"
        assert service.api_url == "https://api.telegram.org/bottest_token_123"

    @pytest.mark.asyncio
    async def test_send_message_success(self, service):
        """Test sending message successfully"""
        with patch("app.omnichannel.telegram_service.httpx.AsyncClient") as mock_client:
            # Mock the response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": True,
                "result": {"message_id": 123, "chat": {"id": 456}}
            }

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_response
            mock_async_client.__aenter__.return_value = mock_async_client

            with patch("app.omnichannel.telegram_service.httpx.AsyncClient", return_value=mock_async_client):
                result = await service.send_message(
                    chat_id=456,
                    text="Test message",
                    parse_mode="HTML"
                )

                assert result["ok"] is True
                assert result["result"]["message_id"] == 123

    @pytest.mark.asyncio
    async def test_send_message_with_reply(self, service):
        """Test sending message with reply_to_message_id"""
        with patch("app.omnichannel.telegram_service.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": True,
                "result": {"message_id": 124}
            }

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_response
            mock_async_client.__aenter__.return_value = mock_async_client

            with patch("app.omnichannel.telegram_service.httpx.AsyncClient", return_value=mock_async_client):
                result = await service.send_message(
                    chat_id=456,
                    text="Reply message",
                    reply_to_message_id=123
                )

                assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_send_typing_indicator(self, service):
        """Test sending typing indicator"""
        with patch("app.omnichannel.telegram_service.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_response
            mock_async_client.__aenter__.return_value = mock_async_client

            with patch("app.omnichannel.telegram_service.httpx.AsyncClient", return_value=mock_async_client):
                result = await service.send_typing_indicator(chat_id=456)

                assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_get_me(self, service):
        """Test getting bot information"""
        with patch("app.omnichannel.telegram_service.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": True,
                "result": {
                    "id": 123456789,
                    "is_bot": True,
                    "first_name": "TestBot",
                    "username": "test_bot"
                }
            }

            mock_async_client = AsyncMock()
            mock_async_client.get.return_value = mock_response
            mock_async_client.__aenter__.return_value = mock_async_client

            with patch("app.omnichannel.telegram_service.httpx.AsyncClient", return_value=mock_async_client):
                result = await service.get_me()

                assert result["ok"] is True
                assert result["result"]["username"] == "test_bot"

    @pytest.mark.asyncio
    async def test_set_webhook(self, service):
        """Test setting webhook"""
        with patch("app.omnichannel.telegram_service.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": True,
                "result": True,
                "description": "Webhook was set"
            }

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_response
            mock_async_client.__aenter__.return_value = mock_async_client

            with patch("app.omnichannel.telegram_service.httpx.AsyncClient", return_value=mock_async_client):
                result = await service.set_webhook(
                    url="https://example.com/webhook/telegram",
                    allowed_updates=["message"]
                )

                assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_delete_webhook(self, service):
        """Test deleting webhook"""
        with patch("app.omnichannel.telegram_service.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": True,
                "result": True,
                "description": "Webhook was deleted"
            }

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_response
            mock_async_client.__aenter__.return_value = mock_async_client

            with patch("app.omnichannel.telegram_service.httpx.AsyncClient", return_value=mock_async_client):
                result = await service.delete_webhook()

                assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_send_message_failure(self, service):
        """Test sending message failure"""
        with patch("app.omnichannel.telegram_service.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "ok": False,
                "error_code": 400,
                "description": "Bad Request: chat_id is invalid"
            }

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_response
            mock_async_client.__aenter__.return_value = mock_async_client

            with patch("app.omnichannel.telegram_service.httpx.AsyncClient", return_value=mock_async_client):
                result = await service.send_message(
                    chat_id=0,  # Invalid chat ID
                    text="Test message"
                )

                assert result["ok"] is False
                assert "error" in result
