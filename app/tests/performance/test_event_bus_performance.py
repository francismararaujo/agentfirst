"""Performance tests for Event Bus - Test SNS/SQS latency and throughput"""

import pytest
import time
import json
from unittest.mock import patch
from app.core.event_bus import EventBus, EventMessage, EventBusConfig


@pytest.mark.performance
class TestEventBusLatency:
    """Performance tests for Event Bus latency"""

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
    async def test_publish_event_latency(self, event_bus):
        """Test SNS publish latency (should be < 100ms)"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={"order_id": "123", "amount": 100.00},
            user_email="user@example.com"
        )

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-123"}

            start = time.time()
            await event_bus.publish_event(msg)
            elapsed = (time.time() - start) * 1000  # Convert to ms

            assert elapsed < 100, f"Publish took {elapsed}ms, expected < 100ms"

    @pytest.mark.asyncio
    async def test_send_message_latency(self, event_bus):
        """Test SQS send latency (should be < 100ms)"""
        msg = EventMessage(
            event_type="order.confirmed",
            source="retail_agent",
            data={"order_id": "456"},
            user_email="user@example.com"
        )

        with patch.object(event_bus.sqs_client, "send_message") as mock_send:
            mock_send.return_value = {"MessageId": "sqs-msg-1"}

            start = time.time()
            await event_bus.send_message(msg)
            elapsed = (time.time() - start) * 1000

            assert elapsed < 100, f"Send took {elapsed}ms, expected < 100ms"

    @pytest.mark.asyncio
    async def test_receive_messages_latency(self, event_bus):
        """Test SQS receive latency (should be < 500ms with long polling)"""
        with patch.object(event_bus.sqs_client, "receive_message") as mock_receive:
            mock_receive.return_value = {
                "Messages": [
                    {
                        "MessageId": "sqs-msg-1",
                        "Body": json.dumps({
                            "event_type": "order.created",
                            "source": "retail_agent",
                            "data": {}
                        }),
                        "ReceiptHandle": "handle-1"
                    }
                ]
            }

            start = time.time()
            await event_bus.receive_messages()
            elapsed = (time.time() - start) * 1000

            assert elapsed < 500, f"Receive took {elapsed}ms, expected < 500ms"

    @pytest.mark.asyncio
    async def test_delete_message_latency(self, event_bus):
        """Test SQS delete latency (should be < 100ms)"""
        with patch.object(event_bus.sqs_client, "delete_message") as mock_delete:
            start = time.time()
            await event_bus.delete_message(receipt_handle="handle-123")
            elapsed = (time.time() - start) * 1000

            assert elapsed < 100, f"Delete took {elapsed}ms, expected < 100ms"

    @pytest.mark.asyncio
    async def test_send_to_dlq_latency(self, event_bus):
        """Test DLQ send latency (should be < 100ms)"""
        msg = EventMessage(
            event_type="order.failed",
            source="retail_agent",
            data={"order_id": "789"}
        )

        with patch.object(event_bus.sqs_client, "send_message") as mock_send:
            mock_send.return_value = {"MessageId": "dlq-msg-1"}

            start = time.time()
            await event_bus.send_to_dlq(msg, reason="Max retries exceeded")
            elapsed = (time.time() - start) * 1000

            assert elapsed < 100, f"DLQ send took {elapsed}ms, expected < 100ms"


@pytest.mark.performance
class TestEventBusThroughput:
    """Performance tests for Event Bus throughput"""

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
    async def test_publish_throughput(self, event_bus):
        """Test SNS publish throughput (should be > 100 msg/s)"""
        num_messages = 50

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-123"}

            start = time.time()

            for i in range(num_messages):
                msg = EventMessage(
                    event_type="order.created",
                    source="retail_agent",
                    data={"order_id": str(i)},
                    user_email=f"user{i}@example.com"
                )
                await event_bus.publish_event(msg)

            elapsed = time.time() - start
            throughput = num_messages / elapsed

            assert throughput > 100, f"Throughput {throughput} msg/s, expected > 100 msg/s"

    @pytest.mark.asyncio
    async def test_send_message_throughput(self, event_bus):
        """Test SQS send throughput (should be > 100 msg/s)"""
        num_messages = 50

        with patch.object(event_bus.sqs_client, "send_message") as mock_send:
            mock_send.return_value = {"MessageId": "sqs-msg-1"}

            start = time.time()

            for i in range(num_messages):
                msg = EventMessage(
                    event_type="order.confirmed",
                    source="retail_agent",
                    data={"order_id": str(i)},
                    user_email=f"user{i}@example.com"
                )
                await event_bus.send_message(msg)

            elapsed = time.time() - start
            throughput = num_messages / elapsed

            assert throughput > 100, f"Throughput {throughput} msg/s, expected > 100 msg/s"

    @pytest.mark.asyncio
    async def test_receive_throughput(self, event_bus):
        """Test SQS receive throughput (should be > 50 msg/s)"""
        num_batches = 10

        with patch.object(event_bus.sqs_client, "receive_message") as mock_receive:
            mock_receive.return_value = {
                "Messages": [
                    {
                        "MessageId": f"sqs-msg-{i}",
                        "Body": json.dumps({
                            "event_type": "order.created",
                            "source": "retail_agent",
                            "data": {"order_id": str(i)}
                        }),
                        "ReceiptHandle": f"handle-{i}"
                    }
                    for i in range(10)
                ]
            }

            start = time.time()

            for _ in range(num_batches):
                await event_bus.receive_messages(max_messages=10)

            elapsed = time.time() - start
            total_messages = num_batches * 10
            throughput = total_messages / elapsed

            assert throughput > 50, f"Throughput {throughput} msg/s, expected > 50 msg/s"

    @pytest.mark.asyncio
    async def test_delete_throughput(self, event_bus):
        """Test SQS delete throughput (should be > 100 msg/s)"""
        num_messages = 50

        with patch.object(event_bus.sqs_client, "delete_message") as mock_delete:
            start = time.time()

            for i in range(num_messages):
                await event_bus.delete_message(receipt_handle=f"handle-{i}")

            elapsed = time.time() - start
            throughput = num_messages / elapsed

            assert throughput > 100, f"Throughput {throughput} msg/s, expected > 100 msg/s"


@pytest.mark.performance
class TestEventBusMessageSize:
    """Performance tests for Event Bus message sizes"""

    @pytest.fixture
    def event_bus(self):
        """Create event bus instance"""
        config = EventBusConfig(
            sns_topic_arn="arn:aws:sns:us-east-1:123456789:omnichannel",
            sqs_queue_url="https://sqs.us-east-1.amazonaws.com/123456789/events"
        )
        return EventBus(config)

    @pytest.mark.asyncio
    async def test_small_message_performance(self, event_bus):
        """Test performance with small messages (< 1KB)"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={"order_id": "123"},
            user_email="user@example.com"
        )

        message_size = len(msg.to_json())
        assert message_size < 1024, f"Message size {message_size} bytes, expected < 1KB"

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-123"}

            start = time.time()
            await event_bus.publish_event(msg)
            elapsed = (time.time() - start) * 1000

            assert elapsed < 100, f"Small message took {elapsed}ms, expected < 100ms"

    @pytest.mark.asyncio
    async def test_large_message_performance(self, event_bus):
        """Test performance with large messages (< 256KB)"""
        # Create a large payload (100KB)
        large_data = "x" * (100 * 1024)
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={"order_id": "123", "payload": large_data},
            user_email="user@example.com"
        )

        message_size = len(msg.to_json())
        assert message_size < 256 * 1024, f"Message size {message_size} bytes, expected < 256KB"

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-123"}

            start = time.time()
            await event_bus.publish_event(msg)
            elapsed = (time.time() - start) * 1000

            assert elapsed < 500, f"Large message took {elapsed}ms, expected < 500ms"

    @pytest.mark.asyncio
    async def test_message_with_metadata_performance(self, event_bus):
        """Test performance with messages containing metadata"""
        msg = EventMessage(
            event_type="order.created",
            source="retail_agent",
            data={"order_id": "123"},
            metadata={
                "priority": "high",
                "retry_count": 0,
                "source_system": "ifood",
                "tags": ["urgent", "vip", "premium"],
                "custom_fields": {
                    "field1": "value1",
                    "field2": "value2",
                    "field3": "value3"
                }
            }
        )

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-123"}

            start = time.time()
            await event_bus.publish_event(msg)
            elapsed = (time.time() - start) * 1000

            assert elapsed < 100, f"Message with metadata took {elapsed}ms, expected < 100ms"


