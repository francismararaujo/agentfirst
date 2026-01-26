"""Monitoring Stack for AgentFirst2 MVP

This stack creates:
- CloudWatch log groups
- X-Ray service map
- Custom metrics
- CloudWatch alarms
"""

from aws_cdk import (
    Stack,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    Duration,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct
from infra.cdk.stacks.lambda_stack import LambdaStack


class MonitoringStack(Stack):
    """Monitoring and observability stack"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        environment_name: str = "development",
        lambda_stack: LambdaStack = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_name = environment_name
        self.lambda_stack = lambda_stack

        # Create CloudWatch log groups
        self._create_log_groups()

        # Create SNS topic for alarms
        self.alarm_topic = self._create_alarm_topic()

        # Create CloudWatch alarms
        self._create_alarms()

        # Create CloudWatch dashboard
        self._create_dashboard()

        # Create outputs
        self._create_outputs()

    def _create_log_groups(self) -> None:
        """Create CloudWatch log groups"""
        # Note: Lambda log group is created automatically by AWS Lambda
        # We only create additional log groups that are not auto-created
        
        # API Gateway logs
        logs.LogGroup(
            self,
            "APIGatewayLogGroup",
            log_group_name=f"/aws/apigateway/agentfirst-{self.environment_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Application logs
        logs.LogGroup(
            self,
            "ApplicationLogGroup",
            log_group_name=f"/agentfirst/application-{self.environment_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Audit logs
        logs.LogGroup(
            self,
            "AuditLogGroup",
            log_group_name=f"/agentfirst/audit-{self.environment_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )

    def _create_alarm_topic(self) -> sns.Topic:
        """Create SNS topic for alarms"""
        topic = sns.Topic(
            self,
            "AlarmTopic",
            display_name="AgentFirst2 Alarms",
            topic_name=f"agentfirst-alarms-{self.environment_name}",
        )
        return topic

    def _create_alarms(self) -> None:
        """Create CloudWatch alarms"""
        # Lambda error alarm
        cloudwatch.Alarm(
            self,
            "LambdaErrorAlarm",
            metric=self.lambda_stack.lambda_function.metric_errors(
                statistic="Sum",
                period=Duration.minutes(1),
            ),
            threshold=5,
            evaluation_periods=1,
            alarm_description="Alert when Lambda errors exceed 5 in 1 minute",
            alarm_name=f"agentfirst-lambda-errors-{self.environment_name}",
        ).add_alarm_action(cw_actions.SnsAction(self.alarm_topic))

        # Lambda duration alarm
        cloudwatch.Alarm(
            self,
            "LambdaDurationAlarm",
            metric=self.lambda_stack.lambda_function.metric_duration(
                statistic="Average",
                period=Duration.minutes(5),
            ),
            threshold=30000,  # 30 seconds in milliseconds
            evaluation_periods=2,
            alarm_description="Alert when Lambda duration exceeds 30 seconds",
            alarm_name=f"agentfirst-lambda-duration-{self.environment_name}",
        ).add_alarm_action(cw_actions.SnsAction(self.alarm_topic))

        # Lambda throttles alarm
        cloudwatch.Alarm(
            self,
            "LambdaThrottlesAlarm",
            metric=self.lambda_stack.lambda_function.metric_throttles(
                statistic="Sum",
                period=Duration.minutes(1),
            ),
            threshold=1,
            evaluation_periods=1,
            alarm_description="Alert when Lambda is throttled",
            alarm_name=f"agentfirst-lambda-throttles-{self.environment_name}",
        ).add_alarm_action(cw_actions.SnsAction(self.alarm_topic))

        # API Gateway 5xx errors alarm
        cloudwatch.Alarm(
            self,
            "APIGateway5xxAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="5XXError",
                statistic="Sum",
                period=Duration.minutes(1),
                dimensions_map={
                    "ApiName": f"agentfirst-{self.environment_name}",
                },
            ),
            threshold=5,
            evaluation_periods=1,
            alarm_description="Alert when API Gateway 5xx errors exceed 5",
            alarm_name=f"agentfirst-api-5xx-{self.environment_name}",
        ).add_alarm_action(cw_actions.SnsAction(self.alarm_topic))

        # DynamoDB read throttle alarm
        cloudwatch.Alarm(
            self,
            "DynamoDBReadThrottleAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/DynamoDB",
                metric_name="ReadThrottleEvents",
                statistic="Sum",
                period=Duration.minutes(1),
            ),
            threshold=1,
            evaluation_periods=1,
            alarm_description="Alert when DynamoDB read throttling occurs",
            alarm_name=f"agentfirst-dynamodb-read-throttle-{self.environment_name}",
        ).add_alarm_action(cw_actions.SnsAction(self.alarm_topic))

        # DynamoDB write throttle alarm
        cloudwatch.Alarm(
            self,
            "DynamoDBWriteThrottleAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/DynamoDB",
                metric_name="WriteThrottleEvents",
                statistic="Sum",
                period=Duration.minutes(1),
            ),
            threshold=1,
            evaluation_periods=1,
            alarm_description="Alert when DynamoDB write throttling occurs",
            alarm_name=f"agentfirst-dynamodb-write-throttle-{self.environment_name}",
        ).add_alarm_action(cw_actions.SnsAction(self.alarm_topic))

    def _create_dashboard(self) -> None:
        """Create CloudWatch dashboard"""
        dashboard = cloudwatch.Dashboard(
            self,
            "AgentFirstDashboard",
            dashboard_name=f"agentfirst-{self.environment_name}",
        )

        # Lambda metrics
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Lambda Invocations",
                left=[
                    self.lambda_stack.lambda_function.metric_invocations(
                        statistic="Sum",
                        period=Duration.minutes(5),
                    ),
                ],
            ),
            cloudwatch.GraphWidget(
                title="Lambda Errors",
                left=[
                    self.lambda_stack.lambda_function.metric_errors(
                        statistic="Sum",
                        period=Duration.minutes(5),
                    ),
                ],
            ),
            cloudwatch.GraphWidget(
                title="Lambda Duration",
                left=[
                    self.lambda_stack.lambda_function.metric_duration(
                        statistic="Average",
                        period=Duration.minutes(5),
                    ),
                ],
            ),
        )

        # API Gateway metrics
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="API Gateway Requests",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/ApiGateway",
                        metric_name="Count",
                        statistic="Sum",
                        period=Duration.minutes(5),
                        dimensions_map={
                            "ApiName": f"agentfirst-{self.environment_name}",
                        },
                    ),
                ],
            ),
            cloudwatch.GraphWidget(
                title="API Gateway Latency",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/ApiGateway",
                        metric_name="Latency",
                        statistic="Average",
                        period=Duration.minutes(5),
                        dimensions_map={
                            "ApiName": f"agentfirst-{self.environment_name}",
                        },
                    ),
                ],
            ),
        )

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs"""
        CfnOutput(
            self,
            "AlarmTopicArn",
            value=self.alarm_topic.topic_arn,
            export_name=f"agentfirst-alarm-topic-{self.environment_name}",
        )

        CfnOutput(
            self,
            "DashboardURL",
            value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name=agentfirst-{self.environment_name}",
            export_name=f"agentfirst-dashboard-url-{self.environment_name}",
        )
