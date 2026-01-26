"""Performance tests for CloudWatch Monitoring"""

import pytest
import time
from unittest.mock import patch
from app.core.monitoring import (
    CloudWatchConfig,
    CloudWatchLogger,
    CloudWatchMetrics,
    PerformanceTracker,
)


@pytest.mark.performance
class TestMonitoringLatency:
    """Performance tests for monitoring latency"""

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

    def test_log_event_latency(self, logger_service):
        """Test log event latency (should be < 10ms)"""
        with patch("app.core.monitoring.logger"):
            start = time.time()
            logger_service.log_event(
                component="test",
                event_type="test",
                data={"key": "value"},
            )
            elapsed = (time.time() - start) * 1000

            assert elapsed < 10, f"Log event took {elapsed}ms, expected < 10ms"

    def test_put_metric_latency(self, metrics_service):
        """Test put metric latency (should be < 50ms)"""
        with patch.object(metrics_service.cloudwatch_client, "put_metric_data"):
            start = time.time()
            metrics_service.put_metric("TestMetric", 42.0)
            elapsed = (time.time() - start) * 1000

            assert elapsed < 50, f"Put metric took {elapsed}ms, expected < 50ms"

    def test_log_performance_latency(self, logger_service):
        """Test log performance latency (should be < 10ms)"""
        with patch("app.core.monitoring.logger"):
            start = time.time()
            logger_service.log_performance(
                component="test",
                operation="test_op",
                duration_ms=123.45,
            )
            elapsed = (time.time() - start) * 1000

            assert elapsed < 10, f"Log performance took {elapsed}ms, expected < 10ms"

    def test_log_error_latency(self, logger_service):
        """Test log error latency (should be < 10ms)"""
        with patch("app.core.monitoring.logger"):
            start = time.time()
            logger_service.log_error(
                component="test",
                error_type="ValueError",
                error_message="Test error",
            )
            elapsed = (time.time() - start) * 1000

            assert elapsed < 10, f"Log error took {elapsed}ms, expected < 10ms"


@pytest.mark.performance
class TestMonitoringThroughput:
    """Performance tests for monitoring throughput"""

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

    def test_log_event_throughput(self, logger_service):
        """Test log event throughput (should be > 1000 events/s)"""
        with patch("app.core.monitoring.logger"):
            num_events = 100
            start = time.time()

            for i in range(num_events):
                logger_service.log_event(
                    component="test",
                    event_type="test",
                    data={"index": i},
                )

            elapsed = time.time() - start
            throughput = num_events / elapsed

            assert throughput > 1000, f"Throughput {throughput} events/s, expected > 1000"

    def test_put_metric_throughput(self, metrics_service):
        """Test put metric throughput (should be > 500 metrics/s)"""
        with patch.object(metrics_service.cloudwatch_client, "put_metric_data"):
            num_metrics = 50
            start = time.time()

            for i in range(num_metrics):
                metrics_service.put_metric(f"Metric{i}", float(i))

            elapsed = time.time() - start
            throughput = num_metrics / elapsed

            assert throughput > 500, f"Throughput {throughput} metrics/s, expected > 500"

    def test_mixed_logging_throughput(self, logger_service):
        """Test mixed logging throughput"""
        with patch("app.core.monitoring.logger"):
            num_operations = 100
            start = time.time()

            for i in range(num_operations):
                if i % 3 == 0:
                    logger_service.log_event(
                        component="test",
                        event_type="test",
                        data={"index": i},
                    )
                elif i % 3 == 1:
                    logger_service.log_performance(
                        component="test",
                        operation="test_op",
                        duration_ms=float(i),
                    )
                else:
                    logger_service.log_error(
                        component="test",
                        error_type="ValueError",
                        error_message=f"Error {i}",
                    )

            elapsed = time.time() - start
            throughput = num_operations / elapsed

            assert throughput > 500, f"Throughput {throughput} ops/s, expected > 500"


@pytest.mark.performance
class TestPerformanceTrackerLatency:
    """Performance tests for performance tracker"""

    @pytest.fixture
    def config(self):
        """Create config"""
        return CloudWatchConfig()

    @pytest.fixture
    def tracker(self, config):
        """Create performance tracker"""
        metrics = CloudWatchMetrics(config)
        logger_service = CloudWatchLogger(config)
        return PerformanceTracker(metrics, logger_service)

    def test_track_operation_latency(self, tracker):
        """Test track operation latency (should be < 50ms)"""
        with patch.object(tracker.metrics.cloudwatch_client, "put_metric_data"):
            start = time.time()

            with tracker.track_operation("test_operation"):
                pass

            elapsed = (time.time() - start) * 1000

            assert elapsed < 50, f"Track operation took {elapsed}ms, expected < 50ms"

    def test_track_operation_throughput(self, tracker):
        """Test track operation throughput (should be > 100 ops/s)"""
        with patch.object(tracker.metrics.cloudwatch_client, "put_metric_data"):
            num_operations = 50
            start = time.time()

            for i in range(num_operations):
                with tracker.track_operation(f"operation_{i}"):
                    pass

            elapsed = time.time() - start
            throughput = num_operations / elapsed

            assert throughput > 100, f"Throughput {throughput} ops/s, expected > 100"


@pytest.mark.performance
class TestMonitoringMemoryUsage:
    """Performance tests for monitoring memory usage"""

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

    def test_large_event_logging(self, logger_service):
        """Test logging large events"""
        with patch("app.core.monitoring.logger"):
            # Create large event data
            large_data = {"key": "x" * 10000}

            start = time.time()
            logger_service.log_event(
                component="test",
                event_type="test",
                data=large_data,
            )
            elapsed = (time.time() - start) * 1000

            assert elapsed < 50, f"Large event logging took {elapsed}ms, expected < 50ms"

    def test_many_metrics_logging(self, metrics_service):
        """Test logging many metrics"""
        with patch.object(metrics_service.cloudwatch_client, "put_metric_data"):
            num_metrics = 1000
            start = time.time()

            for i in range(num_metrics):
                metrics_service.put_metric(f"Metric{i}", float(i))

            elapsed = time.time() - start

            assert elapsed < 10, f"1000 metrics took {elapsed}s, expected < 10s"
