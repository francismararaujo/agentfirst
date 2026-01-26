"""Integration tests for CloudWatch Monitoring"""

import pytest
import json
from unittest.mock import patch
from app.core.monitoring import (
    CloudWatchConfig,
    CloudWatchLogger,
    CloudWatchMetrics,
    CloudWatchAlarms,
    PerformanceTracker,
)


@pytest.mark.integration
class TestMonitoringIntegration:
    """Integration tests for monitoring"""

    @pytest.fixture
    def config(self):
        """Create config"""
        return CloudWatchConfig()

    @pytest.fixture
    def logger_service(self, config):
        """Create logger service"""
        return CloudWatchLogger(config)

    @pytest.fixture
    def metrics_service(self, config):
        """Create metrics service"""
        return CloudWatchMetrics(config)

    @pytest.fixture
    def alarms_service(self, config):
        """Create alarms service"""
        return CloudWatchAlarms(config)

    @pytest.fixture
    def tracker(self, metrics_service, logger_service):
        """Create performance tracker"""
        return PerformanceTracker(metrics_service, logger_service)

    def test_complete_monitoring_workflow(
        self,
        logger_service,
        metrics_service,
        alarms_service,
    ):
        """Test complete monitoring workflow"""
        with patch.object(logger_service.logs_client, "put_log_events"):
            with patch.object(metrics_service.cloudwatch_client, "put_metric_data"):
                with patch.object(alarms_service.cloudwatch_client, "put_metric_alarm"):
                    # Log event
                    logger_service.log_event(
                        component="test_component",
                        event_type="test_event",
                        data={"key": "value"},
                    )

                    # Put metric
                    metrics_service.put_metric(
                        metric_name="TestMetric",
                        value=42.0,
                    )

                    # Create alarm
                    alarms_service.create_alarm(
                        alarm_name="test-alarm",
                        metric_name="TestMetric",
                        threshold=100.0,
                    )

    def test_performance_tracking_workflow(self, tracker):
        """Test performance tracking workflow"""
        with patch.object(tracker.metrics.cloudwatch_client, "put_metric_data"):
            with tracker.track_operation("test_operation"):
                pass

    def test_error_logging_workflow(self, logger_service):
        """Test error logging workflow"""
        with patch("app.core.monitoring.logger"):
            try:
                raise ValueError("Test error")
            except ValueError as e:
                logger_service.log_error(
                    component="test_component",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    context={"operation": "test"},
                )

    def test_metrics_with_dimensions_workflow(self, metrics_service):
        """Test metrics with dimensions workflow"""
        with patch.object(metrics_service.cloudwatch_client, "put_metric_data") as mock_put:
            # Put multiple metrics with different dimensions
            metrics_service.put_message_count("user1@example.com", 5)
            metrics_service.put_message_count("user2@example.com", 3)
            metrics_service.put_latency("ProcessMessage", 123.45)
            metrics_service.put_error_count("ValueError")

            assert mock_put.call_count == 4

    def test_alarm_creation_workflow(self, alarms_service):
        """Test alarm creation workflow"""
        with patch.object(alarms_service.cloudwatch_client, "put_metric_alarm") as mock_put:
            # Create multiple alarms
            alarms_service.create_lambda_error_alarm("function1")
            alarms_service.create_lambda_duration_alarm("function1")
            alarms_service.create_dynamodb_throttle_alarm("table1")
            alarms_service.create_sqs_queue_depth_alarm("queue1")

            assert mock_put.call_count == 4


@pytest.mark.integration
class TestMonitoringErrorHandling:
    """Integration tests for monitoring error handling"""

    @pytest.fixture
    def config(self):
        """Create config"""
        return CloudWatchConfig()

    @pytest.fixture
    def logger_service(self, config):
        """Create logger service"""
        return CloudWatchLogger(config)

    @pytest.fixture
    def metrics_service(self, config):
        """Create metrics service"""
        return CloudWatchMetrics(config)

    def test_logger_handles_exceptions(self, logger_service):
        """Test logger handles exceptions gracefully"""
        with patch("app.core.monitoring.logger"):
            # Should not raise exception
            logger_service.log_event(
                component="test",
                event_type="test",
                data={"key": "value"},
            )

    def test_metrics_handles_exceptions(self, metrics_service):
        """Test metrics handles exceptions gracefully"""
        from botocore.exceptions import ClientError

        with patch.object(
            metrics_service.cloudwatch_client,
            "put_metric_data",
            side_effect=ClientError(
                {"Error": {"Code": "InvalidParameter"}},
                "PutMetricData",
            ),
        ):
            # Should not raise exception
            metrics_service.put_metric("TestMetric", 42.0)

    def test_alarms_handles_exceptions(self, config):
        """Test alarms handles exceptions gracefully"""
        from botocore.exceptions import ClientError

        alarms_service = CloudWatchAlarms(config)

        with patch.object(
            alarms_service.cloudwatch_client,
            "put_metric_alarm",
            side_effect=ClientError(
                {"Error": {"Code": "InvalidParameter"}},
                "PutMetricAlarm",
            ),
        ):
            # Should not raise exception
            alarms_service.create_alarm(
                alarm_name="test-alarm",
                metric_name="TestMetric",
                threshold=100.0,
            )
