"""
Performance tests for NLP Universal service.

Tests latency, throughput, and resource usage of NLP processing.
"""

import pytest
import time
import asyncio
from app.omnichannel.nlp_universal import NLPUniversal


@pytest.mark.performance
class TestNLPPerformance:
    """Performance tests for NLP service"""
    
    @pytest.fixture
    def nlp(self):
        """Create NLP service"""
        return NLPUniversal()
    
    @pytest.mark.asyncio
    async def test_intent_classification_latency(self, nlp):
        """Test that intent classification completes within SLA (< 100ms)"""
        # Arrange
        start_time = time.time()
        
        # Act
        await nlp.understand("Quantos pedidos tenho?")
        
        elapsed = time.time() - start_time
        
        # Assert - Should complete in < 100ms
        assert elapsed < 0.1, f"Intent classification took {elapsed}s, expected < 100ms"
    
    @pytest.mark.asyncio
    async def test_entity_extraction_latency(self, nlp):
        """Test that entity extraction completes quickly (< 100ms)"""
        # Arrange
        start_time = time.time()
        
        # Act
        await nlp.understand("Confirme o pedido #12345 no iFood por 30 minutos")
        
        elapsed = time.time() - start_time
        
        # Assert
        assert elapsed < 0.1, f"Entity extraction took {elapsed}s, expected < 100ms"
    
    @pytest.mark.asyncio
    async def test_nlp_processing_throughput(self, nlp):
        """Test processing multiple messages (throughput)"""
        # Arrange
        messages = [
            "Quantos pedidos tenho?",
            "Confirme esse pedido",
            "Cancela esse pedido",
            "Feche a loja por 30 minutos",
            "Qual foi meu faturamento hoje?"
        ]
        num_iterations = 20
        start_time = time.time()
        
        # Act
        for _ in range(num_iterations):
            for message in messages:
                await nlp.understand(message)
        
        elapsed = time.time() - start_time
        total_messages = len(messages) * num_iterations
        throughput = total_messages / elapsed
        
        # Assert - Should process at least 100 messages per second
        assert throughput >= 100, f"Throughput {throughput} msg/s, expected >= 100 msg/s"
    
    @pytest.mark.asyncio
    async def test_context_aware_processing_latency(self, nlp):
        """Test context-aware processing latency (< 100ms)"""
        # Arrange
        context = {
            'last_intent': 'check_orders',
            'last_connector': 'ifood'
        }
        start_time = time.time()
        
        # Act
        await nlp.understand("E qual foi o mais caro?", context)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert elapsed < 0.1, f"Context-aware processing took {elapsed}s, expected < 100ms"
    
    @pytest.mark.asyncio
    async def test_concurrent_nlp_processing(self, nlp):
        """Test processing messages concurrently"""
        # Arrange
        messages = [
            "Quantos pedidos tenho?",
            "Confirme esse pedido",
            "Cancela esse pedido",
            "Feche a loja",
            "Qual foi meu faturamento?"
        ]
        num_concurrent = 20
        start_time = time.time()
        
        # Act
        tasks = [
            nlp.understand(messages[i % len(messages)])
            for i in range(num_concurrent)
        ]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert len(results) == num_concurrent
        assert elapsed < 1.0, f"Concurrent processing took {elapsed}s, expected < 1s"
    
    @pytest.mark.asyncio
    async def test_nlp_with_large_context(self, nlp):
        """Test NLP processing with large conversation context"""
        # Arrange
        large_context = {
            'last_intent': 'check_orders',
            'last_connector': 'ifood',
            'conversation_history': [f"message_{i}" for i in range(1000)],
            'user_preferences': {f'pref_{i}': f'value_{i}' for i in range(100)}
        }
        start_time = time.time()
        
        # Act
        result = await nlp.understand("E qual foi o mais caro?", large_context)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert result is not None
        assert elapsed < 0.2, f"Processing with large context took {elapsed}s, expected < 200ms"
    
    @pytest.mark.asyncio
    async def test_nlp_with_long_message(self, nlp):
        """Test NLP processing with long message"""
        # Arrange
        long_message = "Quantos pedidos tenho no iFood? " * 50  # Very long message
        start_time = time.time()
        
        # Act
        result = await nlp.understand(long_message)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert result is not None
        assert elapsed < 0.2, f"Processing long message took {elapsed}s, expected < 200ms"
    
    @pytest.mark.asyncio
    async def test_entity_extraction_with_many_entities(self, nlp):
        """Test entity extraction with many entities in message"""
        # Arrange
        message = "Confirme pedido #123 e #456 e #789 no iFood por 30 minutos"
        start_time = time.time()
        
        # Act
        result = await nlp.understand(message)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert len(result.classification.entities) >= 3
        assert elapsed < 0.1, f"Entity extraction took {elapsed}s, expected < 100ms"
    
    @pytest.mark.asyncio
    async def test_nlp_result_serialization_latency(self, nlp):
        """Test NLP result serialization latency (< 10ms)"""
        # Arrange
        result = await nlp.understand("Quantos pedidos tenho no iFood?")
        start_time = time.time()
        
        # Act
        data = result.to_dict()
        
        elapsed = time.time() - start_time
        
        # Assert
        assert data is not None
        assert elapsed < 0.01, f"Serialization took {elapsed}s, expected < 10ms"
    
    @pytest.mark.asyncio
    async def test_nlp_result_deserialization_latency(self, nlp):
        """Test NLP result deserialization latency (< 10ms)"""
        # Arrange
        result = await nlp.understand("Quantos pedidos tenho no iFood?")
        data = result.to_dict()
        start_time = time.time()
        
        # Act
        from app.omnichannel.nlp_models import NLPResult
        restored = NLPResult.from_dict(data)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert restored is not None
        assert elapsed < 0.01, f"Deserialization took {elapsed}s, expected < 10ms"
