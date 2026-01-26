"""X-Ray Observability for AgentFirst2 MVP

This module provides X-Ray distributed tracing capabilities:
- Distributed tracing across services
- Service map visualization
- Trace analysis
- Performance insights
- Subsegment tracking
"""

import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
from aws_xray_sdk.core.context import Context

logger = logging.getLogger(__name__)


class XRayConfig:
    """Configuration for X-Ray observability"""

    def __init__(
        self,
        service_name: str = "agentfirst",
        enabled: bool = True,
        sampling_rate: float = 1.0,
        log_level: str = "INFO",
    ):
        self.service_name = service_name
        self.enabled = enabled
        self.sampling_rate = sampling_rate
        self.log_level = log_level


class XRayObservability:
    """X-Ray distributed tracing"""

    def __init__(self, config: XRayConfig):
        self.config = config
        self.recorder = xray_recorder

        if config.enabled:
            self._configure_xray()

    def _configure_xray(self) -> None:
        """Configure X-Ray recorder"""
        try:
            # Configure X-Ray
            self.recorder.configure(
                service=self.config.service_name,
                sampling=True,
                context_missing="LOG_ERROR",
            )

            # Patch AWS SDK and HTTP libraries
            patch_all()

            logger.info(
                json.dumps({
                    "event": "xray_configured",
                    "service": self.config.service_name,
                })
            )

        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "xray_configuration_failed",
                    "error": str(e),
                })
            )

    def create_segment(
        self,
        name: str,
        namespace: str = "aws",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Create X-Ray segment

        Args:
            name: Segment name
            namespace: Segment namespace
            metadata: Segment metadata
        """
        if not self.config.enabled:
            return DummySegment()

        try:
            segment = self.recorder.begin_segment(
                name=name,
                namespace=namespace,
            )

            if metadata:
                segment.put_metadata("data", metadata)

            return segment

        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "segment_creation_failed",
                    "error": str(e),
                    "segment_name": name,
                })
            )
            return DummySegment()

    def create_subsegment(
        self,
        name: str,
        namespace: str = "local",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Create X-Ray subsegment

        Args:
            name: Subsegment name
            namespace: Subsegment namespace
            metadata: Subsegment metadata
        """
        if not self.config.enabled:
            return DummySubsegment()

        try:
            subsegment = self.recorder.begin_subsegment(
                name=name,
                namespace=namespace,
            )

            if metadata:
                subsegment.put_metadata("data", metadata)

            return subsegment

        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "subsegment_creation_failed",
                    "error": str(e),
                    "subsegment_name": name,
                })
            )
            return DummySubsegment()

    def put_annotation(self, key: str, value: str) -> None:
        """
        Add annotation to current segment

        Args:
            key: Annotation key
            value: Annotation value
        """
        try:
            if self.config.enabled:
                self.recorder.current_segment().put_annotation(key, value)
        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "annotation_failed",
                    "error": str(e),
                    "key": key,
                })
            )

    def put_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to current segment

        Args:
            key: Metadata key
            value: Metadata value
        """
        try:
            if self.config.enabled:
                self.recorder.current_segment().put_metadata(key, value)
        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "metadata_failed",
                    "error": str(e),
                    "key": key,
                })
            )

    def capture_exception(self, exception: Exception) -> None:
        """
        Capture exception in X-Ray

        Args:
            exception: Exception to capture
        """
        try:
            if self.config.enabled:
                self.recorder.current_segment().add_exception(exception)
        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "exception_capture_failed",
                    "error": str(e),
                })
            )

    def trace_operation(
        self,
        operation_name: str,
        namespace: str = "local",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Context manager for tracing operations

        Args:
            operation_name: Operation name
            namespace: Segment namespace
            metadata: Segment metadata
        """
        return OperationTracer(
            self.recorder,
            self.config.enabled,
            operation_name,
            namespace,
            metadata,
        )


class OperationTracer:
    """Context manager for tracing operations"""

    def __init__(
        self,
        recorder,
        enabled: bool,
        operation_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]],
    ):
        self.recorder = recorder
        self.enabled = enabled
        self.operation_name = operation_name
        self.namespace = namespace
        self.metadata = metadata
        self.subsegment = None

    def __enter__(self):
        if self.enabled:
            try:
                self.subsegment = self.recorder.begin_subsegment(
                    name=self.operation_name,
                    namespace=self.namespace,
                )

                if self.metadata:
                    self.subsegment.put_metadata("data", self.metadata)

            except Exception as e:
                logger.error(
                    json.dumps({
                        "event": "operation_tracer_enter_failed",
                        "error": str(e),
                    })
                )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.enabled and self.subsegment:
            try:
                if exc_type is not None:
                    self.subsegment.add_exception(exc_val)

                self.recorder.end_subsegment()

            except Exception as e:
                logger.error(
                    json.dumps({
                        "event": "operation_tracer_exit_failed",
                        "error": str(e),
                    })
                )

        return False


