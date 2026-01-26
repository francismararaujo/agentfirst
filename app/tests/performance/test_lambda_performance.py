"""Performance tests for Lambda & API Gateway - Test latency and throughput"""

import pytest
import time
import json
from fastapi.testclient import TestClient
from app.main import app


@pytest.mark.performance
class TestLambdaLatency:
    """Performance tests for Lambda latency"""

    def test_health_check_latency(self, client):
        """Test health check endpoint latency (should be < 100ms)"""
        start = time.time()
        response = client.get("/health")
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        assert elapsed < 100, f"Health check took {elapsed}ms, expected < 100ms"

    def test_status_endpoint_latency(self, client):
        """Test status endpoint latency (should be < 100ms)"""
        start = time.time()
        response = client.get("/status")
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 100, f"Status endpoint took {elapsed}ms, expected < 100ms"

    def test_telegram_webhook_latency(self, client):
        """Test Telegram webhook latency (should be < 500ms)"""
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

        start = time.time()
        response = client.post(
            "/webhook/telegram",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 500, f"Telegram webhook took {elapsed}ms, expected < 500ms"

    def test_ifood_webhook_latency(self, client):
        """Test iFood webhook latency (should be < 500ms)"""
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

        start = time.time()
        response = client.post(
            "/webhook/ifood",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 500, f"iFood webhook took {elapsed}ms, expected < 500ms"


@pytest.mark.performance
class TestLambdaThroughput:
    """Performance tests for Lambda throughput"""

    def test_sequential_requests_throughput(self, client):
        """Test throughput with sequential requests"""
        num_requests = 10
        start = time.time()

        for _ in range(num_requests):
            response = client.get("/health")
            assert response.status_code == 200

        elapsed = time.time() - start
        throughput = num_requests / elapsed

        assert throughput > 10, f"Throughput {throughput} req/s, expected > 10 req/s"

    def test_webhook_throughput(self, client):
        """Test webhook throughput"""
        payload = {"update_id": 123456}
        num_requests = 10
        start = time.time()

        for i in range(num_requests):
            response = client.post(
                "/webhook/telegram",
                json={**payload, "update_id": 123456 + i},
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 200

        elapsed = time.time() - start
        throughput = num_requests / elapsed

        assert throughput > 5, f"Throughput {throughput} req/s, expected > 5 req/s"


@pytest.mark.performance
class TestResponseSize:
    """Performance tests for response sizes"""

    def test_health_check_response_size(self, client):
        """Test health check response size"""
        response = client.get("/health")

        assert response.status_code == 200
        response_size = len(response.content)
        assert response_size < 1000, f"Response size {response_size} bytes, expected < 1000"

    def test_error_response_size(self, client):
        """Test error response size"""
        response = client.post(
            "/webhook/telegram",
            content="invalid",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        response_size = len(response.content)
        assert response_size < 1000, f"Error response size {response_size} bytes, expected < 1000"


@pytest.mark.performance
class TestMemoryUsage:
    """Performance tests for memory usage"""

    def test_large_payload_handling(self, client):
        """Test handling of large payloads"""
        # Create a large payload (1MB)
        large_data = "x" * (1024 * 1024)
        payload = {
            "events": [
                {
                    "id": "event-1",
                    "type": "ORDER_CREATED",
                    "data": large_data
                }
            ]
        }

        start = time.time()
        response = client.post(
            "/webhook/ifood",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 5, f"Large payload took {elapsed}s, expected < 5s"

    def test_many_small_requests(self, client):
        """Test handling of many small requests"""
        num_requests = 100
        start = time.time()

        for _ in range(num_requests):
            response = client.get("/health")
            assert response.status_code == 200

        elapsed = time.time() - start

        assert elapsed < 30, f"100 requests took {elapsed}s, expected < 30s"


@pytest.mark.performance
class TestConcurrency:
    """Performance tests for concurrent requests"""

    def test_sequential_vs_concurrent_latency(self, client):
        """Test latency comparison between sequential and concurrent requests"""
        # Sequential requests
        start = time.time()
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
        sequential_time = time.time() - start

        # Note: TestClient is synchronous, so we can't truly test concurrency
        # This test just ensures sequential requests work
        assert sequential_time < 5, f"Sequential requests took {sequential_time}s"
