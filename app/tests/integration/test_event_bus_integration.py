"""Integration tests for Event Bus - Test SNS/SQS workflows"""

import pytest
import json
from unittest.mock import patch
from app.core.event_bus import EventBus, EventMessage, EventBusConfig


@pytest.mark.integration
class TestEventBusIntegration:
    """Integration tests for Event Bus"""

    @pytest.fixture
    def event_bus(self):
        """Create event bus instance"""
        config = EventBusConfig(
            sns_topic_arn="arn:aws:sns:us-east-1:123456789:omnichannel",
            sqs_queue_url="https://sqs.us-east-1.amazonaws.com/123456789/events",
            sqs_dlq_url="https://sqs.us-east-1.amazonaws.com/123456789/events-dlq"
        )
        return EventBus(config)

    @pytest.mark.asyncio
    async def test_publish_and_receive_workflow(self, event_bus):
        """Test complete publish and receive workflow"""
        # Create event
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={"order_id": "123", "amount": 100.00},
            user_email="user@example.com"
        )

        # Mock SNS publish
        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-123"}

            # Publish event
            message_id = await event_bus.publish_event(msg)

            assert message_id == "msg-123"
            assert len(event_bus.published_messages) == 1

    @pytest.mark.asyncio
    async def test_sqs_message_lifecycle(self, event_bus):
        """Test complete SQS message lifecycle"""
        # Create event
        msg = EventMessage(
            event_type="order.confirmed",
            source="retail_agent",
            data={"order_id": "456"},
            user_email="user@example.com"
        )

        # Mock SQS send
        with patch.object(event_bus.sqs_client, "send_message") as mock_send:
            mock_send.return_value = {"MessageId": "sqs-msg-1"}

            # Send message
            message_id = await event_bus.send_message(msg)
            assert message_id == "sqs-msg-1"

        # Mock SQS receive
        with patch.object(event_bus.sqs_client, "receive_message") as mock_receive:
            mock_receive.return_value = {
                "Messages": [
                    {
                        "MessageId": "sqs-msg-1",
                        "Body": msg.to_json(),
                        "ReceiptHandle": "handle-1"
                    }
                ]
            }

            # Receive message
            messages = await event_bus.receive_messages()
            assert len(messages) == 1

        # Mock SQS delete
        with patch.object(event_bus.sqs_client, "delete_message") as mock_delete:
            # Delete message
            result = await event_bus.delete_message(receipt_handle="handle-1")
            assert result is True

    @pytest.mark.asyncio
    async def test_dlq_workflow(self, event_bus):
        """Test Dead Letter Queue workflow"""
        # Create event
        msg = EventMessage(
            event_type="order.failed",
            source="retail_agent",
            data={"order_id": "789"},
            correlation_id="corr-789"
        )

        # Mock SQS send to DLQ
        with patch.object(event_bus.sqs_client, "send_message") as mock_send:
            mock_send.return_value = {"MessageId": "dlq-msg-1"}

            # Send to DLQ
            message_id = await event_bus.send_to_dlq(
                msg,
                reason="Max retries exceeded"
            )

            assert message_id == "dlq-msg-1"
            assert msg.metadata["dlq_reason"] == "Max retries exceeded"

    @pytest.mark.asyncio
    async def test_multiple_events_publishing(self, event_bus):
        """Test publishing multiple events"""
        events = [
            EventMessage(
                event_type="order.created",
                source="retail_agent",
                data={"order_id": str(i)},
                user_email=f"user{i}@example.com"
            )
            for i in range(5)
        ]

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-123"}

            # Publish all events
            for event in events:
                await event_bus.publish_event(event)

            assert len(event_bus.published_messages) == 5
            assert mock_publish.call_count == 5

    @pytest.mark.asyncio
    async def test_event_with_metadata(self, event_bus):
        """Test event with custom metadata"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={"order_id": "123"},
            metadata={
                "priority": "high",
                "retry_count": 0,
                "source_system": "ifood"
            }
        )

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-123"}

            await event_bus.publish_event(msg)

            # Verify metadata is included
            call_args = mock_publish.call_args
            message_body = json.loads(call_args[1]["Message"])
            assert message_body["metadata"]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_correlation_id_tracking(self, event_bus):
        """Test correlation ID tracking across events"""
        correlation_id = "corr-workflow-123"

        events = [
            EventMessage(
                event_type="order.created",
                source="retail_agent",
                data={"order_id": "123"},
                correlation_id=correlation_id
            ),
            EventMessage(
                event_type="order.confirmed",
                source="retail_agent",
                data={"order_id": "123"},
                correlation_id=correlation_id
            ),
            EventMessage(
                event_type="order.shipped",
                source="retail_agent",
                data={"order_id": "123"},
                correlation_id=correlation_id
            )
        ]

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-123"}

            for event in events:
                await event_bus.publish_event(event)

            # Verify all events have same correlation ID
            for call in mock_publish.call_args_list:
                message_body = json.loads(call[1]["Message"])
                assert message_body["correlation_id"] == correlation_id


@pytest.mark.integration
class TestEventBusErrorHandling:
    """Integration tests for Event Bus error handling"""

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
    async def test_publish_retry_on_failure(self, event_bus):
        """Test retry logic on publish failure"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={"order_id": "123"},
            correlation_id="corr-123"
        )

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            from botocore.exceptions import ClientError

            # First call fails, second succeeds
            mock_publish.side_effect = [
                ClientError(
                    {"Error": {"Code": "ServiceUnavailable"}},
                    "Publish"
                ),
                {"MessageId": "msg-123"}
            ]

            # First attempt fails
            with pytest.raises(ClientError):
                await event_bus.publish_event(msg)

            assert "corr-123" in event_bus.failed_messages

    @pytest.mark.asyncio
    async def test_receive_with_timeout(self, event_bus):
        """Test receiving messages with timeout"""
        with patch.object(event_bus.sqs_client, "receive_message") as mock_receive:
            mock_receive.return_value = {}

            # Should return empty list on timeout
            result = await event_bus.receive_messages(wait_time_seconds=20)

            assert result == []

    @pytest.mark.asyncio
    async def test_message_attributes_preservation(self, event_bus):
        """Test that message attributes are preserved"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={"order_id": "123"},
            user_email="user@example.com",
            correlation_id="corr-123"
        )

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-123"}

            await event_bus.publish_event(msg)

            # Verify attributes
            call_args = mock_publish.call_args
            attributes = call_args[1]["MessageAttributes"]

            assert attributes["event_type"]["StringValue"] == "order.created"
            assert attributes["source"]["StringValue"] == "retail_agent"
            assert attributes["correlation_id"]["StringValue"] == "corr-123"
            assert attributes["user_email"]["StringValue"] == "user@example.com"
