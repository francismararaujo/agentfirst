"""Unit tests for CloudWatch Monitoring"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app.core.monitoring import (
    CloudWatchConfig,
    CloudWatchLogger,
    CloudWatchMetrics,
    CloudWatchAlarms,
    PerformanceTracker,
)


@pytest.mark.unit
class TestCloudWatchConfig:
    """Tests for CloudWatchConfig"""

    def test_config_creation_with_defaults(self):
        """Test creating config with default values"""
        config = CloudWatchConfig()

        assert config.region == "us-east-1"
        assert config.log_group_prefix == "/aws/lambda/agentfirst"
        assert config.log_retention_days == 30
        assert config.enable_metrics is True
        assert config.enable_dashboards is True
        assert config.namespace == "AgentFirst2"

    def test_config_creation_with_custom_values(self):
        """Test creating config with custom values"""
        config = CloudWatchConfig(
            region="eu-west-1",
            log_group_prefix="/custom/logs",
            log_retention_days=7,
            enable_metrics=False,
            namespace="CustomNamespace",
        )

        assert config.region == "eu-west-1"
        assert config.log_group_prefix == "/custom/logs"
        assert config.log_retention_days == 7
        assert config.enable_metrics is False
        assert config.namespace == "CustomNamespace"


@pytest.mark.unit
class TestCloudWatchLogger:
    """Tests for CloudWatchLogger"""

    @pytest.fixture
    def logger_service(self):
        """Create logger service"""
        config = CloudWatchConfig()
        return CloudWatchLogger(config)

    def test_log_event_info(self, logger_service):
        """Test logging info event"""
        with patch("app.core.monitoring.logger") as mock_logger:
            logger_service.log_event(
                component="test_component",
                event_type="test_event",
                data={"key": "value"},
                level="INFO",
            )

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            log_data = json.loads(call_args)

            assert log_data["component"] == "test_component"
            assert log_data["event_type"] == "test_event"
            assert log_data["level"] == "INFO"

    def test_log_event_error(self, logger_service):
        """Test logging error event"""
        with patch("app.core.monitoring.logger") as mock_logger:
            logger_service.log_event(
                component="test_component",
                event_type="error_event",
                data={"error": "test error"},
                level="ERROR",
            )

            mock_logger.error.assert_called_once()

    def test_log_event_with_correlation_id(self, logger_service):
        """Test logging event with correlation ID"""
        with patch("app.core.monitoring.logger") as mock_logger:
            logger_service.log_event(
                component="test_component",
                event_type="test_event",
                data={},
                correlation_id="corr-123",
            )

            call_args = mock_logger.info.call_args[0][0]
            log_data = json.loads(call_args)

            assert log_data["correlation_id"] == "corr-123"

    def test_log_performance(self, logger_service):
        """Test logging performance metrics"""
        with patch("app.core.monitoring.logger") as mock_logger:
            logger_service.log_performance(
                component="test_component",
                operation="test_operation",
                duration_ms=123.45,
            )

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            log_data = json.loads(call_args)

            assert log_data["event_type"] == "performance"
            assert log_data["operation"] == "test_operation"
            assert log_data["duration_ms"] == 123.45

    def test_log_error(self, logger_service):
        """Test logging error with context"""
        with patch("app.core.monitoring.logger") as mock_logger:
            logger_service.log_error(
                component="test_component",
                error_type="ValueError",
                error_message="Test error message",
                context={"key": "value"},
            )

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            log_data = json.loads(call_args)

            assert log_data["event_type"] == "error"
            assert log_data["error_type"] == "ValueError"
            assert log_data["error_message"] == "Test error message"


@pytest.mark.unit
class TestCloudWatchMetrics:
    """Tests for CloudWatchMetrics"""

    @pytest.fixture
    def metrics_service(self):
        """Create metrics service"""
        config = CloudWatchConfig()
        return CloudWatchMetrics(config)

    def test_put_metric_success(self, metrics_service):
        """Test putting metric successfully"""
        with patch.object(metrics_service.cloudwatch_client, "put_metric_data") as mock_put:
            metrics_service.put_metric(
                metric_name="TestMetric",
                value=42.0,
                unit="Count",
            )

            mock_put.assert_called_once()
            call_args = mock_put.call_args[1]

            assert call_args["Namespace"] == "AgentFirst2"
            assert len(call_args["MetricData"]) == 1
            assert call_args["MetricData"][0]["MetricName"] == "TestMetric"
            assert call_args["MetricData"][0]["Value"] == 42.0

    def test_put_metric_with_dimensions(self, metrics_service):
        """Test putting metric with dimensions"""
        with patch.object(metrics_service.cloudwatch_client, "put_metric_data") as mock_put:
            metrics_service.put_metric(
                metric_name="TestMetric",
                value=42.0,
                dimensions={"Component": "Lambda", "Operation": "ProcessMessage"},
            )

            call_args = mock_put.call_args[1]
            dimensions = call_args["MetricData"][0]["Dimensions"]

            assert len(dimensions) == 2
            assert any(d["Name"] == "Component" for d in dimensions)

    def test_put_metric_disabled(self, metrics_service):
        """Test putting metric when disabled"""
        metrics_service.config.enable_metrics = False

        with patch.object(metrics_service.cloudwatch_client, "put_metric_data") as mock_put:
            metrics_service.put_metric(
                metric_name="TestMetric",
                value=42.0,
            )

            mock_put.assert_not_called()

    def test_put_message_count(self, metrics_service):
        """Test putting message count metric"""
        with patch.object(metrics_service.cloudwatch_client, "put_metric_data") as mock_put:
            metrics_service.put_message_count("user@example.com", count=5)

            call_args = mock_put.call_args[1]
            assert call_args["MetricData"][0]["MetricName"] == "MessageCount"
            assert call_args["MetricData"][0]["Value"] == 5

    def test_put_latency(self, metrics_service):
        """Test putting latency metric"""
        with patch.object(metrics_service.cloudwatch_client, "put_metric_data") as mock_put:
            metrics_service.put_latency("ProcessMessage", 123.45)

            call_args = mock_put.call_args[1]
            assert call_args["MetricData"][0]["MetricName"] == "Latency"
            assert call_args["MetricData"][0]["Value"] == 123.45
            assert call_args["MetricData"][0]["Unit"] == "Milliseconds"

    def test_put_error_count(self, metrics_service):
        """Test putting error count metric"""
        with patch.object(metrics_service.cloudwatch_client, "put_metric_data") as mock_put:
            metrics_service.put_error_count("ValueError")

            call_args = mock_put.call_args[1]
            assert call_args["MetricData"][0]["MetricName"] == "ErrorCount"
            assert call_args["MetricData"][0]["Value"] == 1

    def test_put_usage_percentage(self, metrics_service):
        """Test putting usage percentage metric"""
        with patch.object(metrics_service.cloudwatch_client, "put_metric_data") as mock_put:
            metrics_service.put_usage_percentage("user@example.com", 75.5)

            call_args = mock_put.call_args[1]
            assert call_args["MetricData"][0]["MetricName"] == "UsagePercentage"
            assert call_args["MetricData"][0]["Value"] == 75.5
            assert call_args["MetricData"][0]["Unit"] == "Percent"

    def test_put_queue_depth(self, metrics_service):
        """Test putting queue depth metric"""
        with patch.object(metrics_service.cloudwatch_client, "put_metric_data") as mock_put:
            metrics_service.put_queue_depth("events-queue", 150)

            call_args = mock_put.call_args[1]
            assert call_args["MetricData"][0]["MetricName"] == "QueueDepth"
            assert call_args["MetricData"][0]["Value"] == 150

    def test_put_processing_time(self, metrics_service):
        """Test putting processing time metric"""
        with patch.object(metrics_service.cloudwatch_client, "put_metric_data") as mock_put:
            metrics_service.put_processing_time("ProcessOrder", 456.78, status="Success")

            call_args = mock_put.call_args[1]
            assert call_args["MetricData"][0]["MetricName"] == "ProcessingTime"
            assert call_args["MetricData"][0]["Value"] == 456.78


@pytest.mark.unit
class TestCloudWatchAlarms:
    """Tests for CloudWatchAlarms"""

    @pytest.fixture
    def alarms_service(self):
        """Create alarms service"""
        config = CloudWatchConfig()
        return CloudWatchAlarms(config)

    def test_create_alarm_success(self, alarms_service):
        """Test creating alarm successfully"""
        with patch.object(alarms_service.cloudwatch_client, "put_metric_alarm") as mock_put:
            alarms_service.create_alarm(
                alarm_name="test-alarm",
                metric_name="TestMetric",
                threshold=100.0,
            )

            mock_put.assert_called_once()
            call_args = mock_put.call_args[1]

            assert call_args["AlarmName"] == "test-alarm"
            assert call_args["MetricName"] == "TestMetric"
            assert call_args["Threshold"] == 100.0

    def test_create_lambda_error_alarm(self, alarms_service):
        """Test creating Lambda error alarm"""
        with patch.object(alarms_service.cloudwatch_client, "put_metric_alarm") as mock_put:
            alarms_service.create_lambda_error_alarm("my-function", threshold=5)

            call_args = mock_put.call_args[1]
            assert call_args["AlarmName"] == "my-function-errors"
            assert call_args["MetricName"] == "Errors"
            assert call_args["Threshold"] == 5

    def test_create_lambda_duration_alarm(self, alarms_service):
        """Test creating Lambda duration alarm"""
        with patch.object(alarms_service.cloudwatch_client, "put_metric_alarm") as mock_put:
            alarms_service.create_lambda_duration_alarm("my-function", threshold_ms=30000)

            call_args = mock_put.call_args[1]
            assert call_args["AlarmName"] == "my-function-duration"
            assert call_args["MetricName"] == "Duration"
            assert call_args["Threshold"] == 30000

    def test_create_dynamodb_throttle_alarm(self, alarms_service):
        """Test creating DynamoDB throttle alarm"""
        with patch.object(alarms_service.cloudwatch_client, "put_metric_alarm") as mock_put:
            alarms_service.create_dynamodb_throttle_alarm("users-table")

            call_args = mock_put.call_args[1]
            assert call_args["AlarmName"] == "users-table-throttle"
            assert call_args["MetricName"] == "UserErrors"

    def test_create_sqs_queue_depth_alarm(self, alarms_service):
        """Test creating SQS queue depth alarm"""
        with patch.object(alarms_service.cloudwatch_client, "put_metric_alarm") as mock_put:
            alarms_service.create_sqs_queue_depth_alarm("events-queue", threshold=1000)

            call_args = mock_put.call_args[1]
            assert call_args["AlarmName"] == "events-queue-depth"
            assert call_args["MetricName"] == "ApproximateNumberOfMessagesVisible"
            assert call_args["Threshold"] == 1000


@pytest.mark.unit
class TestPerformanceTracker:
    """Tests for PerformanceTracker"""

    @pytest.fixture
    def tracker(self):
        """Create performance tracker"""
        config = CloudWatchConfig()
        metrics = CloudWatchMetrics(config)
        logger_service = CloudWatchLogger(config)
        return PerformanceTracker(metrics, logger_service)

    def test_track_operation_success(self, tracker):
        """Test tracking successful operation"""
        with patch.object(tracker.metrics.cloudwatch_client, "put_metric_data"):
            with tracker.track_operation("test_operation"):
                pass

    def test_track_operation_with_correlation_id(self, tracker):
        """Test tracking operation with correlation ID"""
        with patch.object(tracker.metrics.cloudwatch_client, "put_metric_data"):
            with tracker.track_operation(
                "test_operation",
                correlation_id="corr-123",
            ):
                pass
