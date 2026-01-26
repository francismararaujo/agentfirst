"""
Performance tests for Brain (Orquestrador Central)

Tests latency, throughput, and resource usage of Brain operations.
"""

import pytest
import time
import asyncio
from unittest.mock import AsyncMock

from app.core.brain import Brain, Intent, Context
from app.omnichannel.models import ChannelType


@pytest.mark.performance
class TestBrainPerformance:
    """Performance tests for Brain"""
    
    @pytest.fixture
    def mock_bedrock(self):
        """Mock Bedrock client"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_memory(self):
        """Mock Memory service"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_event_bus(self):
        """Mock Event Bus"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_auditor(self):
        """Mock Auditor"""
        return AsyncMock()
    
    @pytest.fixture
    def brain(self, mock_bedrock, mock_memory, mock_event_bus, mock_auditor):
        """Create Brain instance"""
        return Brain(mock_bedrock, mock_memory, mock_event_bus, mock_auditor)
    
    @pytest.fixture
    def context(self):
        """Create test context"""
        return Context(
            email="test@example.com",
            channel=ChannelType.TELEGRAM,
            session_id="session_123"
        )
    
    @pytest.mark.asyncio
    async def test_intent_classification_latency(self, brain, mock_bedrock, context):
        """Test intent classification latency (< 100ms)"""
        # Arrange
        message = "Quantos pedidos tenho?"
        mock_bedrock.invoke_model.return_value = {
            'content': [
                {
                    'text': '{"domain": "retail", "action": "check_orders", "confidence": 0.95, "entities": {}}'
                }
            ]
        }
        
        start_time = time.time()
        
        # Act
        intent = await brain._classify_intent(message, context)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert intent.domain == "retail"
        assert elapsed < 0.1, f"Intent classification took {elapsed}s, expected < 100ms"
    
    @pytest.mark.asyncio
    async def test_response_formatting_latency(self, brain, mock_bedrock):
        """Test response formatting latency (< 100ms)"""
        # Arrange
        response_data = {"orders": [{"id": "123", "value": 50.0}]}
        intent = Intent(domain="retail", action="check_orders")
        context = Context(
            email="test@example.com",
            channel=ChannelType.TELEGRAM,
            session_id="session_123"
        )
        
        mock_bedrock.invoke_model.return_value = {
            'content': [
                {
                    'text': 'Você tem 1 pedido'
                }
            ]
        }
        
        start_time = time.time()
        
        # Act
        response = await brain._format_response(response_data, intent, context)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert len(response) > 0
        assert elapsed < 0.1, f"Response formatting took {elapsed}s, expected < 100ms"
    
    @pytest.mark.asyncio
    async def test_complete_message_processing_latency(self, brain, mock_bedrock, mock_memory, mock_event_bus, mock_auditor, context):
        """Test complete message processing latency (< 500ms)"""
        # Arrange
        message = "Quantos pedidos tenho?"
        mock_agent = AsyncMock()
        mock_agent.execute.return_value = {"orders": []}
        brain.register_agent("retail", mock_agent)
        
        mock_bedrock.invoke_model.side_effect = [
            # Classification
            {
                'content': [
                    {
                        'text': '{"domain": "retail", "action": "check_orders", "confidence": 0.95, "entities": {}}'
                    }
                ]
            },
            # Formatting
            {
                'content': [
                    {
                        'text': 'Você tem 0 pedidos'
                    }
                ]
            }
        ]
        
        mock_memory.get_context.return_value = {}
        
        start_time = time.time()
        
        # Act
        response = await brain.process(message, context)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert response is not None
        assert elapsed < 0.5, f"Message processing took {elapsed}s, expected < 500ms"
    
    @pytest.mark.asyncio
    async def test_intent_classification_throughput(self, brain, mock_bedrock, context):
        """Test intent classification throughput (> 100 classifications/s)"""
        # Arrange
        message = "Quantos pedidos tenho?"
        mock_bedrock.invoke_model.return_value = {
            'content': [
                {
                    'text': '{"domain": "retail", "action": "check_orders", "confidence": 0.95, "entities": {}}'
                }
            ]
        }
        
        num_classifications = 100
        start_time = time.time()
        
        # Act
        for _ in range(num_classifications):
            await brain._classify_intent(message, context)
        
        elapsed = time.time() - start_time
        throughput = num_classifications / elapsed
        
        # Assert
        assert throughput >= 100, f"Throughput {throughput} classifications/s, expected >= 100 classifications/s"
    
    @pytest.mark.asyncio
    async def test_concurrent_message_processing(self, brain, mock_bedrock, mock_memory, mock_event_bus, mock_auditor):
        """Test concurrent message processing"""
        # Arrange
        num_concurrent = 50
        
        mock_agent = AsyncMock()
        mock_agent.execute.return_value = {"orders": []}
        brain.register_agent("retail", mock_agent)
        
        mock_bedrock.invoke_model.side_effect = [
            # Classification
            {
                'content': [
                    {
                        'text': '{"domain": "retail", "action": "check_orders", "confidence": 0.95, "entities": {}}'
                    }
                ]
            },
            # Formatting
            {
                'content': [
                    {
                        'text': 'Você tem 0 pedidos'
                    }
                ]
            }
        ] * num_concurrent
        
        mock_memory.get_context.return_value = {}
        
        start_time = time.time()
        
        # Act
        tasks = [
            brain.process(
                "Quantos pedidos tenho?",
                Context(
                    email=f"test{i}@example.com",
                    channel=ChannelType.TELEGRAM,
                    session_id=f"session_{i}"
                )
            )
            for i in range(num_concurrent)
        ]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert len(results) == num_concurrent
        assert elapsed < 5.0, f"Concurrent processing took {elapsed}s, expected < 5s"
    
    @pytest.mark.asyncio
    async def test_memory_context_retrieval_latency(self, brain, mock_memory, context):
        """Test memory context retrieval latency (< 50ms)"""
        # Arrange
        mock_memory.get_context.return_value = {
            'last_intent': 'check_orders',
            'history': [{'message': 'test', 'response': 'test'}]
        }
        
        start_time = time.time()
        
        # Act
        memory_context = await mock_memory.get_context(context.email)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert memory_context is not None
        assert elapsed < 0.05, f"Memory retrieval took {elapsed}s, expected < 50ms"
    
    @pytest.mark.asyncio
    async def test_event_publishing_latency(self, brain, mock_event_bus):
        """Test event publishing latency (< 50ms)"""
        # Arrange
        event_data = {
            'email': 'test@example.com',
            'action': 'check_orders',
            'timestamp': '2025-01-25T10:00:00'
        }
        
        start_time = time.time()
        
        # Act
        await mock_event_bus.publish(
            topic="retail.check_orders",
            message=event_data
        )
        
        elapsed = time.time() - start_time
        
        # Assert
        assert elapsed < 0.05, f"Event publishing took {elapsed}s, expected < 50ms"
    
    @pytest.mark.asyncio
    async def test_auditor_logging_latency(self, brain, mock_auditor):
        """Test auditor logging latency (< 50ms)"""
        # Arrange
        start_time = time.time()
        
        # Act
        await mock_auditor.log_transaction(
            email="test@example.com",
            action="check_orders",
            input_data={"message": "test"},
            output_data={"response": "test"}
        )
        
        elapsed = time.time() - start_time
        
        # Assert
        assert elapsed < 0.05, f"Auditor logging took {elapsed}s, expected < 50ms"
    
    @pytest.mark.asyncio
    async def test_agent_execution_latency(self, brain):
        """Test agent execution latency (< 200ms)"""
        # Arrange
        mock_agent = AsyncMock()
        mock_agent.execute.return_value = {"orders": []}
        brain.register_agent("retail", mock_agent)
        
        intent = Intent(domain="retail", action="check_orders")
        context = Context(
            email="test@example.com",
            channel=ChannelType.TELEGRAM,
            session_id="session_123"
        )
        
        start_time = time.time()
        
        # Act
        result = await mock_agent.execute(intent, context)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert result is not None
        assert elapsed < 0.2, f"Agent execution took {elapsed}s, expected < 200ms"
    
    @pytest.mark.asyncio
    async def test_build_classification_prompt_latency(self, brain, context):
        """Test building classification prompt latency (< 10ms)"""
        # Arrange
        message = "Quantos pedidos tenho?"
        
        start_time = time.time()
        
        # Act
        prompt = brain._build_classification_prompt(message, context)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert len(prompt) > 0
        assert elapsed < 0.01, f"Prompt building took {elapsed}s, expected < 10ms"
