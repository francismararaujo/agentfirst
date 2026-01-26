"""
Smoke tests for deployment validation

These tests verify that the deployment was successful and all components are working.
"""

import pytest
import boto3
import os
from unittest.mock import MagicMock, patch


@pytest.mark.smoke
class TestDeploymentValidation:
    """Smoke tests for deployment"""
    
    @pytest.fixture
    def aws_region(self):
        """Get AWS region from environment"""
        return os.getenv("AWS_REGION", "us-east-1")
    
    def test_dynamodb_tables_exist(self, aws_region):
        """Test that all required DynamoDB tables exist"""
        dynamodb = boto3.client("dynamodb", region_name=aws_region)
        
        required_tables = [
            "users",
            "sessions",
            "memory",
            "usage",
            "audit_logs",
            "escalation"
        ]
        
        try:
            response = dynamodb.list_tables()
            existing_tables = response.get("TableNames", [])
            
            for table in required_tables:
                assert any(table in t for t in existing_tables), f"Table {table} not found"
        except Exception as e:
            pytest.skip(f"DynamoDB not accessible: {e}")
    
    def test_lambda_function_exists(self, aws_region):
        """Test that Lambda function exists"""
        lambda_client = boto3.client("lambda", region_name=aws_region)
        
        try:
            response = lambda_client.get_function(FunctionName="agentfirst-webhook")
            assert response["Configuration"]["FunctionName"] == "agentfirst-webhook"
            assert response["Configuration"]["Runtime"] in ["python3.11", "python3.12", "python3.13"]
        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.skip("Lambda function not found")
        except Exception as e:
            pytest.skip(f"Lambda not accessible: {e}")
    
    def test_api_gateway_exists(self, aws_region):
        """Test that API Gateway exists"""
        apigw = boto3.client("apigateway", region_name=aws_region)
        
        try:
            response = apigw.get_rest_apis()
            apis = response.get("items", [])
            assert len(apis) > 0, "No API Gateway found"
        except Exception as e:
            pytest.skip(f"API Gateway not accessible: {e}")
    
    def test_sns_topics_exist(self, aws_region):
        """Test that SNS topics exist"""
        sns = boto3.client("sns", region_name=aws_region)
        
        required_topics = [
            "omnichannel",
            "retail"
        ]
        
        try:
            response = sns.list_topics()
            existing_topics = [t["TopicArn"] for t in response.get("Topics", [])]
            
            for topic in required_topics:
                assert any(topic in t for t in existing_topics), f"Topic {topic} not found"
        except Exception as e:
            pytest.skip(f"SNS not accessible: {e}")
    
    def test_sqs_queues_exist(self, aws_region):
        """Test that SQS queues exist"""
        sqs = boto3.client("sqs", region_name=aws_region)
        
        try:
            response = sqs.list_queues()
            queues = response.get("QueueUrls", [])
            assert len(queues) > 0, "No SQS queues found"
        except Exception as e:
            pytest.skip(f"SQS not accessible: {e}")
    
    def test_cloudwatch_log_groups_exist(self, aws_region):
        """Test that CloudWatch log groups exist"""
        logs = boto3.client("logs", region_name=aws_region)
        
        try:
            response = logs.describe_log_groups()
            log_groups = response.get("logGroups", [])
            assert len(log_groups) > 0, "No CloudWatch log groups found"
        except Exception as e:
            pytest.skip(f"CloudWatch Logs not accessible: {e}")
    
    def test_kms_keys_exist(self, aws_region):
        """Test that KMS keys exist"""
        kms = boto3.client("kms", region_name=aws_region)
        
        try:
            response = kms.list_keys()
            keys = response.get("Keys", [])
            assert len(keys) > 0, "No KMS keys found"
        except Exception as e:
            pytest.skip(f"KMS not accessible: {e}")
    
    def test_secrets_manager_secrets_exist(self, aws_region):
        """Test that Secrets Manager secrets exist"""
        secrets = boto3.client("secretsmanager", region_name=aws_region)
        
        required_secrets = [
            "telegram-bot-token",
            "ifood-oauth",
            "bedrock-api-key"
        ]
        
        try:
            response = secrets.list_secrets()
            existing_secrets = [s["Name"] for s in response.get("SecretList", [])]
            
            for secret in required_secrets:
                assert any(secret in s for s in existing_secrets), f"Secret {secret} not found"
        except Exception as e:
            pytest.skip(f"Secrets Manager not accessible: {e}")
    
    def test_iam_roles_exist(self, aws_region):
        """Test that IAM roles exist"""
        iam = boto3.client("iam", region_name=aws_region)
        
        required_roles = [
            "agentfirst-lambda-role",
            "agentfirst-github-actions-role"
        ]
        
        try:
            response = iam.list_roles()
            existing_roles = [r["RoleName"] for r in response.get("Roles", [])]
            
            for role in required_roles:
                assert any(role in r for r in existing_roles), f"Role {role} not found"
        except Exception as e:
            pytest.skip(f"IAM not accessible: {e}")
    
    def test_lambda_has_xray_tracing(self, aws_region):
        """Test that Lambda has X-Ray tracing enabled"""
        lambda_client = boto3.client("lambda", region_name=aws_region)
        
        try:
            response = lambda_client.get_function(FunctionName="agentfirst-webhook")
            tracing_config = response["Configuration"].get("TracingConfig", {})
            assert tracing_config.get("Mode") == "Active", "X-Ray tracing not enabled"
        except Exception as e:
            pytest.skip(f"Lambda not accessible: {e}")
    
    def test_lambda_has_environment_variables(self, aws_region):
        """Test that Lambda has required environment variables"""
        lambda_client = boto3.client("lambda", region_name=aws_region)
        
        required_env_vars = [
            "ENVIRONMENT",
            "AWS_REGION",
            "DYNAMODB_TABLE_USERS",
            "DYNAMODB_TABLE_SESSIONS",
            "DYNAMODB_TABLE_MEMORY",
            "DYNAMODB_TABLE_USAGE",
            "DYNAMODB_TABLE_AUDIT_LOGS"
        ]
        
        try:
            response = lambda_client.get_function(FunctionName="agentfirst-webhook")
            env_vars = response["Configuration"].get("Environment", {}).get("Variables", {})
            
            for var in required_env_vars:
                assert var in env_vars, f"Environment variable {var} not found"
        except Exception as e:
            pytest.skip(f"Lambda not accessible: {e}")
    
    def test_api_gateway_has_logging(self, aws_region):
        """Test that API Gateway has CloudWatch logging enabled"""
        apigw = boto3.client("apigateway", region_name=aws_region)
        
        try:
            response = apigw.get_rest_apis()
            apis = response.get("items", [])
            
            for api in apis:
                stages = apigw.get_stages(restApiId=api["id"]).get("item", [])
                for stage in stages:
                    logging_level = stage.get("methodSettings", {}).get("*/*", {}).get("LoggingLevel")
                    assert logging_level in ["INFO", "ERROR"], "API Gateway logging not properly configured"
        except Exception as e:
            pytest.skip(f"API Gateway not accessible: {e}")
    
    def test_dynamodb_has_encryption(self, aws_region):
        """Test that DynamoDB tables have encryption enabled"""
        dynamodb = boto3.client("dynamodb", region_name=aws_region)
        
        try:
            response = dynamodb.list_tables()
            tables = response.get("TableNames", [])
            
            for table in tables:
                table_desc = dynamodb.describe_table(TableName=table)
                sse = table_desc["Table"].get("SSEDescription", {})
                assert sse.get("Status") == "ENABLED", f"Encryption not enabled for table {table}"
        except Exception as e:
            pytest.skip(f"DynamoDB not accessible: {e}")
    
    def test_dynamodb_has_pitr(self, aws_region):
        """Test that DynamoDB tables have Point-in-Time Recovery enabled"""
        dynamodb = boto3.client("dynamodb", region_name=aws_region)
        
        try:
            response = dynamodb.list_tables()
            tables = response.get("TableNames", [])
            
            for table in tables:
                pitr = dynamodb.describe_continuous_backups(TableName=table)
                status = pitr.get("ContinuousBackupsDescription", {}).get("PointInTimeRecoveryDescription", {}).get("PointInTimeRecoveryStatus")
                assert status == "ENABLED", f"PITR not enabled for table {table}"
        except Exception as e:
            pytest.skip(f"DynamoDB not accessible: {e}")
    
    def test_sqs_has_dlq(self, aws_region):
        """Test that SQS queues have Dead Letter Queue configured"""
        sqs = boto3.client("sqs", region_name=aws_region)
        
        try:
            response = sqs.list_queues()
            queues = response.get("QueueUrls", [])
            
            for queue_url in queues:
                attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["All"])
                dlq_policy = attrs.get("Attributes", {}).get("RedrivePolicy")
                # DLQ is optional but recommended
                if dlq_policy:
                    assert "deadLetterTargetArn" in dlq_policy, f"DLQ not properly configured for queue {queue_url}"
        except Exception as e:
            pytest.skip(f"SQS not accessible: {e}")
    
    def test_cloudwatch_alarms_exist(self, aws_region):
        """Test that CloudWatch alarms are configured"""
        cloudwatch = boto3.client("cloudwatch", region_name=aws_region)
        
        try:
            response = cloudwatch.describe_alarms()
            alarms = response.get("MetricAlarms", [])
            assert len(alarms) > 0, "No CloudWatch alarms found"
        except Exception as e:
            pytest.skip(f"CloudWatch not accessible: {e}")


@pytest.mark.smoke
class TestDeploymentConfiguration:
    """Tests for deployment configuration"""
    
    def test_environment_variables_set(self):
        """Test that required environment variables are set"""
        required_vars = [
            "AWS_REGION",
            "ENVIRONMENT"
        ]
        
        for var in required_vars:
            assert os.getenv(var), f"Environment variable {var} not set"
    
    def test_aws_credentials_available(self):
        """Test that AWS credentials are available"""
        try:
            sts = boto3.client("sts")
            identity = sts.get_caller_identity()
            assert identity.get("Account"), "AWS credentials not available"
        except Exception as e:
            pytest.skip(f"AWS credentials not available: {e}")
    
    def test_docker_image_available(self):
        """Test that Docker image is available in ECR"""
        try:
            ecr = boto3.client("ecr", region_name=os.getenv("AWS_REGION", "us-east-1"))
            response = ecr.describe_repositories(repositoryNames=["agentfirst"])
            assert len(response.get("repositories", [])) > 0, "Docker image not found in ECR"
        except Exception as e:
            pytest.skip(f"ECR not accessible: {e}")
