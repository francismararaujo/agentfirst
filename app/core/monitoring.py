"""CloudWatch Monitoring for AgentFirst2 MVP

This module provides CloudWatch monitoring capabilities:
- Structured logging (JSON format)
- Custom metrics (business + technical)
- Log groups per component
- Log retention policies
- Automated dashboards
"""

import json
import logging
import time
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CloudWatchConfig:
    """Configuration for CloudWatch monitoring"""

    def __init__(
        self,
        region: str = "us-east-1",
        log_group_prefix: str = "/aws/lambda/agentfirst",
        log_retention_days: int = 30,
        enable_metrics: bool = True,
        enable_dashboards: bool = True,
        namespace: str = "AgentFirst2",
    ):
        self.region = region
        self.log_group_prefix = log_group_prefix
        self.log_retention_days = log_retention_days
        self.enable_metrics = enable_metrics
        self.enable_dashboards = enable_dashboards
        self.namespace = namespace


class CloudWatchLogger:
    """Structured logging to CloudWatch"""

    def __init__(self, config: CloudWatchConfig):
        self.config = config
        self.logs_client = boto3.client("logs", region_name=config.region)
        self.cloudwatch_client = boto3.client("cloudwatch", region_name=config.region)

    def log_event(
        self,
        component: str,
        event_type: str,
        data: Dict[str, Any],
        level: str = "INFO",
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Log structured event to CloudWatch

        Args:
            component: Component name (e.g., 'lambda_handler', 'event_bus')
            event_type: Event type (e.g., 'message_received', 'order_created')
            data: Event data
            level: Log level (INFO, WARNING, ERROR, DEBUG)
            correlation_id: Correlation ID for tracing
        """
        try:
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "component": component,
                "event_type": event_type,
                "level": level,
                "correlation_id": correlation_id,
                "data": data,
            }

            # Log to standard logger (which writes to CloudWatch)
            log_message = json.dumps(log_entry)

            if level == "ERROR":
                logger.error(log_message)
            elif level == "WARNING":
                logger.warning(log_message)
            elif level == "DEBUG":
                logger.debug(log_message)
            else:
                logger.info(log_message)

        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "logging_failed",
                    "error": str(e),
                    "component": component,
                })
            )

    def log_performance(
        self,
        component: str,
        operation: str,
        duration_ms: float,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log performance metrics

        Args:
            component: Component name
            operation: Operation name
            duration_ms: Duration in milliseconds
            correlation_id: Correlation ID
            metadata: Additional metadata
        """
        try:
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "component": component,
                "event_type": "performance",
                "operation": operation,
                "duration_ms": duration_ms,
                "correlation_id": correlation_id,
                "metadata": metadata or {},
            }

            logger.info(json.dumps(log_entry))

        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "performance_logging_failed",
                    "error": str(e),
                })
            )

    def log_error(
        self,
        component: str,
        error_type: str,
        error_message: str,
        correlation_id: Optional[str] = None,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log error with context

        Args:
            component: Component name
            error_type: Error type
            error_message: Error message
            correlation_id: Correlation ID
            stack_trace: Stack trace
            context: Additional context
        """
        try:
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "component": component,
                "event_type": "error",
                "error_type": error_type,
                "error_message": error_message,
                "correlation_id": correlation_id,
                "stack_trace": stack_trace,
                "context": context or {},
            }

            logger.error(json.dumps(log_entry))

        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "error_logging_failed",
                    "error": str(e),
                })
            )


class CloudWatchMetrics:
    """Custom metrics for CloudWatch"""

    def __init__(self, config: CloudWatchConfig):
        self.config = config
        self.cloudwatch_client = boto3.client("cloudwatch", region_name=config.region)

    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "Count",
        dimensions: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Put custom metric to CloudWatch

        Args:
            metric_name: Metric name
            value: Metric value
            unit: Unit (Count, Seconds, Bytes, etc.)
            dimensions: Metric dimensions
        """
        try:
            if not self.config.enable_metrics:
                return

            metric_data = {
                "MetricName": metric_name,
                "Value": value,
                "Unit": unit,
                "Timestamp": datetime.now(timezone.utc),
            }

            if dimensions:
                metric_data["Dimensions"] = [
                    {"Name": k, "Value": v} for k, v in dimensions.items()
                ]

            self.cloudwatch_client.put_metric_data(
                Namespace=self.config.namespace,
                MetricData=[metric_data],
            )

        except ClientError as e:
            logger.error(
                json.dumps({
                    "event": "metric_put_failed",
                    "error": str(e),
                    "metric_name": metric_name,
                })
            )

    def put_message_count(self, user_email: str, count: int = 1) -> None:
        """
        Track message count metric

        Args:
            user_email: User email
            count: Number of messages
        """
        self.put_metric(
            "MessageCount",
            count,
            unit="Count",
            dimensions={"UserEmail": user_email},
        )

    def put_latency(
        self,
        operation: str,
        duration_ms: float,
        component: str = "Lambda",
    ) -> None:
        """
        Track latency metric

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            component: Component name
        """
        self.put_metric(
            "Latency",
            duration_ms,
            unit="Milliseconds",
            dimensions={"Operation": operation, "Component": component},
        )

    def put_error_count(self, error_type: str, component: str = "Lambda") -> None:
        """
        Track error count metric

        Args:
            error_type: Error type
            component: Component name
        """
        self.put_metric(
            "ErrorCount",
            1,
            unit="Count",
            dimensions={"ErrorType": error_type, "Component": component},
        )

    def put_usage_percentage(self, user_email: str, percentage: float) -> None:
        """
        Track usage percentage metric

        Args:
            user_email: User email
            percentage: Usage percentage (0-100)
        """
        self.put_metric(
            "UsagePercentage",
            percentage,
            unit="Percent",
            dimensions={"UserEmail": user_email},
        )

    def put_queue_depth(self, queue_name: str, depth: int) -> None:
        """
        Track SQS queue depth metric

        Args:
            queue_name: Queue name
            depth: Queue depth
        """
        self.put_metric(
            "QueueDepth",
            depth,
            unit="Count",
            dimensions={"QueueName": queue_name},
        )

    def put_processing_time(
        self,
        operation: str,
        duration_ms: float,
        status: str = "Success",
    ) -> None:
        """
        Track processing time metric

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            status: Operation status (Success, Failed)
        """
        self.put_metric(
            "ProcessingTime",
            duration_ms,
            unit="Milliseconds",
            dimensions={"Operation": operation, "Status": status},
        )


class CloudWatchAlarms:
    """CloudWatch alarms for monitoring"""

    def __init__(self, config: CloudWatchConfig):
        self.config = config
        self.cloudwatch_client = boto3.client("cloudwatch", region_name=config.region)

    def create_alarm(
        self,
        alarm_name: str,
        metric_name: str,
        threshold: float,
        comparison_operator: str = "GreaterThanThreshold",
        evaluation_periods: int = 1,
        period_seconds: int = 300,
        statistic: str = "Sum",
        alarm_description: str = "",
        alarm_actions: Optional[List[str]] = None,
    ) -> None:
        """
        Create CloudWatch alarm

        Args:
            alarm_name: Alarm name
            metric_name: Metric name
            threshold: Threshold value
            comparison_operator: Comparison operator
            evaluation_periods: Number of evaluation periods
            period_seconds: Period in seconds
            statistic: Statistic (Sum, Average, Maximum, Minimum)
            alarm_description: Alarm description
            alarm_actions: SNS topic ARNs for alarm actions
        """
        try:
            params = {
                "AlarmName": alarm_name,
                "MetricName": metric_name,
                "Namespace": self.config.namespace,
                "Statistic": statistic,
                "Period": period_seconds,
                "EvaluationPeriods": evaluation_periods,
                "Threshold": threshold,
                "ComparisonOperator": comparison_operator,
                "AlarmDescription": alarm_description,
            }

            if alarm_actions:
                params["AlarmActions"] = alarm_actions

            self.cloudwatch_client.put_metric_alarm(**params)

            logger.info(
                json.dumps({
                    "event": "alarm_created",
                    "alarm_name": alarm_name,
                    "metric_name": metric_name,
                })
            )

        except ClientError as e:
            logger.error(
                json.dumps({
                    "event": "alarm_creation_failed",
                    "error": str(e),
                    "alarm_name": alarm_name,
                })
            )

    def create_lambda_error_alarm(
        self,
        function_name: str,
        threshold: int = 5,
        alarm_actions: Optional[List[str]] = None,
    ) -> None:
        """
        Create alarm for Lambda errors

        Args:
            function_name: Lambda function name
            threshold: Error threshold
            alarm_actions: SNS topic ARNs
        """
        self.create_alarm(
            alarm_name=f"{function_name}-errors",
            metric_name="Errors",
            threshold=threshold,
            comparison_operator="GreaterThanThreshold",
            evaluation_periods=1,
            period_seconds=300,
            statistic="Sum",
            alarm_description=f"Alert when {function_name} has > {threshold} errors",
            alarm_actions=alarm_actions,
        )

    def create_lambda_duration_alarm(
        self,
        function_name: str,
        threshold_ms: float = 30000,
        alarm_actions: Optional[List[str]] = None,
    ) -> None:
        """
        Create alarm for Lambda duration

        Args:
            function_name: Lambda function name
            threshold_ms: Duration threshold in milliseconds
            alarm_actions: SNS topic ARNs
        """
        self.create_alarm(
            alarm_name=f"{function_name}-duration",
            metric_name="Duration",
            threshold=threshold_ms,
            comparison_operator="GreaterThanThreshold",
            evaluation_periods=1,
            period_seconds=300,
            statistic="Average",
            alarm_description=f"Alert when {function_name} duration > {threshold_ms}ms",
            alarm_actions=alarm_actions,
        )

    def create_dynamodb_throttle_alarm(
        self,
        table_name: str,
        alarm_actions: Optional[List[str]] = None,
    ) -> None:
        """
        Create alarm for DynamoDB throttling

        Args:
            table_name: DynamoDB table name
            alarm_actions: SNS topic ARNs
        """
        self.create_alarm(
            alarm_name=f"{table_name}-throttle",
            metric_name="UserErrors",
            threshold=1,
            comparison_operator="GreaterThanOrEqualToThreshold",
            evaluation_periods=1,
            period_seconds=60,
            statistic="Sum",
            alarm_description=f"Alert when {table_name} is throttled",
            alarm_actions=alarm_actions,
        )

    def create_sqs_queue_depth_alarm(
        self,
        queue_name: str,
        threshold: int = 1000,
        alarm_actions: Optional[List[str]] = None,
    ) -> None:
        """
        Create alarm for SQS queue depth

        Args:
            queue_name: SQS queue name
            threshold: Queue depth threshold
            alarm_actions: SNS topic ARNs
        """
        self.create_alarm(
            alarm_name=f"{queue_name}-depth",
            metric_name="ApproximateNumberOfMessagesVisible",
            threshold=threshold,
            comparison_operator="GreaterThanThreshold",
            evaluation_periods=1,
            period_seconds=300,
            statistic="Average",
            alarm_description=f"Alert when {queue_name} depth > {threshold}",
            alarm_actions=alarm_actions,
        )


class PerformanceTracker:
    """Track performance metrics"""

    def __init__(self, metrics: CloudWatchMetrics, logger_service: CloudWatchLogger):
        self.metrics = metrics
        self.logger_service = logger_service

    def track_operation(
        self,
        operation_name: str,
        component: str = "Lambda",
        correlation_id: Optional[str] = None,
    ):
        """
        Context manager to track operation performance

        Args:
            operation_name: Operation name
            component: Component name
            correlation_id: Correlation ID
        """
        return OperationTracker(
            self.metrics,
            self.logger_service,
            operation_name,
            component,
            correlation_id,
        )


class OperationTracker:
    """Context manager for tracking operations"""

    def __init__(
        self,
        metrics: CloudWatchMetrics,
        logger_service: CloudWatchLogger,
        operation_name: str,
        component: str,
        correlation_id: Optional[str],
    ):
        self.metrics = metrics
        self.logger_service = logger_service
        self.operation_name = operation_name
        self.component = component
        self.correlation_id = correlation_id
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.logger_service.log_event(
            self.component,
            f"{self.operation_name}_started",
            {},
            correlation_id=self.correlation_id,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000

        if exc_type is None:
            self.logger_service.log_performance(
                self.component,
                self.operation_name,
                duration_ms,
                correlation_id=self.correlation_id,
            )
            self.metrics.put_latency(
                self.operation_name,
                duration_ms,
                component=self.component,
            )
        else:
            self.logger_service.log_error(
                self.component,
                exc_type.__name__,
                str(exc_val),
                correlation_id=self.correlation_id,
            )
            self.metrics.put_error_count(exc_type.__name__, component=self.component)

        return False
