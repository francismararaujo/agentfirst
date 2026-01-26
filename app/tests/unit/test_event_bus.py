"""Unit tests for Event Bus - Test SNS/SQS event publishing and consumption"""

import pytest
import json
from unittest.mock import patch
from app.core.event_bus import EventBus, EventMessage, EventBusConfig


@pytest.mark.unit
class TestEventMessage:
    """Tests for EventMessage class"""

    def test_event_message_creation(self):
        """Test creating an event message"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={"order_id": "123", "amount": 100.00},
            user_email="user@example.com"
        )

        assert msg.event_type == "order.created"
        assert msg.source == "retail_agent"
        assert msg.data["order_id"] == "123"
        assert msg.user_email == "user@example.com"
        assert msg.correlation_id is not None
        assert msg.timestamp is not None

    def test_event_message_to_dict(self):
        """Test converting event message to dictionary"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={"order_id": "123"},
            correlation_id="corr-123"
        )

        result = msg.to_dict()

        assert result["event_type"] == "order.created"
        assert result["source"] == "retail_agent"
        assert result["correlation_id"] == "corr-123"
        assert "timestamp" in result

    def test_event_message_to_json(self):
        """Test converting event message to JSON"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={"order_id": "123"}
        )

        result = msg.to_json()

        assert isinstance(result, str)
        data = json.loads(result)
        assert data["event_type"] == "order.created"

    def test_event_message_from_dict(self):
        """Test creating event message from dictionary"""
        data = {
            "event_type": "order.created",
            "source": "retail_agent",
            "data": {"order_id": "123"},
            "correlation_id": "corr-123",
            "user_email": "user@example.com",
            "timestamp": "2024-01-01T10:00:00"
        }

        msg = EventMessage.from_dict(data)

        assert msg.event_type == "order.created"
        assert msg.correlation_id == "corr-123"
        assert msg.timestamp == "2024-01-01T10:00:00"

    def test_event_message_auto_correlation_id(self):
        """Test that correlation ID is auto-generated"""
        msg1 = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={}
        )
        msg2 = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={}
        )

        assert msg1.correlation_id != msg2.correlation_id


@pytest.mark.unit
class TestEventBusConfig:
    """Tests for EventBusConfig class"""

    def test_config_creation_with_defaults(self):
        """Test creating config with default values"""
        config = EventBusConfig()

        assert config.region == "us-east-1"
        assert config.enable_encryption is True
        assert config.message_retention_seconds == 345600
        assert config.visibility_timeout_seconds == 300
        assert config.dlq_retention_seconds == 1209600

    def test_config_creation_with_custom_values(self):
        """Test creating config with custom values"""
        config = EventBusConfig(
            region="eu-west-1",
            sns_topic_arn="arn:aws:sns:eu-west-1:123456789:topic",
            sqs_queue_url="https://sqs.eu-west-1.amazonaws.com/123456789/queue",
            enable_encryption=False
        )

        assert config.region == "eu-west-1"
        assert config.sns_topic_arn == "arn:aws:sns:eu-west-1:123456789:topic"
        assert config.enable_encryption is False


@pytest.mark.unit
class TestEventBusPublish:
    """Tests for EventBus publish functionality"""

    @pytest.fixture
    def event_bus(self):
        """Create event bus instance"""
        config = EventBusConfig(
            sns_topic_arn="arn:aws:sns:us-east-1:123456789:topic",
            sqs_queue_url="https://sqs.us-east-1.amazonaws.com/123456789/queue",
            sqs_dlq_url="https://sqs.us-east-1.amazonaws.com/123456789/dlq"
        )
        return EventBus(config)

    @pytest.mark.asyncio
    async def test_publish_event_success(self, event_bus):
        """Test publishing event successfully"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={"order_id": "123"}
        )

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-123"}

            result = await event_bus.publish_event(msg)

            assert result == "msg-123"
            assert "msg-123" in event_bus.published_messages
            mock_publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_event_no_topic_arn(self, event_bus):
        """Test publishing event without topic ARN"""
        event_bus.config.sns_topic_arn = None
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={}
        )

        with pytest.raises(ValueError):
            await event_bus.publish_event(msg)

    @pytest.mark.asyncio
    async def test_publish_event_with_user_email(self, event_bus):
        """Test publishing event with user email"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={"order_id": "123"},
            user_email="user@example.com"
        )

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-123"}

            await event_bus.publish_event(msg)

            call_args = mock_publish.call_args
            assert "user_email" in call_args[1]["MessageAttributes"]

    @pytest.mark.asyncio
    async def test_publish_event_failure(self, event_bus):
        """Test publishing event failure"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={}
        )

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            from botocore.exceptions import ClientError
            mock_publish.side_effect = ClientError(
                {"Error": {"Code": "InvalidParameter"}},
                "Publish"
            )

            with pytest.raises(ClientError):
                await event_bus.publish_event(msg)

            assert msg.correlation_id in event_bus.failed_messages


