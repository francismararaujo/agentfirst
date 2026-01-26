"""
Integration tests for Memory Service

Tests complete workflows for context management.
"""

import pytest
from unittest.mock import AsyncMock

from app.core.memory import MemoryService


@pytest.mark.integration
class TestMemoryIntegration:
    """Integration tests for MemoryService"""
    
    @pytest.fixture
    def mock_dynamodb(self):
        """Mock DynamoDB client"""
        return AsyncMock()
    
    @pytest.fixture
    def memory_service(self, mock_dynamodb):
        """Create MemoryService instance"""
        return MemoryService(mock_dynamodb, table_name='memory')
    
    @pytest.mark.asyncio
    async def test_complete_context_workflow(self, memory_service, mock_dynamodb):
        """Test complete context management workflow"""
        # Arrange
        email = "merchant@example.com"
        
        # Mock initial query (empty)
        mock_dynamodb.query.return_value = {'Items': []}
        
        # Act 1: Get initial context
        context = await memory_service.get_context(email)
        
        # Assert 1
        assert context['email'] == email
        assert context['last_intent'] is None
        
        # Act 2: Update context
        await memory_service.update_context(email, {
            'last_intent': 'check_orders',
            'last_domain': 'retail'
        })
        
        # Assert 2
        assert mock_dynamodb.put_item.call_count == 2
    
    @pytest.mark.asyncio
    async def test_history_management_workflow(self, memory_service, mock_dynamodb):
        """Test history management workflow"""
        # Arrange
        email = "merchant@example.com"
        
        mock_dynamodb.query.return_value = {'Items': []}
        
        # Act 1: Add first message
        await memory_service.add_to_history(
            email,
            "Quantos pedidos tenho?",
            "Você tem 3 pedidos",
            "retail"
        )
        
        # Assert 1
        assert mock_dynamodb.put_item.called
        
        # Act 2: Add second message
        await memory_service.add_to_history(
            email,
            "Qual foi o mais caro?",
            "O mais caro foi R$ 125,50",
            "retail"
        )
        
        # Assert 2
        assert mock_dynamodb.put_item.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_preference_management_workflow(self, memory_service, mock_dynamodb):
        """Test preference management workflow"""
        # Arrange
        email = "merchant@example.com"
        
        mock_dynamodb.query.return_value = {'Items': []}
        
        # Act 1: Set preference
        await memory_service.set_preference(email, "language", "pt-BR")
        
        # Assert 1
        assert mock_dynamodb.put_item.called
        
        # Act 2: Get preference
        mock_dynamodb.query.return_value = {
            'Items': [
                {
                    'email': {'S': email},
                    'domain': {'S': 'global'},
                    'key': {'S': 'preferences'},
                    'value': {'S': '{"language": "pt-BR"}'},
                    'timestamp': {'S': '2025-01-25T10:00:00'}
                }
            ]
        }
        
        preference = await memory_service.get_preference(email, "language")
        
        # Assert 2
        assert preference == "pt-BR"
    
    @pytest.mark.asyncio
    async def test_domain_context_workflow(self, memory_service, mock_dynamodb):
        """Test domain-specific context workflow"""
        # Arrange
        email = "merchant@example.com"
        domain = "retail"
        
        mock_dynamodb.query.return_value = {
            'Items': [
                {
                    'email': {'S': email},
                    'domain': {'S': domain},
                    'key': {'S': 'last_orders'},
                    'value': {'S': '[{"id": "123", "value": 50.0}]'},
                    'timestamp': {'S': '2025-01-25T10:00:00'}
                }
            ]
        }
        
        # Act
        context = await memory_service.get_domain_context(email, domain)
        
        # Assert
        assert 'last_orders' in context
        assert len(context['last_orders']) == 1
    
    @pytest.mark.asyncio
    async def test_context_persistence_across_calls(self, memory_service, mock_dynamodb):
        """Test context persistence across multiple calls"""
        # Arrange
        email = "merchant@example.com"
        
        # First call - empty
        mock_dynamodb.query.return_value = {'Items': []}
        context1 = await memory_service.get_context(email)
        
        # Update context
        await memory_service.update_context(email, {
            'last_intent': 'check_orders'
        })
        
        # Second call - with data
        mock_dynamodb.query.return_value = {
            'Items': [
                {
                    'email': {'S': email},
                    'domain': {'S': 'global'},
                    'key': {'S': 'last_intent'},
                    'value': {'S': 'check_orders'},
                    'timestamp': {'S': '2025-01-25T10:00:00'}
                }
            ]
        }
        context2 = await memory_service.get_context(email)
        
        # Assert
        assert context1['last_intent'] is None
        assert context2['last_intent'] == 'check_orders'
    
    @pytest.mark.asyncio
    async def test_clear_context_workflow(self, memory_service, mock_dynamodb):
        """Test clearing context workflow"""
        # Arrange
        email = "merchant@example.com"
        
        mock_dynamodb.query.return_value = {
            'Items': [
                {
                    'email': {'S': email},
                    'domain': {'S': 'global'},
                    'key': {'S': 'last_intent'},
                    'value': {'S': 'check_orders'}
                },
                {
                    'email': {'S': email},
                    'domain': {'S': 'retail'},
                    'key': {'S': 'last_orders'},
                    'value': {'S': '[]'}
                }
            ]
        }
        
        # Act
        await memory_service.clear_context(email)
        
        # Assert
        assert mock_dynamodb.delete_item.call_count == 2
    
    @pytest.mark.asyncio
    async def test_multi_domain_context(self, memory_service, mock_dynamodb):
        """Test managing context for multiple domains"""
        # Arrange
        email = "merchant@example.com"
        
        mock_dynamodb.query.return_value = {
            'Items': [
                {
                    'email': {'S': email},
                    'domain': {'S': 'retail'},
                    'key': {'S': 'last_orders'},
                    'value': {'S': '[]'},
                    'timestamp': {'S': '2025-01-25T10:00:00'}
                },
                {
                    'email': {'S': email},
                    'domain': {'S': 'tax'},
                    'key': {'S': 'last_taxes'},
                    'value': {'S': '[]'},
                    'timestamp': {'S': '2025-01-25T10:00:00'}
                }
            ]
        }
        
        # Act
        context = await memory_service.get_context(email)
        
        # Assert
        assert 'retail' in context['domains']
        assert 'tax' in context['domains']
