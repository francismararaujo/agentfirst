"""
Integration tests for Brain (Orquestrador Central)

Tests complete workflows for intent classification, context management, and agent routing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.brain import Brain, Intent, Context
from app.omnichannel.models import ChannelType


@pytest.mark.integration
class TestBrainIntegration:
    """Integration tests for Brain"""
    
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
    
    @pytest.mark.asyncio
    async def test_complete_order_check_workflow(self, brain, mock_bedrock, mock_memory, mock_event_bus, mock_auditor):
        """Test complete workflow for checking orders"""
        # Arrange
        message = "Quantos pedidos tenho no iFood?"
        context = Context(
            email="merchant@example.com",
            channel=ChannelType.TELEGRAM,
            session_id="session_123"
        )
        
        # Mock agent
        mock_agent = AsyncMock()
        mock_agent.execute.return_value = {
            "orders": [
                {"id": "12345", "value": 89.90, "status": "confirmed"},
                {"id": "12346", "value": 125.50, "status": "pending"},
                {"id": "12347", "value": 67.30, "status": "ready"}
            ]
        }
        brain.register_agent("retail", mock_agent)
        
        # Mock Bedrock responses
        mock_bedrock.invoke_model.side_effect = [
            # Classification
            {
                'content': [
                    {
                        'text': '{"domain": "retail", "action": "check_orders", "connector": "ifood", "confidence": 0.95, "entities": {}}'
                    }
                ]
            },
            # Formatting
            {
                'content': [
                    {
                        'text': 'Você tem 3 pedidos no iFood:\n1️⃣ Pedido #12345 - R$ 89,90 (confirmado)\n2️⃣ Pedido #12346 - R$ 125,50 (pendente)\n3️⃣ Pedido #12347 - R$ 67,30 (pronto)'
                    }
                ]
            }
        ]
        
        mock_memory.get_context.return_value = {}
        
        # Act
        response = await brain.process(message, context)
        
        # Assert
        assert "3 pedidos" in response or "pedidos" in response.lower()
        mock_agent.execute.assert_called_once()
        mock_auditor.log_transaction.assert_called()
        mock_event_bus.publish.assert_called()
    
    @pytest.mark.asyncio
    async def test_complete_order_confirmation_workflow(self, brain, mock_bedrock, mock_memory, mock_event_bus, mock_auditor):
        """Test complete workflow for confirming order"""
        # Arrange
        message = "Confirme o pedido 12345"
        context = Context(
            email="merchant@example.com",
            channel=ChannelType.TELEGRAM,
            session_id="session_123"
        )
        
        # Mock agent
        mock_agent = AsyncMock()
        mock_agent.execute.return_value = {
            "order_id": "12345",
            "status": "confirmed",
            "message": "Pedido confirmado com sucesso"
        }
        brain.register_agent("retail", mock_agent)
        
        # Mock Bedrock responses
        mock_bedrock.invoke_model.side_effect = [
            # Classification
            {
                'content': [
                    {
                        'text': '{"domain": "retail", "action": "confirm_order", "connector": "ifood", "confidence": 0.95, "entities": {"order_id": "12345"}}'
                    }
                ]
            },
            # Formatting
            {
                'content': [
                    {
                        'text': '✅ Pedido #12345 confirmado com sucesso!'
                    }
                ]
            }
        ]
        
        mock_memory.get_context.return_value = {}
        
        # Act
        response = await brain.process(message, context)
        
        # Assert
        assert "confirmado" in response.lower()
        mock_agent.execute.assert_called_once()
        mock_auditor.log_transaction.assert_called()
        mock_event_bus.publish.assert_called()
    
    @pytest.mark.asyncio
    async def test_context_preservation_across_messages(self, brain, mock_bedrock, mock_memory, mock_event_bus, mock_auditor):
        """Test context preservation across multiple messages"""
        # Arrange
        context = Context(
            email="merchant@example.com",
            channel=ChannelType.TELEGRAM,
            session_id="session_123"
        )
        
        # Mock agent
        mock_agent = AsyncMock()
        mock_agent.execute.return_value = {"result": "success"}
        brain.register_agent("retail", mock_agent)
        
        # Mock memory with context
        mock_memory.get_context.return_value = {
            'last_intent': 'check_orders',
            'last_domain': 'retail',
            'last_connector': 'ifood',
            'history': [
                {'message': 'Quantos pedidos tenho?', 'response': 'Você tem 3 pedidos'}
            ]
        }
        
        # Mock Bedrock responses
        mock_bedrock.invoke_model.side_effect = [
            # Classification
            {
                'content': [
                    {
                        'text': '{"domain": "retail", "action": "check_orders", "connector": "ifood", "confidence": 0.95, "entities": {}}'
                    }
                ]
            },
            # Formatting
            {
                'content': [
                    {
                        'text': 'Você tem 3 pedidos'
                    }
                ]
            }
        ]
        
        # Act
        response = await brain.process("Quantos pedidos tenho?", context)
        
        # Assert
        assert response is not None
        mock_memory.get_context.assert_called_with("merchant@example.com")
        mock_memory.update_context.assert_called()
    
    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(self, brain, mock_bedrock, mock_memory, mock_auditor):
        """Test error handling in workflow"""
        # Arrange
        message = "Quantos pedidos tenho?"
        context = Context(
            email="merchant@example.com",
            channel=ChannelType.TELEGRAM,
            session_id="session_123"
        )
        
        # Mock agent to raise error
        mock_agent = AsyncMock()
        mock_agent.execute.side_effect = Exception("API error")
        brain.register_agent("retail", mock_agent)
        
        # Mock Bedrock response
        mock_bedrock.invoke_model.return_value = {
            'content': [
                {
                    'text': '{"domain": "retail", "action": "check_orders", "confidence": 0.95, "entities": {}}'
                }
            ]
        }
        
        mock_memory.get_context.return_value = {}
        
        # Act
        response = await brain.process(message, context)
        
        # Assert
        assert "erro" in response.lower() or "error" in response.lower()
        mock_auditor.log_transaction.assert_called()
    
    @pytest.mark.asyncio
    async def test_event_handling_order_received(self, brain, mock_bedrock, mock_memory, mock_event_bus, mock_auditor):
        """Test handling order_received event"""
        # Arrange
        event_data = {
            'email': 'merchant@example.com',
            'order_id': '12348',
            'value': 95.00,
            'session_id': 'session_123'
        }
        
        # Mock agent
        mock_agent = AsyncMock()
        mock_agent.execute.return_value = {"status": "received"}
        brain.register_agent("retail", mock_agent)
        
        # Mock Bedrock responses
        mock_bedrock.invoke_model.side_effect = [
            # Classification
            {
                'content': [
                    {
                        'text': '{"domain": "retail", "action": "new_order", "confidence": 0.95, "entities": {}}'
                    }
                ]
            },
            # Formatting
            {
                'content': [
                    {
                        'text': 'Novo pedido recebido! 📦 Pedido #12348 - R$ 95,00'
                    }
                ]
            }
        ]
        
        mock_memory.get_context.return_value = {}
        
        # Act
        await brain.handle_event("order_received", event_data)
        
        # Assert
        mock_agent.execute.assert_called()
        mock_auditor.log_transaction.assert_called()
    
    @pytest.mark.asyncio
    async def test_multi_domain_routing(self, brain, mock_bedrock, mock_memory, mock_event_bus, mock_auditor):
        """Test routing to different domains"""
        # Arrange
        context = Context(
            email="user@example.com",
            channel=ChannelType.TELEGRAM,
            session_id="session_123"
        )
        
        # Mock agents for different domains
        retail_agent = AsyncMock()
        retail_agent.execute.return_value = {"orders": []}
        brain.register_agent("retail", retail_agent)
        
        tax_agent = AsyncMock()
        tax_agent.execute.return_value = {"taxes": []}
        brain.register_agent("tax", tax_agent)
        
        # Mock Bedrock response for tax domain
        mock_bedrock.invoke_model.side_effect = [
            # Classification
            {
                'content': [
                    {
                        'text': '{"domain": "tax", "action": "check_taxes", "confidence": 0.95, "entities": {}}'
                    }
                ]
            },
            # Formatting
            {
                'content': [
                    {
                        'text': 'Seus impostos estão em dia'
                    }
                ]
            }
        ]
        
        mock_memory.get_context.return_value = {}
        
        # Act
        response = await brain.process("Qual é minha situação fiscal?", context)
        
        # Assert
        assert response is not None
        tax_agent.execute.assert_called_once()
        retail_agent.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_context_update_after_processing(self, brain, mock_bedrock, mock_memory, mock_event_bus, mock_auditor):
        """Test that context is updated after processing"""
        # Arrange
        message = "Quantos pedidos tenho?"
        context = Context(
            email="merchant@example.com",
            channel=ChannelType.TELEGRAM,
            session_id="session_123"
        )
        
        # Mock agent
        mock_agent = AsyncMock()
        mock_agent.execute.return_value = {"orders": []}
        brain.register_agent("retail", mock_agent)
        
        # Mock Bedrock responses
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
        
        # Act
        await brain.process(message, context)
        
        # Assert
        mock_memory.update_context.assert_called_once()
        call_args = mock_memory.update_context.call_args
        assert call_args[0][0] == "merchant@example.com"
        assert 'last_intent' in call_args[0][1]
        assert 'last_domain' in call_args[0][1]