@pytest.mark.unit
class TestEventBusSQS:
    """Tests for EventBus SQS functionality"""

    @pytest.fixture
    def event_bus(self):
        """Create event bus instance"""
        config = EventBusConfig(
            sqs_queue_url="https://sqs.us-east-1.amazonaws.com/123456789/queue",
            sqs_dlq_url="https://sqs.us-east-1.amazonaws.com/123456789/dlq"
        )
        return EventBus(config)

    @pytest.mark.asyncio
    async def test_send_message_success(self, event_bus):
        """Test sending message to SQS"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={"order_id": "123"},
            user_email="user@example.com"
        )

        with patch.object(event_bus.sqs_client, "send_message") as mock_send:
            mock_send.return_value = {"MessageId": "msg-123"}

            result = await event_bus.send_message(msg)

            assert result == "msg-123"
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_receive_messages_success(self, event_bus):
        """Test receiving messages from SQS"""
        with patch.object(event_bus.sqs_client, "receive_message") as mock_receive:
            mock_receive.return_value = {
                "Messages": [
                    {
                        "MessageId": "msg-1",
                        "Body": json.dumps({
                            "event_type": "order.created",
                            "source": "retail_agent",
                            "data": {}
                        }),
                        "ReceiptHandle": "handle-1"
                    }
                ]
            }

            result = await event_bus.receive_messages()

            assert len(result) == 1
            assert result[0]["MessageId"] == "msg-1"

    @pytest.mark.asyncio
    async def test_receive_messages_empty(self, event_bus):
        """Test receiving messages when queue is empty"""
        with patch.object(event_bus.sqs_client, "receive_message") as mock_receive:
            mock_receive.return_value = {}

            result = await event_bus.receive_messages()

            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_delete_message_success(self, event_bus):
        """Test deleting message from SQS"""
        with patch.object(event_bus.sqs_client, "delete_message") as mock_delete:
            result = await event_bus.delete_message(
                receipt_handle="handle-123"
            )

            assert result is True
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_message_no_receipt_handle(self, event_bus):
        """Test deleting message without receipt handle"""
        with pytest.raises(ValueError):
            await event_bus.delete_message(receipt_handle=None)

    @pytest.mark.asyncio
    async def test_send_to_dlq_success(self, event_bus):
        """Test sending message to DLQ"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={}
        )

        with patch.object(event_bus.sqs_client, "send_message") as mock_send:
            mock_send.return_value = {"MessageId": "msg-dlq-123"}

            result = await event_bus.send_to_dlq(
                msg,
                reason="Processing failed"
            )

            assert result == "msg-dlq-123"
            assert msg.metadata["dlq_reason"] == "Processing failed"

    def test_get_queue_attributes_success(self, event_bus):
        """Test getting queue attributes"""
        with patch.object(event_bus.sqs_client, "get_queue_attributes") as mock_get:
            mock_get.return_value = {
                "Attributes": {
                    "ApproximateNumberOfMessages": "10",
                    "ApproximateNumberOfMessagesNotVisible": "2"
                }
            }

            result = event_bus.get_queue_attributes()

            assert result["ApproximateNumberOfMessages"] == "10"

    def test_get_topic_attributes_success(self, event_bus):
        """Test getting topic attributes"""
        event_bus.config.sns_topic_arn = "arn:aws:sns:us-east-1:123456789:topic"

        with patch.object(event_bus.sns_client, "get_topic_attributes") as mock_get:
            mock_get.return_value = {
                "Attributes": {
                    "TopicArn": "arn:aws:sns:us-east-1:123456789:topic",
                    "DisplayName": "Test Topic"
                }
            }

            result = event_bus.get_topic_attributes()

            assert "TopicArn" in result


@pytest.mark.unit
class TestEventBusMetrics:
    """Tests for EventBus metrics tracking"""

    @pytest.fixture
    def event_bus(self):
        """Create event bus instance"""
        config = EventBusConfig(
            sns_topic_arn="arn:aws:sns:us-east-1:123456789:topic",
            sqs_queue_url="https://sqs.us-east-1.amazonaws.com/123456789/queue"
        )
        return EventBus(config)

    @pytest.mark.asyncio
    async def test_published_messages_tracking(self, event_bus):
        """Test tracking published messages"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={}
        )

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-1"}

            await event_bus.publish_event(msg)

            assert len(event_bus.published_messages) == 1
            assert "msg-1" in event_bus.published_messages

    @pytest.mark.asyncio
    async def test_failed_messages_tracking(self, event_bus):
        """Test tracking failed messages"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={},
            correlation_id="corr-123"
        )

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            from botocore.exceptions import ClientError
            mock_publish.side_effect = ClientError(
                {"Error": {"Code": "InvalidParameter"}},
                "Publish"
            )

            with pytest.raises(ClientError):
                await event_bus.publish_event(msg)

            assert len(event_bus.failed_messages) == 1
            assert "corr-123" in event_bus.failed_messages
