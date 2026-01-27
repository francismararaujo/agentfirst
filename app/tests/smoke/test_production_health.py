"""
Smoke tests for Production Health (Phase 13.3)

Tests basic functionality in production environment:
- Health checks
- API endpoints
- Database connectivity
- External integrations
- Performance benchmarks
"""

import pytest
import requests
import time
import json
from datetime import datetime
from typing import Dict, Any


@pytest.mark.smoke
class TestProductionHealth:
    """Smoke tests for production health"""

    @pytest.fixture
    def production_url(self):
        """Production API URL"""
        return "https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod"

    @pytest.fixture
    def timeout(self):
        """Request timeout for production tests"""
        return 30  # 30 seconds timeout

    def test_health_endpoint_responds(self, production_url, timeout):
        """Test health endpoint responds successfully"""
        start_time = time.time()
        
        response = requests.get(f"{production_url}/health", timeout=timeout)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Basic response validation
        assert response.status_code == 200, f"Health endpoint should return 200, got {response.status_code}"
        
        # Response time validation
        assert response_time < 5.0, f"Health endpoint should respond in <5s, took {response_time:.2f}s"
        
        # Content validation
        data = response.json()
        assert "status" in data, "Health response should contain status"
        assert data["status"] == "healthy", f"Status should be healthy, got {data['status']}"
        assert "environment" in data, "Health response should contain environment"
        assert "version" in data, "Health response should contain version"

    def test_status_endpoint_responds(self, production_url, timeout):
        """Test status endpoint responds successfully"""
        start_time = time.time()
        
        response = requests.get(f"{production_url}/status", timeout=timeout)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Basic response validation
        assert response.status_code == 200, f"Status endpoint should return 200, got {response.status_code}"
        
        # Response time validation
        assert response_time < 5.0, f"Status endpoint should respond in <5s, took {response_time:.2f}s"
        
        # Content validation
        data = response.json()
        assert "status" in data, "Status response should contain status"
        assert data["status"] == "running", f"Status should be running, got {data['status']}"
        assert "environment" in data, "Status response should contain environment"
        assert data["environment"] == "production", f"Environment should be production, got {data['environment']}"

    def test_docs_examples_endpoint(self, production_url, timeout):
        """Test documentation examples endpoint"""
        response = requests.get(f"{production_url}/docs/examples", timeout=timeout)
        
        assert response.status_code == 200, f"Docs examples should return 200, got {response.status_code}"
        
        data = response.json()
        assert "title" in data, "Docs examples should contain title"
        assert "examples" in data, "Docs examples should contain examples"
        assert "integration_patterns" in data, "Docs examples should contain integration patterns"

    def test_openapi_json_endpoint(self, production_url, timeout):
        """Test OpenAPI JSON endpoint"""
        response = requests.get(f"{production_url}/openapi.json", timeout=timeout)
        
        assert response.status_code == 200, f"OpenAPI JSON should return 200, got {response.status_code}"
        assert response.headers.get("content-type") == "application/json"
        
        data = response.json()
        assert "openapi" in data, "OpenAPI spec should contain openapi version"
        assert "info" in data, "OpenAPI spec should contain info"
        assert "paths" in data, "OpenAPI spec should contain paths"

    def test_swagger_ui_accessible(self, production_url, timeout):
        """Test Swagger UI is accessible"""
        response = requests.get(f"{production_url}/docs", timeout=timeout)
        
        assert response.status_code == 200, f"Swagger UI should return 200, got {response.status_code}"
        assert "text/html" in response.headers.get("content-type", "")

    def test_redoc_accessible(self, production_url, timeout):
        """Test ReDoc is accessible"""
        response = requests.get(f"{production_url}/redoc", timeout=timeout)
        
        assert response.status_code == 200, f"ReDoc should return 200, got {response.status_code}"
        assert "text/html" in response.headers.get("content-type", "")

    def test_telegram_webhook_endpoint_exists(self, production_url, timeout):
        """Test Telegram webhook endpoint exists (should reject invalid requests)"""
        # Send invalid request (should be rejected but endpoint should exist)
        response = requests.post(
            f"{production_url}/webhook/telegram",
            json={"invalid": "data"},
            timeout=timeout
        )
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404, "Telegram webhook endpoint should exist"
        
        # Should return 400 for invalid data (expected behavior)
        assert response.status_code in [400, 422], f"Invalid request should return 400/422, got {response.status_code}"

    def test_ifood_webhook_endpoint_exists(self, production_url, timeout):
        """Test iFood webhook endpoint exists (should reject invalid requests)"""
        # Send invalid request (should be rejected but endpoint should exist)
        response = requests.post(
            f"{production_url}/webhook/ifood",
            json={"invalid": "data"},
            timeout=timeout
        )
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404, "iFood webhook endpoint should exist"
        
        # Should return 400 or 401 for invalid data/signature (expected behavior)
        assert response.status_code in [400, 401, 422], f"Invalid request should return 400/401/422, got {response.status_code}"

    def test_cors_headers(self, production_url, timeout):
        """Test CORS headers are properly configured"""
        response = requests.options(f"{production_url}/health", timeout=timeout)
        
        # CORS headers should be present
        headers = response.headers
        assert "access-control-allow-origin" in headers or response.status_code == 405, "CORS headers should be configured"

    def test_security_headers(self, production_url, timeout):
        """Test security headers are present"""
        response = requests.get(f"{production_url}/health", timeout=timeout)
        
        headers = response.headers
        
        # Check for basic security headers
        security_headers = [
            "x-request-id",  # Custom request ID
            "x-process-time"  # Custom process time
        ]
        
        for header in security_headers:
            assert header in headers, f"Security header {header} should be present"

    def test_response_format_consistency(self, production_url, timeout):
        """Test response format consistency across endpoints"""
        endpoints = ["/health", "/status", "/docs/examples"]
        
        for endpoint in endpoints:
            response = requests.get(f"{production_url}{endpoint}", timeout=timeout)
            
            assert response.status_code == 200, f"Endpoint {endpoint} should return 200"
            assert response.headers.get("content-type") == "application/json", f"Endpoint {endpoint} should return JSON"
            
            # Should be valid JSON
            try:
                data = response.json()
                assert isinstance(data, dict), f"Endpoint {endpoint} should return JSON object"
            except json.JSONDecodeError:
                pytest.fail(f"Endpoint {endpoint} should return valid JSON")

    def test_error_handling(self, production_url, timeout):
        """Test error handling for non-existent endpoints"""
        response = requests.get(f"{production_url}/nonexistent", timeout=timeout)
        
        assert response.status_code == 404, f"Non-existent endpoint should return 404, got {response.status_code}"

    def test_rate_limiting_headers(self, production_url, timeout):
        """Test rate limiting headers (if implemented)"""
        response = requests.get(f"{production_url}/health", timeout=timeout)
        
        # Rate limiting headers are optional but good to check
        rate_limit_headers = ["x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset"]
        
        # If any rate limiting header is present, log it (not required for test to pass)
        for header in rate_limit_headers:
            if header in response.headers:
                print(f"Rate limiting header found: {header} = {response.headers[header]}")


