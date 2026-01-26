"""Unit tests for X-Ray Observability"""

import pytest
from unittest.mock import patch, MagicMock
from app.core.observability import (
    XRayConfig,
    XRayObservability,
    ServiceMap,
    DistributedTracing,
    DummySegment,
    DummySubsegment,
)


@pytest.mark.unit
class TestXRayConfig:
    """Tests for XRayConfig"""

    def test_config_creation_with_defaults(self):
        """Test creating config with default values"""
        config = XRayConfig()

        assert config.service_name == "agentfirst"
        assert config.enabled is True
        assert config.sampling_rate == 1.0
        assert config.log_level == "INFO"

    def test_config_creation_with_custom_values(self):
        """Test creating config with custom values"""
        config = XRayConfig(
            service_name="custom-service",
            enabled=False,
            sampling_rate=0.5,
            log_level="DEBUG",
        )

        assert config.service_name == "custom-service"
        assert config.enabled is False
        assert config.sampling_rate == 0.5
        assert config.log_level == "DEBUG"


@pytest.mark.unit
class TestXRayObservability:
    """Tests for XRayObservability"""

    @pytest.fixture
    def observability(self):
        """Create observability service"""
        config = XRayConfig(enabled=False)  # Disable for testing
        return XRayObservability(config)

    def test_observability_creation_disabled(self):
        """Test creating observability with X-Ray disabled"""
        config = XRayConfig(enabled=False)
        obs = XRayObservability(config)

        assert obs.config.enabled is False

    def test_create_segment_disabled(self, observability):
        """Test creating segment when X-Ray is disabled"""
        segment = observability.create_segment("test-segment")

        assert isinstance(segment, DummySegment)

    def test_create_subsegment_disabled(self, observability):
        """Test creating subsegment when X-Ray is disabled"""
        subsegment = observability.create_subsegment("test-subsegment")

        assert isinstance(subsegment, DummySubsegment)

    def test_put_annotation_disabled(self, observability):
        """Test putting annotation when X-Ray is disabled"""
        # Should not raise exception
        observability.put_annotation("key", "value")

    def test_put_metadata_disabled(self, observability):
        """Test putting metadata when X-Ray is disabled"""
        # Should not raise exception
        observability.put_metadata("key", {"data": "value"})

    def test_capture_exception_disabled(self, observability):
        """Test capturing exception when X-Ray is disabled"""
        # Should not raise exception
        observability.capture_exception(ValueError("test error"))

    def test_trace_operation_disabled(self, observability):
        """Test tracing operation when X-Ray is disabled"""
        with observability.trace_operation("test_operation"):
            pass


@pytest.mark.unit
class TestDummySegment:
    """Tests for DummySegment"""

    def test_dummy_segment_operations(self):
        """Test dummy segment operations"""
        segment = DummySegment()

        # Should not raise exceptions
        segment.put_annotation("key", "value")
        segment.put_metadata("key", {"data": "value"})
        segment.add_exception(ValueError("test"))

    def test_dummy_segment_context_manager(self):
        """Test dummy segment as context manager"""
        segment = DummySegment()

        with segment as s:
            assert s is segment


@pytest.mark.unit
class TestDummySubsegment:
    """Tests for DummySubsegment"""

    def test_dummy_subsegment_operations(self):
        """Test dummy subsegment operations"""
        subsegment = DummySubsegment()

        # Should not raise exceptions
        subsegment.put_annotation("key", "value")
        subsegment.put_metadata("key", {"data": "value"})
        subsegment.add_exception(ValueError("test"))

    def test_dummy_subsegment_context_manager(self):
        """Test dummy subsegment as context manager"""
        subsegment = DummySubsegment()

        with subsegment as s:
            assert s is subsegment


@pytest.mark.unit
class TestServiceMap:
    """Tests for ServiceMap"""

    @pytest.fixture
    def service_map(self):
        """Create service map"""
        config = XRayConfig(enabled=False)
        observability = XRayObservability(config)
        return ServiceMap(observability)

    def test_trace_lambda_invocation(self, service_map):
        """Test tracing Lambda invocation"""
        with service_map.trace_lambda_invocation(
            "my-function",
            {"key": "value"},
            correlation_id="corr-123",
        ):
            pass

    def test_trace_dynamodb_operation(self, service_map):
        """Test tracing DynamoDB operation"""
        with service_map.trace_dynamodb_operation(
            "GetItem",
            "users-table",
            key={"email": "user@example.com"},
        ):
            pass

    def test_trace_sns_publish(self, service_map):
        """Test tracing SNS publish"""
        with service_map.trace_sns_publish(
            "arn:aws:sns:us-east-1:123456789:topic",
            message_id="msg-123",
        ):
            pass

    def test_trace_sqs_operation(self, service_map):
        """Test tracing SQS operation"""
        with service_map.trace_sqs_operation(
            "SendMessage",
            "https://sqs.us-east-1.amazonaws.com/123456789/queue",
            message_count=1,
        ):
            pass

    def test_trace_bedrock_invocation(self, service_map):
        """Test tracing Bedrock invocation"""
        with service_map.trace_bedrock_invocation(
            "anthropic.claude-3-sonnet-20240229-v1:0",
            input_tokens=100,
        ):
            pass

    def test_trace_external_api_call(self, service_map):
        """Test tracing external API call"""
        with service_map.trace_external_api_call(
            "ifood",
            "https://api.ifood.com/v1/orders",
            method="GET",
        ):
            pass


@pytest.mark.unit
class TestDistributedTracing:
    """Tests for DistributedTracing"""

    def test_get_trace_id_no_segment(self):
        """Test getting trace ID when no segment exists"""
        trace_id = DistributedTracing.get_trace_id()

        # Should return None or not raise exception
        assert trace_id is None or isinstance(trace_id, str)

    def test_get_segment_id_no_segment(self):
        """Test getting segment ID when no segment exists"""
        segment_id = DistributedTracing.get_segment_id()

        # Should return None or not raise exception
        assert segment_id is None or isinstance(segment_id, str)

    def test_create_trace_header(self):
        """Test creating trace header"""
        header = DistributedTracing.create_trace_header(
            "1-5e6722a7-cc2xmpl46db7ae98d0da47ae",
            "a58d0afd3d6025",
        )

        assert "Root=" in header
        assert "Parent=" in header
        assert "Sampled=1" in header
