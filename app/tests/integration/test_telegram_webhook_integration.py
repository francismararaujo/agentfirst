"""Integration tests for Telegram webhook"""

import pytest
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app


@pytest.mark.integration
class TestTelegramWebhookIntegration:
    """Integration tests for Telegram webhook"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_telegram_webhook_receives_message(self, client):
        """Test that webhook receives and processes message"""
        payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "date": 1234567890,
                "chat": {
                    "id": 987654321,
                    "first_name": "Test",
                    "type": "private"
                },
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Test"
                },
                "text": "Olá, como você está?"
            }
        }

        with patch("app.main.TelegramService.send_typing_indicator", new_callable=AsyncMock) as mock_typing:
            with patch("app.main.TelegramService.send_message", new_callable=AsyncMock) as mock_send:
                mock_typing.return_value = {"ok": True}
                mock_send.return_value = {
                    "ok": True,
                    "result": {"message_id": 2}
                }

                response = client.post(
                    "/webhook/telegram",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                assert response.status_code == 200
                assert response.json()["ok"] is True

    def test_telegram_webhook_missing_message(self, client):
        """Test webhook with missing message"""
        payload = {
            "update_id": 123456789,
        }

        response = client.post(
            "/webhook/telegram",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_telegram_webhook_missing_chat_id(self, client):
        """Test webhook with missing chat_id"""
        payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "date": 1234567890,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Test"
                },
                "text": "Olá"
            }
        }

        response = client.post(
            "/webhook/telegram",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_telegram_webhook_missing_text(self, client):
        """Test webhook with missing text"""
        payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "date": 1234567890,
                "chat": {
                    "id": 987654321,
                    "first_name": "Test",
                    "type": "private"
                },
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Test"
                }
            }
        }

        response = client.post(
            "/webhook/telegram",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_telegram_webhook_invalid_json(self, client):
        """Test webhook with invalid JSON"""
        response = client.post(
            "/webhook/telegram",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        assert "error" in response.json()

    def test_telegram_webhook_sends_response(self, client):
        """Test that webhook sends response to user"""
        payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "date": 1234567890,
                "chat": {
                    "id": 987654321,
                    "first_name": "Test",
                    "type": "private"
                },
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Test"
                },
                "text": "Teste"
            }
        }

        with patch("app.main.TelegramService.send_typing_indicator", new_callable=AsyncMock) as mock_typing:
            with patch("app.main.TelegramService.send_message", new_callable=AsyncMock) as mock_send:
                mock_typing.return_value = {"ok": True}
                mock_send.return_value = {
                    "ok": True,
                    "result": {"message_id": 2}
                }

                response = client.post(
                    "/webhook/telegram",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                # Verify send_message was called
                assert mock_send.called
                call_args = mock_send.call_args
                assert call_args[1]["chat_id"] == 987654321
                assert "Recebi sua mensagem" in call_args[1]["text"]