@pytest.mark.performance
class TestEventBusScalability:
    """Performance tests for Event Bus scalability"""

    @pytest.fixture
    def event_bus(self):
        """Create event bus instance"""
        config = EventBusConfig(
            sns_topic_arn="arn:aws:sns:us-east-1:123456789:omnichannel",
            sqs_queue_url="https://sqs.us-east-1.amazonaws.com/123456789/events"
        )
        return EventBus(config)

    @pytest.mark.asyncio
    async def test_burst_publishing(self, event_bus):
        """Test burst publishing (100 messages in < 2 seconds)"""
        num_messages = 100

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-123"}

            start = time.time()

            for i in range(num_messages):
                msg = EventMessage(
                    event_type="order.created",
                    source="retail_agent",
                    data={"order_id": str(i)},
                    user_email=f"user{i % 10}@example.com"
                )
                await event_bus.publish_event(msg)

            elapsed = time.time() - start

            assert elapsed < 2, f"Burst publishing took {elapsed}s, expected < 2s"
            assert len(event_bus.published_messages) == num_messages

    @pytest.mark.asyncio
    async def test_sustained_publishing(self, event_bus):
        """Test sustained publishing (1000 messages)"""
        num_messages = 1000

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-123"}

            start = time.time()

            for i in range(num_messages):
                msg = EventMessage(
                    event_type="order.created",
                    source="retail_agent",
                    data={"order_id": str(i)},
                    user_email=f"user{i % 100}@example.com"
                )
                await event_bus.publish_event(msg)

            elapsed = time.time() - start
            throughput = num_messages / elapsed

            assert throughput > 100, f"Throughput {throughput} msg/s, expected > 100 msg/s"
            assert len(event_bus.published_messages) == num_messages

    @pytest.mark.asyncio
    async def test_mixed_operations_performance(self, event_bus):
        """Test performance with mixed publish/receive/delete operations"""
        num_operations = 100

        with patch.object(event_bus.sns_client, "publish") as mock_publish, \
             patch.object(event_bus.sqs_client, "send_message") as mock_send, \
             patch.object(event_bus.sqs_client, "receive_message") as mock_receive, \
             patch.object(event_bus.sqs_client, "delete_message") as mock_delete:

            mock_publish.return_value = {"MessageId": "msg-123"}
            mock_send.return_value = {"MessageId": "sqs-msg-1"}
            mock_receive.return_value = {
                "Messages": [
                    {
                        "MessageId": "sqs-msg-1",
                        "Body": json.dumps({"event_type": "order.created"}),
                        "ReceiptHandle": "handle-1"
                    }
                ]
            }

            start = time.time()

            for i in range(num_operations):
                msg = EventMessage(
                    event_type="order.created",
                    source="retail_agent",
                    data={"order_id": str(i)}
                )

                # Publish to SNS
                await event_bus.publish_event(msg)

                # Send to SQS
                await event_bus.send_message(msg)

                # Receive from SQS
                if i % 10 == 0:
                    await event_bus.receive_messages()

                # Delete from SQS
                if i % 10 == 0:
                    await event_bus.delete_message(receipt_handle="handle-1")

            elapsed = time.time() - start

            assert elapsed < 10, f"Mixed operations took {elapsed}s, expected < 10s"


