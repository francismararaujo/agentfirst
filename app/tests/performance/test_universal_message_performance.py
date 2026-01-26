"""
Performance tests for universal message processing.

Tests latency, throughput, and resource usage of message processing.
"""

import pytest
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.omnichannel.models import UniversalMessage, ChannelType
from app.omnichannel.universal_message_processor import UniversalMessageProcessor
from app.omnichannel.channel_mapping_service import ChannelMappingService


@pytest.mark.performance
class TestUniversalMessagePerformance:
    """Performance tests for message processing"""
    
    @pytest.fixture
    def mock_channel_mapping(self):
        """Mock channel mapping service"""
        service = AsyncMock(spec=ChannelMappingService)
        service.get_email_by_channel_id = AsyncMock(return_value="user@example.com")
        return service
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager"""
        manager = AsyncMock()
        mock_session = MagicMock()
        mock_session.session_id = "session_123"
        manager.get = AsyncMock(return_value=mock_session)
        return manager
    
    @pytest.fixture
    def mock_memory_service(self):
        """Mock memory service"""
        service = AsyncMock()
        service.get_context = AsyncMock(return_value={
            'last_intent': 'check_orders',
            'last_connector': 'ifood',
            'conversation_history': [],
            'user_preferences': {}
        })
        service.update_context = AsyncMock()
        return service
    
    @pytest.fixture
    def processor(self, mock_channel_mapping, mock_session_manager, mock_memory_service):
        """Create processor instance"""
        return UniversalMessageProcessor(
            channel_mapping_service=mock_channel_mapping,
            session_manager=mock_session_manager,
            memory_service=mock_memory_service
        )
    
    @pytest.mark.asyncio
    async def test_message_processing_latency(self, processor):
        """Test that message processing completes within SLA (< 2 seconds)"""
        # Arrange
        start_time = time.time()
        
        # Act
        await processor.process_message(
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            message_text="Quantos pedidos tenho?",
            message_id="msg_123"
        )
        
        elapsed = time.time() - start_time
        
        # Assert - Should complete in < 2 seconds
        assert elapsed < 2.0, f"Message processing took {elapsed}s, expected < 2s"
    
    @pytest.mark.asyncio
    async def test_email_extraction_latency(self, processor):
        """Test that email extraction completes quickly (< 100ms)"""
        # Arrange
        start_time = time.time()
        
        # Act
        email = await processor._extract_email(ChannelType.TELEGRAM, "123456")
        
        elapsed = time.time() - start_time
        
        # Assert
        assert email == "user@example.com"
        assert elapsed < 0.1, f"Email extraction took {elapsed}s, expected < 100ms"
    
    @pytest.mark.asyncio
    async def test_context_retrieval_latency(self, processor):
        """Test that context retrieval completes quickly (< 500ms)"""
        # Arrange
        start_time = time.time()
        
        # Act
        context = await processor._retrieve_context("user@example.com")
        
        elapsed = time.time() - start_time
        
        # Assert
        assert context is not None
        assert elapsed < 0.5, f"Context retrieval took {elapsed}s, expected < 500ms"
    
    @pytest.mark.asyncio
    async def test_context_update_latency(self, processor):
        """Test that context update completes quickly (< 500ms)"""
        # Arrange
        start_time = time.time()
        
        # Act
        await processor.update_context(
            email="user@example.com",
            intent="check_orders",
            connector="ifood"
        )
        
        elapsed = time.time() - start_time
        
        # Assert
        assert elapsed < 0.5, f"Context update took {elapsed}s, expected < 500ms"
    
    @pytest.mark.asyncio
    async def test_message_processing_throughput(self, processor):
        """Test processing multiple messages (throughput)"""
        # Arrange
        num_messages = 100
        start_time = time.time()
        
        # Act
        for i in range(num_messages):
            await processor.process_message(
                channel=ChannelType.TELEGRAM,
                channel_user_id=f"user_{i}",
                message_text=f"Message {i}",
                message_id=f"msg_{i}"
            )
        
        elapsed = time.time() - start_time
        throughput = num_messages / elapsed
        
        # Assert - Should process at least 50 messages per second
        assert throughput >= 50, f"Throughput {throughput} msg/s, expected >= 50 msg/s"
    
    @pytest.mark.asyncio
    async def test_universal_message_creation_latency(self):
        """Test that UniversalMessage creation is fast (< 10ms)"""
        # Arrange
        start_time = time.time()
        
        # Act
        msg = UniversalMessage(
            text="Test message",
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            message_id="msg_123",
            timestamp=datetime.now(),
            email="user@example.com"
        )
        
        elapsed = time.time() - start_time
        
        # Assert
        assert msg is not None
        assert elapsed < 0.01, f"Message creation took {elapsed}s, expected < 10ms"
    
    @pytest.mark.asyncio
    async def test_serialization_latency(self):
        """Test that serialization is fast (< 10ms)"""
        # Arrange
        msg = UniversalMessage(
            text="Test message",
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            message_id="msg_123",
            timestamp=datetime.now(),
            email="user@example.com",
            context={'key': 'value'}
        )
        
        start_time = time.time()
        
        # Act
        data = msg.to_dict()
        
        elapsed = time.time() - start_time
        
        # Assert
        assert data is not None
        assert elapsed < 0.01, f"Serialization took {elapsed}s, expected < 10ms"
    
    @pytest.mark.asyncio
    async def test_deserialization_latency(self):
        """Test that deserialization is fast (< 10ms)"""
        # Arrange
        msg = UniversalMessage(
            text="Test message",
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            message_id="msg_123",
            timestamp=datetime.now(),
            email="user@example.com"
        )
        data = msg.to_dict()
        
        start_time = time.time()
        
        # Act
        restored = UniversalMessage.from_dict(data)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert restored is not None
        assert elapsed < 0.01, f"Deserialization took {elapsed}s, expected < 10ms"
    
    @pytest.mark.asyncio
    async def test_concurrent_message_processing(self, processor):
        """Test processing messages concurrently"""
        import asyncio
        
        # Arrange
        num_concurrent = 10
        start_time = time.time()
        
        # Act
        tasks = [
            processor.process_message(
                channel=ChannelType.TELEGRAM,
                channel_user_id=f"user_{i}",
                message_text=f"Message {i}",
                message_id=f"msg_{i}"
            )
            for i in range(num_concurrent)
        ]
        
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        # Assert
        assert len(results) == num_concurrent
        assert elapsed < 2.0, f"Concurrent processing took {elapsed}s, expected < 2s"
    
    @pytest.mark.asyncio
    async def test_memory_usage_with_large_context(self, processor, mock_memory_service):
        """Test memory usage with large conversation context"""
        # Arrange
        large_history = [f"message_{i}" for i in range(1000)]
        mock_memory_service.get_context.return_value = {
            'last_intent': 'check_orders',
            'last_connector': 'ifood',
            'conversation_history': large_history,
            'user_preferences': {'key': 'value'}
        }
        
        # Act
        result = await processor.process_message(
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            message_text="Test",
            message_id="msg_123"
        )
        
        # Assert
        assert len(result.context['conversation_history']) == 1000
        assert result.context['last_intent'] == 'check_orders'
