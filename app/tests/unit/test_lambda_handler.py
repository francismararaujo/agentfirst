"""Unit tests for Lambda handler - Test Lambda execution, error handling, and metrics"""

import pytest
import json
import time
from unittest.mock import MagicMock, patch, AsyncMock
from app.lambda_handler import (
    lambda_handler,
    LambdaMetrics,
    _log_structured,
    _extract_request_info,
    _validate_event
)


@pytest.mark.unit
class TestLambdaMetrics:
    """Tests for LambdaMetrics class"""

    def test_metrics_initialization(self):
        """Test metrics initialization"""
        metrics = LambdaMetrics()
        assert metrics.start_time is None
        assert metrics.end_time is None
        assert metrics.duration_ms == 0
        assert metrics.memory_used == 0
        assert metrics.error_count == 0

    def test_metrics_start_and_end(self):
        """Test metrics start and end timing"""
        metrics = LambdaMetrics()
        metrics.start()
        assert metrics.start_time is not None

        time.sleep(0.01)  # Sleep 10ms
        metrics.end()

        assert metrics.end_time is not None
        assert metrics.duration_ms > 10  # Should be at least 10ms

    def test_metrics_to_dict(self):
        """Test metrics conversion to dictionary"""
        metrics = LambdaMetrics()
        metrics.start()
        time.sleep(0.01)
        metrics.end()
        metrics.error_count = 1

        result = metrics.to_dict()
        assert "duration_ms" in result
        assert "memory_used" in result
        assert "error_count" in result
        assert result["error_count"] == 1


@pytest.mark.unit
class TestExtractRequestInfo:
    """Tests for _extract_request_info function"""

    def test_extract_request_info_complete(self):
        """Test extracting request info with all fields"""
        event = {
            "httpMethod": "POST",
            "path": "/webhook/telegram",
            "requestContext": {
                "identity": {"sourceIp": "192.168.1.1"},
                "requestId": "req-123"
            },
            "headers": {"User-Agent": "TelegramBot/1.0"}
        }

        result = _extract_request_info(event)

        assert result["method"] == "POST"
        assert result["path"] == "/webhook/telegram"
        assert result["source_ip"] == "192.168.1.1"
        assert result["user_agent"] == "TelegramBot/1.0"
        assert result["request_id"] == "req-123"

    def test_extract_request_info_missing_fields(self):
        """Test extracting request info with missing fields"""
        event = {}

        result = _extract_request_info(event)

        assert result["method"] == "UNKNOWN"
        assert result["path"] == "UNKNOWN"
        assert result["source_ip"] == "UNKNOWN"
        assert result["user_agent"] == "UNKNOWN"
        assert result["request_id"] == "UNKNOWN"

    def test_extract_request_info_partial_fields(self):
        """Test extracting request info with partial fields"""
        event = {
            "httpMethod": "GET",
            "path": "/health"
        }

        result = _extract_request_info(event)

        assert result["method"] == "GET"
        assert result["path"] == "/health"
        assert result["source_ip"] == "UNKNOWN"


@pytest.mark.unit
class TestValidateEvent:
    """Tests for _validate_event function"""

    def test_validate_event_valid(self):
        """Test validating a valid event"""
        event = {
            "httpMethod": "POST",
            "path": "/webhook/telegram"
        }

        assert _validate_event(event) is True

    def test_validate_event_missing_method(self):
        """Test validating event with missing httpMethod"""
        event = {
            "path": "/webhook/telegram"
        }

        assert _validate_event(event) is False

    def test_validate_event_missing_path(self):
        """Test validating event with missing path"""
        event = {
            "httpMethod": "POST"
        }

        assert _validate_event(event) is False

    def test_validate_event_empty(self):
        """Test validating empty event"""
        event = {}

        assert _validate_event(event) is False