@pytest.mark.smoke
class TestProductionPerformance:
    """Smoke tests for production performance"""

    @pytest.fixture
    def production_url(self):
        """Production API URL"""
        return "https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod"

    def test_health_endpoint_performance(self, production_url):
        """Test health endpoint performance"""
        response_times = []
        
        # Make 5 requests to get average response time
        for _ in range(5):
            start_time = time.time()
            response = requests.get(f"{production_url}/health", timeout=10)
            end_time = time.time()
            
            assert response.status_code == 200, "Health endpoint should be available"
            response_times.append(end_time - start_time)
        
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        # Performance assertions
        assert avg_response_time < 2.0, f"Average response time should be <2s, got {avg_response_time:.2f}s"
        assert max_response_time < 5.0, f"Max response time should be <5s, got {max_response_time:.2f}s"

    def test_concurrent_requests(self, production_url):
        """Test handling of concurrent requests"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                start_time = time.time()
                response = requests.get(f"{production_url}/health", timeout=10)
                end_time = time.time()
                
                results.put({
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                })
            except Exception as e:
                results.put({
                    "status_code": None,
                    "response_time": None,
                    "success": False,
                    "error": str(e)
                })
        
        # Create 10 concurrent threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Collect results
        all_results = []
        while not results.empty():
            all_results.append(results.get())
        
        # Validate results
        assert len(all_results) == 10, "Should have 10 results"
        
        successful_requests = [r for r in all_results if r["success"]]
        assert len(successful_requests) >= 8, f"At least 8/10 requests should succeed, got {len(successful_requests)}"
        
        # Performance validation
        assert total_time < 15.0, f"10 concurrent requests should complete in <15s, took {total_time:.2f}s"

    def test_payload_size_limits(self, production_url):
        """Test payload size handling"""
        # Test small payload (should work)
        small_payload = {"test": "data"}
        response = requests.post(
            f"{production_url}/webhook/telegram",
            json=small_payload,
            timeout=10
        )
        
        # Should not fail due to payload size (may fail for other reasons)
        assert response.status_code != 413, "Small payload should not exceed size limits"
        
        # Test large payload (should be rejected or handled gracefully)
        large_payload = {"test": "x" * 1000000}  # 1MB of data
        try:
            response = requests.post(
                f"{production_url}/webhook/telegram",
                json=large_payload,
                timeout=30
            )
            
            # Should either reject (413) or handle gracefully
            assert response.status_code in [400, 413, 422], "Large payload should be handled appropriately"
        except requests.exceptions.Timeout:
            # Timeout is acceptable for very large payloads
            pass


@pytest.mark.smoke
class TestProductionIntegrations:
    """Smoke tests for production integrations"""

    @pytest.fixture
    def production_url(self):
        """Production API URL"""
        return "https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod"

    def test_aws_services_connectivity(self, production_url):
        """Test connectivity to AWS services (indirect)"""
        # Test that endpoints requiring AWS services work
        response = requests.get(f"{production_url}/health", timeout=10)
        
        assert response.status_code == 200, "Health endpoint should work (requires AWS services)"
        
        data = response.json()
        assert "status" in data, "Health response should contain status (requires DynamoDB/other AWS services)"

    def test_telegram_webhook_structure(self, production_url):
        """Test Telegram webhook accepts proper structure"""
        # Valid Telegram update structure
        telegram_update = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Test"
                },
                "chat": {
                    "id": 987654321,
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "test message"
            }
        }
        
        response = requests.post(
            f"{production_url}/webhook/telegram",
            json=telegram_update,
            timeout=10
        )
        
        # Should accept the structure (may fail for other reasons like authentication)
        assert response.status_code != 422, "Valid Telegram structure should not cause validation errors"

    def test_ifood_webhook_signature_validation(self, production_url):
        """Test iFood webhook signature validation"""
        # Valid iFood event structure (without proper signature)
        ifood_event = {
            "eventId": "evt_test123",
            "eventType": "order.placed",
            "timestamp": datetime.now().isoformat() + "Z",
            "merchantId": "test_merchant",
            "data": {
                "orderId": "order_test123",
                "totalAmount": 50.00
            }
        }
        
        response = requests.post(
            f"{production_url}/webhook/ifood",
            json=ifood_event,
            timeout=10
        )
        
        # Should reject due to missing/invalid signature (expected behavior)
        assert response.status_code in [400, 401], f"iFood webhook should validate signatures, got {response.status_code}"

    def test_bedrock_integration_indirect(self, production_url):
        """Test Bedrock integration (indirect through health check)"""
        # The health endpoint may check Bedrock connectivity
        response = requests.get(f"{production_url}/health", timeout=15)
        
        assert response.status_code == 200, "Health check should pass (may include Bedrock connectivity)"
        
        data = response.json()
        assert data["status"] == "healthy", "System should be healthy (including Bedrock integration)"


@pytest.mark.smoke
class TestProductionSecurity:
    """Smoke tests for production security"""

    @pytest.fixture
    def production_url(self):
        """Production API URL"""
        return "https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod"

    def test_https_enforcement(self, production_url):
        """Test HTTPS is enforced"""
        # The production URL should be HTTPS
        assert production_url.startswith("https://"), "Production should use HTTPS"
        
        # Test that HTTP redirects to HTTPS (if applicable)
        http_url = production_url.replace("https://", "http://")
        try:
            response = requests.get(f"{http_url}/health", timeout=10, allow_redirects=False)
            # Should either redirect to HTTPS or be unreachable
            if response.status_code in [301, 302, 308]:
                assert response.headers.get("location", "").startswith("https://"), "HTTP should redirect to HTTPS"
        except requests.exceptions.ConnectionError:
            # HTTP not available (good - HTTPS only)
            pass

    def test_sql_injection_protection(self, production_url):
        """Test SQL injection protection"""
        # Try SQL injection in various parameters
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ]
        
        for payload in sql_payloads:
            # Test in URL parameters
            response = requests.get(
                f"{production_url}/health",
                params={"test": payload},
                timeout=10
            )
            
            # Should not cause server errors
            assert response.status_code != 500, f"SQL injection payload should not cause server error: {payload}"

    def test_xss_protection(self, production_url):
        """Test XSS protection"""
        # Try XSS payloads
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            response = requests.post(
                f"{production_url}/webhook/telegram",
                json={"message": {"text": payload}},
                timeout=10
            )
            
            # Should not reflect the payload in response
            if response.status_code == 200:
                response_text = response.text.lower()
                assert "<script>" not in response_text, "XSS payload should not be reflected"
                assert "javascript:" not in response_text, "XSS payload should not be reflected"

    def test_request_size_limits(self, production_url):
        """Test request size limits"""
        # Very large request body
        large_data = "x" * (10 * 1024 * 1024)  # 10MB
        
        try:
            response = requests.post(
                f"{production_url}/webhook/telegram",
                data=large_data,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            # Should reject large requests
            assert response.status_code in [400, 413, 422], "Large requests should be rejected"
        except requests.exceptions.Timeout:
            # Timeout is acceptable for very large requests
            pass
        except requests.exceptions.ConnectionError:
            # Connection error is acceptable (request too large)
            pass

    def test_method_not_allowed(self, production_url):
        """Test method restrictions"""
        # Test unsupported methods on endpoints
        unsupported_methods = ["PUT", "DELETE", "PATCH"]
        
        for method in unsupported_methods:
            response = requests.request(
                method,
                f"{production_url}/health",
                timeout=10
            )
            
            # Should return 405 Method Not Allowed
            assert response.status_code == 405, f"Method {method} should not be allowed on /health"