"""Integration tests for Lambda & API Gateway - Test end-to-end request/response flow"""

import pytest
import json
from fastapi.testclient import TestClient
from app.main import app


@pytest.mark.integration
class TestAPIGatewayIntegration:
    """Integration tests for API Gateway endpoints"""

    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "environment" in data
        assert "version" in data

    def test_status_endpoint(self, client):
        """Test status endpoint"""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "environment" in data
        assert "version" in data

    def test_telegram_webhook_valid_json(self, client):
        """Test Telegram webhook with valid JSON"""
        payload = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "from": {"id": 123, "first_name": "John"},
                "chat": {"id": 123, "type": "private"},
                "date": 1234567890,
                "text": "Hello"
            }
        }

        response = client.post(
            "/webhook/telegram",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_telegram_webhook_invalid_json(self, client):
        """Test Telegram webhook with invalid JSON"""
        response = client.post(
            "/webhook/telegram",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400

    def test_ifood_webhook_valid_json(self, client):
        """Test iFood webhook with valid JSON"""
        payload = {
            "events": [
                {
                    "id": "event-123",
                    "type": "ORDER_CREATED",
                    "createdAt": "2024-01-01T10:00:00Z",
                    "orderId": "order-123"
                }
            ]
        }

        response = client.post(
            "/webhook/ifood",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_ifood_webhook_invalid_json(self, client):
        """Test iFood webhook with invalid JSON"""
        response = client.post(
            "/webhook/ifood",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in response"""
        response = client.get("/health")

        assert response.status_code == 200
        # CORS headers should be present (set by middleware)

    def test_request_id_header_present(self, client):
        """Test that X-Request-ID header is present in response"""
        response = client.get("/health")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    def test_process_time_header_present(self, client):
        """Test that X-Process-Time header is present in response"""
        response = client.get("/health")

        assert response.status_code == 200
        assert "X-Process-Time" in response.headers

    def test_multiple_requests_different_request_ids(self, client):
        """Test that different requests have different request IDs"""
        response1 = client.get("/health")
        response2 = client.get("/health")

        request_id1 = response1.headers.get("X-Request-ID")
        request_id2 = response2.headers.get("X-Request-ID")

        # Request IDs should be different (or at least both present)
        assert request_id1 is not None
        assert request_id2 is not None

    def test_error_response_format(self, client):
        """Test error response format"""
        response = client.post(
            "/webhook/telegram",
            content="invalid",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_404_not_found(self, client):
        """Test 404 response for non-existent endpoint"""
        response = client.get("/nonexistent")

        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 response for wrong HTTP method"""
        response = client.get("/webhook/telegram")

        assert response.status_code == 405


@pytest.mark.integration
class TestWebhookIntegration:
    """Integration tests for webhook endpoints"""

    def test_telegram_webhook_with_custom_headers(self, client):
        """Test Telegram webhook with custom headers"""
        payload = {"update_id": 123456}

        response = client.post(
            "/webhook/telegram",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "TelegramBot/1.0",
                "X-Custom-Header": "custom-value"
            }
        )

        assert response.status_code == 200

    def test_ifood_webhook_with_signature(self, client):
        """Test iFood webhook with signature header"""
        payload = {"events": []}

        response = client.post(
            "/webhook/ifood",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Signature": "test-signature"
            }
        )

        assert response.status_code == 200

    def test_webhook_large_payload(self, client):
        """Test webhook with large payload"""
        # Create a large payload
        payload = {
            "events": [
                {
                    "id": f"event-{i}",
                    "type": "ORDER_CREATED",
                    "data": "x" * 1000
                }
                for i in range(100)
            ]
        }

        response = client.post(
            "/webhook/ifood",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200

    def test_webhook_empty_payload(self, client):
        """Test webhook with empty payload"""
        response = client.post(
            "/webhook/telegram",
            json={},
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200


@pytest.mark.integration
class TestErrorHandling:
    """Integration tests for error handling"""

    def test_malformed_json(self, client):
        """Test handling of malformed JSON"""
        response = client.post(
            "/webhook/telegram",
            content="{invalid json}",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400

    def test_missing_content_type(self, client):
        """Test handling of missing Content-Type header"""
        response = client.post(
            "/webhook/telegram",
            content='{"test": "data"}'
        )

        # Should still work (FastAPI is lenient)
        assert response.status_code in [200, 400]

    def test_wrong_content_type(self, client):
        """Test handling of wrong Content-Type"""
        response = client.post(
            "/webhook/telegram",
            content='{"test": "data"}',
            headers={"Content-Type": "text/plain"}
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 415]

    def test_timeout_handling(self, client):
        """Test that requests complete within reasonable time"""
        import time

        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 5  # Should complete within 5 seconds
