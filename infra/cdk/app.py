"""AWS CDK App for AgentFirst2 MVP Infrastructure"""

import os
from aws_cdk import App, Environment
from infra.cdk.stacks.core_stack import CoreStack
from infra.cdk.stacks.lambda_stack import LambdaStack
from infra.cdk.stacks.monitoring_stack import MonitoringStack


def main():
    """Create and configure CDK app"""
    app = App()

    # Get environment variables
    aws_region = os.getenv("AWS_REGION", "us-east-1")
    aws_account = os.getenv("AWS_ACCOUNT_ID", "")
    environment_name = os.getenv("ENVIRONMENT", "development")

    # Define AWS environment
    env = Environment(
        account=aws_account,
        region=aws_region
    )

    # Create stacks
    core_stack = CoreStack(
        app,
        f"agentfirst-core-{environment_name}",
        env=env,
        environment_name=environment_name,
        description="AgentFirst2 MVP - Core Infrastructure (DynamoDB, SNS, SQS, KMS)"
    )

    lambda_stack = LambdaStack(
        app,
        f"agentfirst-lambda-{environment_name}",
        env=env,
        environment_name=environment_name,
        core_stack=core_stack,
        description="AgentFirst2 MVP - Lambda & API Gateway"
    )

    monitoring_stack = MonitoringStack(
        app,
        f"agentfirst-monitoring-{environment_name}",
        env=env,
        environment_name=environment_name,
        lambda_stack=lambda_stack,
        description="AgentFirst2 MVP - CloudWatch & X-Ray Monitoring"
    )

    # Add dependencies
    lambda_stack.add_dependency(core_stack)
    monitoring_stack.add_dependency(lambda_stack)

    app.synth()


if __name__ == "__main__":
    main()