class DummySegment:
    """Dummy segment for when X-Ray is disabled"""

    def put_annotation(self, key: str, value: str) -> None:
        pass

    def put_metadata(self, key: str, value: Any) -> None:
        pass

    def add_exception(self, exception: Exception) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class DummySubsegment:
    """Dummy subsegment for when X-Ray is disabled"""

    def put_annotation(self, key: str, value: str) -> None:
        pass

    def put_metadata(self, key: str, value: Any) -> None:
        pass

    def add_exception(self, exception: Exception) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class ServiceMap:
    """Service map for X-Ray visualization"""

    def __init__(self, observability: XRayObservability):
        self.observability = observability

    def trace_lambda_invocation(
        self,
        function_name: str,
        event: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ):
        """
        Trace Lambda invocation

        Args:
            function_name: Lambda function name
            event: Lambda event
            correlation_id: Correlation ID
        """
        metadata = {
            "function_name": function_name,
            "correlation_id": correlation_id,
            "event": event,
        }

        return self.observability.trace_operation(
            f"lambda_{function_name}",
            namespace="aws",
            metadata=metadata,
        )

    def trace_dynamodb_operation(
        self,
        operation: str,
        table_name: str,
        key: Optional[Dict[str, Any]] = None,
    ):
        """
        Trace DynamoDB operation

        Args:
            operation: Operation type (GetItem, PutItem, etc.)
            table_name: Table name
            key: Item key
        """
        metadata = {
            "operation": operation,
            "table_name": table_name,
            "key": key,
        }

        return self.observability.trace_operation(
            f"dynamodb_{operation}",
            namespace="aws",
            metadata=metadata,
        )

    def trace_sns_publish(
        self,
        topic_arn: str,
        message_id: Optional[str] = None,
    ):
        """
        Trace SNS publish

        Args:
            topic_arn: SNS topic ARN
            message_id: Message ID
        """
        metadata = {
            "topic_arn": topic_arn,
            "message_id": message_id,
        }

        return self.observability.trace_operation(
            "sns_publish",
            namespace="aws",
            metadata=metadata,
        )

    def trace_sqs_operation(
        self,
        operation: str,
        queue_url: str,
        message_count: Optional[int] = None,
    ):
        """
        Trace SQS operation

        Args:
            operation: Operation type (SendMessage, ReceiveMessage, etc.)
            queue_url: Queue URL
            message_count: Message count
        """
        metadata = {
            "operation": operation,
            "queue_url": queue_url,
            "message_count": message_count,
        }

        return self.observability.trace_operation(
            f"sqs_{operation}",
            namespace="aws",
            metadata=metadata,
        )

    def trace_bedrock_invocation(
        self,
        model_id: str,
        input_tokens: Optional[int] = None,
    ):
        """
        Trace Bedrock invocation

        Args:
            model_id: Model ID
            input_tokens: Input token count
        """
        metadata = {
            "model_id": model_id,
            "input_tokens": input_tokens,
        }

        return self.observability.trace_operation(
            f"bedrock_{model_id}",
            namespace="aws",
            metadata=metadata,
        )

    def trace_external_api_call(
        self,
        api_name: str,
        endpoint: str,
        method: str = "GET",
    ):
        """
        Trace external API call

        Args:
            api_name: API name
            endpoint: API endpoint
            method: HTTP method
        """
        metadata = {
            "api_name": api_name,
            "endpoint": endpoint,
            "method": method,
        }

        return self.observability.trace_operation(
            f"api_{api_name}",
            namespace="external",
            metadata=metadata,
        )


class DistributedTracing:
    """Distributed tracing utilities"""

    @staticmethod
    def get_trace_id() -> Optional[str]:
        """
        Get current trace ID

        Returns:
            Trace ID or None
        """
        try:
            from aws_xray_sdk.core import xray_recorder

            segment = xray_recorder.current_segment()
            if segment:
                return segment.trace_id

        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "get_trace_id_failed",
                    "error": str(e),
                })
            )

        return None

    @staticmethod
    def get_segment_id() -> Optional[str]:
        """
        Get current segment ID

        Returns:
            Segment ID or None
        """
        try:
            from aws_xray_sdk.core import xray_recorder

            segment = xray_recorder.current_segment()
            if segment:
                return segment.id

        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "get_segment_id_failed",
                    "error": str(e),
                })
            )

        return None

    @staticmethod
    def create_trace_header(trace_id: str, segment_id: str) -> str:
        """
        Create X-Ray trace header

        Args:
            trace_id: Trace ID
            segment_id: Segment ID

        Returns:
            Trace header string
        """
        return f"Root={trace_id};Parent={segment_id};Sampled=1"
