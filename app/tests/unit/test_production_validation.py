"""
Unit tests for Production Validation (Phase 13.3)

Tests the production validation script and components:
- Validation test functions
- Report generation
- Error handling
- Performance benchmarks
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the production validation script
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from scripts.production_validation import ProductionValidator, ValidationResult


@pytest.mark.unit
class TestValidationResult:
    """Unit tests for ValidationResult"""

    def test_validation_result_creation(self):
        """Test ValidationResult creation"""
        result = ValidationResult(
            test_name="test_health",
            success=True,
            message="Health check passed",
            duration=1.5,
            details={"status_code": 200}
        )
        
        assert result.test_name == "test_health"
        assert result.success is True
        assert result.message == "Health check passed"
        assert result.duration == 1.5
        assert result.details == {"status_code": 200}

    def test_validation_result_defaults(self):
        """Test ValidationResult with default values"""
        result = ValidationResult(
            test_name="test_basic",
            success=False,
            message="Test failed",
            duration=0.5
        )
        
        assert result.details is None


@pytest.mark.unit
class TestProductionValidator:
    """Unit tests for ProductionValidator"""

    @pytest.fixture
    def validator(self):
        """Create ProductionValidator instance"""
        return ProductionValidator("http://testserver")

    @pytest.fixture
    def mock_response(self):
        """Create mock HTTP response"""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"status": "healthy"}
        response.headers = {"content-type": "application/json"}
        response.elapsed.total_seconds.return_value = 0.5
        return response

    def test_validator_initialization(self, validator):
        """Test validator initialization"""
        assert validator.base_url == "http://testserver"
        assert validator.results == []
        assert validator.session is not None

    def test_run_test_success(self, validator):
        """Test run_test with successful test"""
        def mock_test():
            return True, "Test passed", {"key": "value"}
        
        result = validator.run_test(mock_test, "Mock Test")
        
        assert result.test_name == "Mock Test"
        assert result.success is True
        assert result.message == "Test passed"
        assert result.details == {"key": "value"}
        assert result.duration > 0

    def test_run_test_failure(self, validator):
        """Test run_test with failed test"""
        def mock_test():
            return False, "Test failed", {}
        
        result = validator.run_test(mock_test, "Mock Test")
        
        assert result.test_name == "Mock Test"
        assert result.success is False
        assert result.message == "Test failed"

    def test_run_test_exception(self, validator):
        """Test run_test with exception"""
        def mock_test():
            raise ValueError("Test exception")
        
        result = validator.run_test(mock_test, "Mock Test")
        
        assert result.test_name == "Mock Test"
        assert result.success is False
        assert "Exception: Test exception" in result.message

    def test_run_test_boolean_return(self, validator):
        """Test run_test with boolean return"""
        def mock_test():
            return True
        
        result = validator.run_test(mock_test, "Mock Test")
        
        assert result.success is True
        assert result.message == "Test completed"

    @patch('requests.Session.get')
    def test_validate_health_endpoints(self, mock_get, validator, mock_response):
        """Test validate_health_endpoints"""
        mock_get.return_value = mock_response
        
        success, message, details = validator.validate_health_endpoints()
        
        assert success is True
        assert "3/3 endpoints healthy" in message
        assert "/health" in details
        assert "/status" in details
        assert "/docs/examples" in details

    @patch('requests.Session.get')
    def test_validate_health_endpoints_failure(self, mock_get, validator):
        """Test validate_health_endpoints with failures"""
        # Mock failed response
        failed_response = Mock()
        failed_response.status_code = 500
        failed_response.elapsed.total_seconds.return_value = 1.0
        mock_get.return_value = failed_response
        
        success, message, details = validator.validate_health_endpoints()
        
        assert success is False
        assert "0/3 endpoints healthy" in message

    @patch('requests.Session.get')
    def test_validate_performance(self, mock_get, validator, mock_response):
        """Test validate_performance"""
        mock_get.return_value = mock_response
        
        success, message, details = validator.validate_performance()
        
        assert success is True
        assert "Avg:" in message
        assert "Max:" in message
        assert "average_response_time" in details
        assert "max_response_time" in details

    @patch('requests.Session.get')
    def test_validate_performance_slow(self, mock_get, validator):
        """Test validate_performance with slow responses"""
        # Mock slow response
        slow_response = Mock()
        slow_response.status_code = 200
        slow_response.elapsed.total_seconds.return_value = 10.0  # Very slow
        mock_get.return_value = slow_response
        
        success, message, details = validator.validate_performance()
        
        assert success is False  # Should fail due to slow response
        assert details["average_response_time"] > 5.0

    @patch('requests.Session.get')
    def test_validate_api_documentation(self, mock_get, validator, mock_response):
        """Test validate_api_documentation"""
        mock_get.return_value = mock_response
        
        success, message, details = validator.validate_api_documentation()
        
        assert success is True
        assert "3/3 documentation endpoints accessible" in message
        assert "/docs" in details
        assert "/redoc" in details
        assert "/openapi.json" in details

    @patch('requests.Session.post')
    def test_validate_webhook_endpoints(self, mock_post, validator):
        """Test validate_webhook_endpoints"""
        # Mock webhook response (should reject invalid data but endpoint exists)
        webhook_response = Mock()
        webhook_response.status_code = 400  # Bad request, but endpoint exists
        mock_post.return_value = webhook_response
        
        success, message, details = validator.validate_webhook_endpoints()
        
        assert success is True
        assert "2/2 webhook endpoints exist" in message
        assert "/webhook/telegram" in details
        assert "/webhook/ifood" in details

    @patch('requests.Session.get')
    def test_validate_security_headers(self, mock_get, validator):
        """Test validate_security_headers"""
        # Mock response with security headers
        secure_response = Mock()
        secure_response.status_code = 200
        secure_response.headers = {
            "x-request-id": "req_123",
            "x-process-time": "0.5",
            "content-type": "application/json"
        }
        mock_get.return_value = secure_response
        
        validator.base_url = "https://testserver"  # HTTPS
        
        success, message, details = validator.validate_security_headers()
        
        assert success is True
        assert "security checks passed" in message
        assert details["https_only"] is True
        assert details["has_request_id"] is True

    @patch('requests.Session.get')
    def test_validate_concurrent_requests(self, mock_get, validator, mock_response):
        """Test validate_concurrent_requests"""
        mock_get.return_value = mock_response
        
        success, message, details = validator.validate_concurrent_requests()
        
        assert success is True
        assert "concurrent requests successful" in message
        assert details["total_requests"] == 10
        assert details["success_rate"] >= 0.8

    @patch('requests.Session.post')
    def test_validate_telegram_integration(self, mock_post, validator):
        """Test validate_telegram_integration"""
        # Mock successful structure validation
        telegram_response = Mock()
        telegram_response.status_code = 200  # Structure is valid
        telegram_response.headers = {"content-type": "application/json"}
        mock_post.return_value = telegram_response
        
        success, message, details = validator.validate_telegram_integration()
        
        assert success is True
        assert "Telegram structure validation: PASS" in message
        assert details["structure_valid"] is True

    @patch('requests.Session.get')
    @patch('requests.Session.post')
    def test_validate_error_handling(self, mock_post, mock_get, validator):
        """Test validate_error_handling"""
        # Mock 404 response for non-existent endpoint
        not_found_response = Mock()
        not_found_response.status_code = 404
        mock_get.return_value = not_found_response
        
        # Mock 400 response for invalid JSON
        bad_request_response = Mock()
        bad_request_response.status_code = 400
        mock_post.return_value = bad_request_response
        
        success, message, details = validator.validate_error_handling()
        
        assert success is True
        assert "error responses correct" in message

    def test_generate_report(self, validator):
        """Test generate_report"""
        # Add some mock results
        validator.results = [
            ValidationResult("test1", True, "Passed", 1.0, {"key": "value"}),
            ValidationResult("test2", False, "Failed", 0.5, {}),
            ValidationResult("test3", True, "Passed", 2.0, {})
        ]
        
        report = validator.generate_report()
        
        assert "timestamp" in report
        assert report["base_url"] == validator.base_url
        assert report["summary"]["total_tests"] == 3
        assert report["summary"]["passed_tests"] == 2
        assert report["summary"]["failed_tests"] == 1
        assert report["summary"]["success_rate"] == 200/3  # 66.67%
        assert len(report["results"]) == 3

    def test_run_quick_validation(self, validator):
        """Test run_quick_validation"""
        # Mock all test methods to return success
        with patch.object(validator, 'validate_health_endpoints', return_value=(True, "OK", {})), \
             patch.object(validator, 'validate_performance', return_value=(True, "OK", {})), \
             patch.object(validator, 'validate_webhook_endpoints', return_value=(True, "OK", {})), \
             patch.object(validator, 'validate_security_headers', return_value=(True, "OK", {})):
            
            results = validator.run_quick_validation()
            
            assert len(results) == 4
            assert all(result.success for result in results)

    def test_run_full_validation(self, validator):
        """Test run_full_validation"""
        # Mock all test methods to return success
        test_methods = [
            'validate_health_endpoints',
            'validate_performance', 
            'validate_api_documentation',
            'validate_webhook_endpoints',
            'validate_security_headers',
            'validate_concurrent_requests',
            'validate_telegram_integration',
            'validate_error_handling'
        ]
        
        patches = []
        for method in test_methods:
            patches.append(patch.object(validator, method, return_value=(True, "OK", {})))
        
        with patch.multiple(validator, **{method: Mock(return_value=(True, "OK", {})) for method in test_methods}):
            results = validator.run_full_validation()
            
            assert len(results) == 8
            assert all(result.success for result in results)

    def test_print_summary_excellent(self, validator, capsys):
        """Test print_summary with excellent results"""
        # Add results with 95% success rate
        validator.results = [
            ValidationResult("test1", True, "Passed", 1.0),
            ValidationResult("test2", True, "Passed", 1.0),
            ValidationResult("test3", True, "Passed", 1.0),
            ValidationResult("test4", True, "Passed", 1.0),
            ValidationResult("test5", False, "Failed", 1.0)  # 1 failure out of 5 = 80%
        ]
        
        validator.print_summary()
        
        captured = capsys.readouterr()
        assert "VALIDATION SUMMARY" in captured.out
        assert "Total Tests: 5" in captured.out
        assert "Passed: 4" in captured.out
        assert "Failed: 1" in captured.out

    def test_print_summary_with_failures(self, validator, capsys):
        """Test print_summary with failures"""
        validator.results = [
            ValidationResult("test1", True, "Passed", 1.0),
            ValidationResult("test2", False, "Failed test", 1.0),
            ValidationResult("test3", False, "Another failure", 1.0)
        ]
        
        validator.print_summary()
        
        captured = capsys.readouterr()
        assert "FAILED TESTS:" in captured.out
        assert "test2: Failed test" in captured.out
        assert "test3: Another failure" in captured.out


@pytest.mark.unit
class TestProductionValidatorEdgeCases:
    """Unit tests for edge cases and error conditions"""

    @pytest.fixture
    def validator(self):
        """Create ProductionValidator instance"""
        return ProductionValidator("http://testserver")

    @patch('requests.Session.get')
    def test_validate_health_endpoints_timeout(self, mock_get, validator):
        """Test validate_health_endpoints with timeout"""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        
        success, message, details = validator.validate_health_endpoints()
        
        assert success is False
        assert "0/3 endpoints healthy" in message

    @patch('requests.Session.get')
    def test_validate_performance_no_responses(self, mock_get, validator):
        """Test validate_performance with no successful responses"""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        success, message, details = validator.validate_performance()
        
        assert success is False
        assert message == "No successful requests"

    @patch('requests.Session.get')
    def test_validate_concurrent_requests_partial_failure(self, mock_get, validator):
        """Test validate_concurrent_requests with partial failures"""
        # Mock responses: some succeed, some fail
        responses = []
        for i in range(10):
            if i < 7:  # 7 succeed
                response = Mock()
                response.status_code = 200
                responses.append(response)
            else:  # 3 fail
                responses.append(Exception("Connection failed"))
        
        mock_get.side_effect = responses
        
        success, message, details = validator.validate_concurrent_requests()
        
        # Should still pass with 70% success rate (>= 80% required for full success)
        # But this tests the partial failure scenario
        assert details["total_requests"] == 10

    def test_generate_report_empty_results(self, validator):
        """Test generate_report with no results"""
        report = validator.generate_report()
        
        assert report["summary"]["total_tests"] == 0
        assert report["summary"]["passed_tests"] == 0
        assert report["summary"]["failed_tests"] == 0
        assert report["summary"]["success_rate"] == 0
        assert report["results"] == []

    @patch('requests.Session.post')
    def test_validate_telegram_integration_invalid_structure(self, mock_post, validator):
        """Test validate_telegram_integration with invalid structure"""
        # Mock 422 response (validation error)
        validation_error_response = Mock()
        validation_error_response.status_code = 422
        validation_error_response.headers = {"content-type": "application/json"}
        mock_post.return_value = validation_error_response
        
        success, message, details = validator.validate_telegram_integration()
        
        assert success is False
        assert "Telegram structure validation: FAIL" in message
        assert details["structure_valid"] is False

    @patch('requests.Session.get')
    def test_validate_security_headers_insecure(self, mock_get, validator):
        """Test validate_security_headers with insecure configuration"""
        # Mock response without security headers
        insecure_response = Mock()
        insecure_response.status_code = 200
        insecure_response.headers = {}  # No security headers
        mock_get.return_value = insecure_response
        
        validator.base_url = "http://testserver"  # HTTP (not HTTPS)
        
        success, message, details = validator.validate_security_headers()
        
        # Should fail or have low score due to missing security features
        assert details["https_only"] is False
        assert details["has_request_id"] is False

    def test_run_test_with_string_return(self, validator):
        """Test run_test with string return value"""
        def mock_test():
            return "Test completed successfully"
        
        result = validator.run_test(mock_test, "Mock Test")
        
        assert result.success is True
        assert result.message == "Test completed successfully"

    def test_run_test_with_none_return(self, validator):
        """Test run_test with None return value"""
        def mock_test():
            return None
        
        result = validator.run_test(mock_test, "Mock Test")
        
        assert result.success is True
        assert result.message == "None"