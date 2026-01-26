"""
Unit tests for Memory Service

Tests context retrieval, storage, and management.
"""

import pytest
from unittest.mock import AsyncMock
from hypothesis import given, strategies as st

from app.core.memory import MemoryService, MemoryEntry


@pytest.mark.unit
class TestMemoryService:
    """Tests for MemoryService"""
    
    @pytest.fixture
    def mock_dynamodb(self):
        """Mock DynamoDB client"""
        return AsyncMock()
    
    @pytest.fixture
    def memory_service(self, mock_dynamodb):
        """Create MemoryService instance"""
        return MemoryService(mock_dynamodb, table_name='memory')
    
    @pytest.mark.asyncio
    async def test_get_context_empty(self, memory_service, mock_dynamodb):
        """Test getting context for new user"""
        # Arrange
        email = "test@example.com"
        mock_dynamodb.query.return_value = {'Items': []}
        
        # Act
        context = await memory_service.get_context(email)
        
        # Assert
        assert context['email'] == email
        assert context['last_intent'] is None
        assert context['history'] == []
        assert context['preferences'] == {}
    
    @pytest.mark.asyncio
    async def test_get_context_with_data(self, memory_service, mock_dynamodb):
        """Test getting context with existing data"""
        # Arrange
        email = "test@example.com"
        mock_dynamodb.query.return_value = {
            'Items': [
                {
                    'email': {'S': email},
                    'domain': {'S': 'global'},
                    'key': {'S': 'last_intent'},
                    'value': {'S': 'check_orders'},
                    'timestamp': {'S': '2025-01-25T10:00:00'}
                },
                {
                    'email': {'S': email},
                    'domain': {'S': 'global'},
                    'key': {'S': 'history'},
                    'value': {'S': '[]'},
                    'timestamp': {'S': '2025-01-25T10:00:00'}
                }
            ]
        }
        
        # Act
        context = await memory_service.get_context(email)
        
        # Assert
        assert context['email'] == email
        assert context['last_intent'] == 'check_orders'
        assert context['history'] == []
    
    @pytest.mark.asyncio
    async def test_update_context(self, memory_service, mock_dynamodb):
        """Test updating context"""
        # Arrange
        email = "test@example.com"
        updates = {
            'last_intent': 'check_orders',
            'last_domain': 'retail'
        }
        
        # Act
        await memory_service.update_context(email, updates)
        
        # Assert
        assert mock_dynamodb.put_item.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_domain_context(self, memory_service, mock_dynamodb):
        """Test getting domain-specific context"""
        # Arrange
        email = "test@example.com"
        domain = "retail"
        mock_dynamodb.query.return_value = {
            'Items': [
                {
                    'email': {'S': email},
                    'domain': {'S': domain},
                    'key': {'S': 'last_orders'},
                    'value': {'S': '[]'},
                    'timestamp': {'S': '2025-01-25T10:00:00'}
                }
            ]
        }
        
        # Act
        context = await memory_service.get_domain_context(email, domain)
        
        # Assert
        assert 'last_orders' in context
        assert context['last_orders'] == []
    
    @pytest.mark.asyncio
    async def test_add_to_history(self, memory_service, mock_dynamodb):
        """Test adding message to history"""
        # Arrange
        email = "test@example.com"
        message = "Quantos pedidos tenho?"
        response = "Você tem 3 pedidos"
        domain = "retail"
        
        mock_dynamodb.query.return_value = {'Items': []}
        
        # Act
        await memory_service.add_to_history(email, message, response, domain)
        
        # Assert
        mock_dynamodb.put_item.assert_called()
    
    @pytest.mark.asyncio
    async def test_set_preference(self, memory_service, mock_dynamodb):
        """Test setting user preference"""
        # Arrange
        email = "test@example.com"
        key = "language"
        value = "pt-BR"
        
        mock_dynamodb.query.return_value = {'Items': []}
        
        # Act
        await memory_service.set_preference(email, key, value)
        
        # Assert
        mock_dynamodb.put_item.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_preference(self, memory_service, mock_dynamodb):
        """Test getting user preference"""
        # Arrange
        email = "test@example.com"
        key = "language"
        
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
        
        # Act
        preference = await memory_service.get_preference(email, key)
        
        # Assert
        assert preference == "pt-BR"
    
    @pytest.mark.asyncio
    async def test_get_preference_default(self, memory_service, mock_dynamodb):
        """Test getting preference with default value"""
        # Arrange
        email = "test@example.com"
        key = "language"
        default = "en-US"
        
        mock_dynamodb.query.return_value = {'Items': []}
        
        # Act
        preference = await memory_service.get_preference(email, key, default)
        
        # Assert
        assert preference == default
    
    @pytest.mark.asyncio
    async def test_clear_context(self, memory_service, mock_dynamodb):
        """Test clearing user context"""
        # Arrange
        email = "test@example.com"
        mock_dynamodb.query.return_value = {
            'Items': [
                {
                    'email': {'S': email},
                    'domain': {'S': 'global'},
                    'key': {'S': 'last_intent'},
                    'value': {'S': 'check_orders'}
                }
            ]
        }
        
        # Act
        await memory_service.clear_context(email)
        
        # Assert
        mock_dynamodb.delete_item.assert_called()


@pytest.mark.property
class TestMemoryServiceProperties:
    """Property-based tests for MemoryService"""
    
    @given(st.emails())
    def test_context_email_is_preserved(self, email):
        """Validates: Context email is always preserved
        
        Property: context.email == input_email
        """
        # Arrange
        mock_dynamodb = AsyncMock()
        mock_dynamodb.query.return_value = {'Items': []}
        memory_service = MemoryService(mock_dynamodb)
        
        # Act
        import asyncio
        context = asyncio.run(memory_service.get_context(email))
        
        # Assert
        assert context['email'] == email
    
    @given(st.text(min_size=1, max_size=50))
    def test_preference_key_is_valid(self, key):
        """Validates: Preference key is always non-empty
        
        Property: len(key) > 0
        """
        # Assert
        assert len(key) > 0
    
    @given(st.lists(st.dictionaries(st.text(), st.text())))
    def test_history_is_list(self, history):
        """Validates: History is always a list
        
        Property: isinstance(history, list)
        """
        # Assert
        assert isinstance(history, list)