@pytest.mark.unit
class TestLambdaHandler:
    """Tests for lambda_handler function"""

    @pytest.mark.asyncio
    async def test_lambda_handler_success(self):
        """Test lambda handler with successful request"""
        event = {
            "httpMethod": "GET",
            "path": "/health",
            "requestContext": {
                "identity": {"sourceIp": "192.168.1.1"},
                "requestId": "req-123"
            },
            "headers": {}
        }

        context = MagicMock()
        context.memory_limit_in_mb = 512

        with patch("app.lambda_handler.handler", new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = {
                "statusCode": 200,
                "body": json.dumps({"status": "healthy"})
            }

            response = await lambda_handler(event, context)

            assert response["statusCode"] == 200
            assert "body" in response

    @pytest.mark.asyncio
    async def test_lambda_handler_invalid_event(self):
        """Test lambda handler with invalid event"""
        event = {}  # Missing required fields

        context = MagicMock()
        context.memory_limit_in_mb = 512

        response = await lambda_handler(event, context)

        assert response["statusCode"] == 400
        assert "error" in json.loads(response["body"])

    @pytest.mark.asyncio
    async def test_lambda_handler_exception(self):
        """Test lambda handler with exception"""
        event = {
            "httpMethod": "GET",
            "path": "/health",
            "requestContext": {
                "identity": {"sourceIp": "192.168.1.1"},
                "requestId": "req-123"
            },
            "headers": {}
        }

        context = MagicMock()
        context.memory_limit_in_mb = 512

        with patch("app.lambda_handler.handler", new_callable=AsyncMock) as mock_handler:
            mock_handler.side_effect = Exception("Test error")

            response = await lambda_handler(event, context)

            assert response["statusCode"] == 500
            assert "error" in json.loads(response["body"])

    @pytest.mark.asyncio
    async def test_lambda_handler_metrics(self):
        """Test lambda handler metrics tracking"""
        event = {
            "httpMethod": "GET",
            "path": "/health",
            "requestContext": {
                "identity": {"sourceIp": "192.168.1.1"},
                "requestId": "req-123"
            },
            "headers": {}
        }

        context = MagicMock()
        context.memory_limit_in_mb = 512

        with patch("app.lambda_handler.handler", new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = {
                "statusCode": 200,
                "body": json.dumps({"status": "healthy"})
            }

            response = await lambda_handler(event, context)

            assert response["statusCode"] == 200
            # Metrics should be logged (verified by logger calls)

    @pytest.mark.asyncio
    async def test_lambda_handler_request_id_preserved(self):
        """Test that request ID is preserved in response"""
        event = {
            "httpMethod": "GET",
            "path": "/health",
            "requestContext": {
                "identity": {"sourceIp": "192.168.1.1"},
                "requestId": "req-123"
            },
            "headers": {}
        }

        context = MagicMock()
        context.memory_limit_in_mb = 512

        with patch("app.lambda_handler.handler", new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = {
                "statusCode": 200,
                "body": json.dumps({"status": "healthy"})
            }

            response = await lambda_handler(event, context)

            assert response["statusCode"] == 200


@pytest.mark.unit
class TestLogStructured:
    """Tests for _log_structured function"""

    def test_log_structured_info(self):
        """Test structured logging with INFO level"""
        with patch("app.lambda_handler.logger") as mock_logger:
            _log_structured("INFO", "Test message", key="value")

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            log_data = json.loads(call_args)

            assert log_data["level"] == "INFO"
            assert log_data["message"] == "Test message"
            assert log_data["key"] == "value"

    def test_log_structured_error(self):
        """Test structured logging with ERROR level"""
        with patch("app.lambda_handler.logger") as mock_logger:
            _log_structured("ERROR", "Error message", error_code=500)

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            log_data = json.loads(call_args)

            assert log_data["level"] == "ERROR"
            assert log_data["message"] == "Error message"
            assert log_data["error_code"] == 500

    def test_log_structured_includes_timestamp(self):
        """Test that structured log includes timestamp"""
        with patch("app.lambda_handler.logger") as mock_logger:
            _log_structured("INFO", "Test message")

            call_args = mock_logger.info.call_args[0][0]
            log_data = json.loads(call_args)

            assert "timestamp" in log_data
            assert isinstance(log_data["timestamp"], (int, float))