@pytest.mark.performance
class TestEventBusMemoryUsage:
    """Performance tests for Event Bus memory usage"""

    @pytest.fixture
    def event_bus(self):
        """Create event bus instance"""
        config = EventBusConfig(
            sns_topic_arn="arn:aws:sns:us-east-1:123456789:omnichannel",
            sqs_queue_url="https://sqs.us-east-1.amazonaws.com/123456789/events"
        )
        return EventBus(config)

    @pytest.mark.asyncio
    async def test_message_tracking_memory(self, event_bus):
        """Test memory usage for message tracking"""
        num_messages = 1000

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            mock_publish.return_value = {"MessageId": "msg-123"}

            for i in range(num_messages):
                msg = EventMessage(
                    event_type="order.created",
                    source="retail_agent",
                    data={"order_id": str(i)}
                )
                await event_bus.publish_event(msg)

            # Verify tracking lists don't grow unbounded
            assert len(event_bus.published_messages) == num_messages
            assert len(event_bus.failed_messages) == 0

    @pytest.mark.asyncio
    async def test_failed_message_tracking(self, event_bus):
        """Test memory usage for failed message tracking"""
        num_messages = 100

        with patch.object(event_bus.sns_client, "publish") as mock_publish:
            from botocore.exceptions import ClientError

            mock_publish.side_effect = ClientError(
                {"Error": {"Code": "InvalidParameter"}},
                "Publish"
            )

            for i in range(num_messages):
                msg = EventMessage(
                    event_type="order.created",
                    source="retail_agent",
                    data={"order_id": str(i)},
                    correlation_id=f"corr-{i}"
                )

                try:
                    await event_bus.publish_event(msg)
                except ClientError:
                    pass

            # Verify failed messages are tracked
            assert len(event_bus.failed_messages) == num_messages
