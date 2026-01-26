"""
Integration tests for universal message processing.

Tests complete workflows including message processing, context retrieval,
and multi-channel scenarios.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.omnichannel.models import UniversalMessage, ChannelType
from app.omnichannel.universal_message_processor import UniversalMessageProcessor
from app.omnichannel.channel_mapping_service import ChannelMappingService


@pytest.mark.integration
class TestUniversalMessageIntegration:
    """Integration tests for message processing"""
    
    @pytest.fixture
    def mock_channel_mapping(self):
        """Mock channel mapping service"""
        service = AsyncMock(spec=ChannelMappingService)
        service.get_email_by_channel_id = AsyncMock()
        service.map_channel_to_email = AsyncMock()
        service.get_channels_for_email = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager"""
        manager = AsyncMock()
        manager.get = AsyncMock()
        return manager
    
    @pytest.fixture
    def mock_memory_service(self):
        """Mock memory service"""
        service = AsyncMock()
        service.get_context = AsyncMock()
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
    async def test_complete_message_processing_workflow(
        self,
        processor,
        mock_channel_mapping,
        mock_session_manager,
        mock_memory_service
    ):
        """Test complete workflow: receive → extract email → get context → create message"""
        # Arrange
        mock_channel_mapping.get_email_by_channel_id.return_value = "user@example.com"
        mock_session = MagicMock()
        mock_session.session_id = "session_123"
        mock_session_manager.get.return_value = mock_session
        mock_memory_service.get_context.return_value = {
            'last_intent': 'check_orders',
            'last_connector': 'ifood',
            'conversation_history': ['msg1'],
            'user_preferences': {'language': 'pt-BR'}
        }
        
        # Act
        result = await processor.process_message(
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            message_text="Quantos pedidos tenho?",
            message_id="msg_123"
        )
        
        # Assert
        assert result.email == "user@example.com"
        assert result.session_id == "session_123"
        assert result.context['last_intent'] == 'check_orders'
        assert result.context['user_preferences']['language'] == 'pt-BR'
        
        # Verify all services were called
        mock_channel_mapping.get_email_by_channel_id.assert_called_once()
        mock_session_manager.get.assert_called_once_with("user@example.com")
        mock_memory_service.get_context.assert_called_once_with("user@example.com")
    
    @pytest.mark.asyncio
    async def test_context_preservation_across_messages(
        self,
        processor,
        mock_channel_mapping,
        mock_session_manager,
        mock_memory_service
    ):
        """Test that context is preserved across multiple messages"""
        # Arrange
        mock_channel_mapping.get_email_by_channel_id.return_value = "user@example.com"
        mock_session = MagicMock()
        mock_session.session_id = "session_123"
        mock_session_manager.get.return_value = mock_session
        
        # First message context
        mock_memory_service.get_context.return_value = {
            'last_intent': None,
            'last_connector': None,
            'conversation_history': [],
            'user_preferences': {}
        }
        
        # Act - First message
        msg1 = await processor.process_message(
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            message_text="Quantos pedidos tenho?",
            message_id="msg_1"
        )
        
        # Update context after first message
        await processor.update_context(
            email="user@example.com",
            intent="check_orders",
            connector="ifood"
        )
        
        # Second message context (updated)
        mock_memory_service.get_context.return_value = {
            'last_intent': 'check_orders',
            'last_connector': 'ifood',
            'conversation_history': ['msg_1'],
            'user_preferences': {}
        }
        
        # Act - Second message (follow-up)
        msg2 = await processor.process_message(
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            message_text="Qual foi o mais caro?",
            message_id="msg_2"
        )
        
        # Assert
        assert msg2.context['last_intent'] == 'check_orders'
        assert msg2.context['last_connector'] == 'ifood'
    
    @pytest.mark.asyncio
    async def test_multi_channel_same_user(
        self,
        processor,
        mock_channel_mapping,
        mock_session_manager,
        mock_memory_service
    ):
        """Test same user on different channels"""
        # Arrange
        mock_channel_mapping.get_email_by_channel_id.return_value = "user@example.com"
        mock_session = MagicMock()
        mock_session.session_id = "session_123"
        mock_session_manager.get.return_value = mock_session
        mock_memory_service.get_context.return_value = {
            'last_intent': 'check_orders',
            'last_connector': 'ifood',
            'conversation_history': [],
            'user_preferences': {}
        }
        
        # Act - Message on Telegram
        msg_telegram = await processor.process_message(
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            message_text="Quantos pedidos?",
            message_id="msg_1"
        )
        
        # Act - Same user on WhatsApp
        msg_whatsapp = await processor.process_message(
            channel=ChannelType.WHATSAPP,
            channel_user_id="+5511999999999",
            message_text="Qual foi o mais caro?",
            message_id="msg_2"
        )
        
        # Assert - Same email, different channels
        assert msg_telegram.email == msg_whatsapp.email
        assert msg_telegram.channel != msg_whatsapp.channel
        assert msg_telegram.channel_user_id != msg_whatsapp.channel_user_id
        
        # Both should have same context
        assert msg_telegram.context['last_intent'] == msg_whatsapp.context['last_intent']
    
    @pytest.mark.asyncio
    async def test_message_with_channel_metadata(
        self,
        processor,
        mock_channel_mapping,
        mock_session_manager,
        mock_memory_service
    ):
        """Test processing message with channel-specific metadata"""
        # Arrange
        mock_channel_mapping.get_email_by_channel_id.return_value = "user@example.com"
        mock_session = MagicMock()
        mock_session.session_id = "session_123"
        mock_session_manager.get.return_value = mock_session
        mock_memory_service.get_context.return_value = {}
        
        telegram_metadata = {
            'reply_to_message_id': 456,
            'edit_date': 1234567890,
            'forward_from': 'channel_name'
        }
        
        # Act
        result = await processor.process_message(
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            message_text="Test",
            message_id="msg_123",
            metadata=telegram_metadata
        )
        
        # Assert
        assert result.metadata == telegram_metadata
        assert result.metadata['reply_to_message_id'] == 456
    
    @pytest.mark.asyncio
    async def test_context_update_workflow(
        self,
        processor,
        mock_memory_service
    ):
        """Test updating context after message processing"""
        # Act
        await processor.update_context(
            email="user@example.com",
            intent="check_orders",
            connector="ifood",
            order_id="12345",
            add_to_history="User asked about orders"
        )
        
        # Assert
        mock_memory_service.update_context.assert_called_once()
        call_args = mock_memory_service.update_context.call_args
        updates = call_args[0][1]
        
        assert updates['last_intent'] == "check_orders"
        assert updates['last_connector'] == "ifood"
        assert updates['last_order_id'] == "12345"
        assert updates['add_to_history'] == "User asked about orders"
    
    @pytest.mark.asyncio
    async def test_error_handling_missing_email(
        self,
        processor,
        mock_channel_mapping
    ):
        """Test error handling when email cannot be extracted"""
        # Arrange
        mock_channel_mapping.get_email_by_channel_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot extract email"):
            await processor.process_message(
                channel=ChannelType.TELEGRAM,
                channel_user_id="unknown",
                message_text="Test",
                message_id="msg_123"
            )
    
    @pytest.mark.asyncio
    async def test_error_handling_missing_session(
        self,
        processor,
        mock_channel_mapping,
        mock_session_manager
    ):
        """Test error handling when session not found"""
        # Arrange
        mock_channel_mapping.get_email_by_channel_id.return_value = "user@example.com"
        mock_session_manager.get.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="No session found"):
            await processor.process_message(
                channel=ChannelType.TELEGRAM,
                channel_user_id="123456",
                message_text="Test",
                message_id="msg_123"
            )


@pytest.mark.integration
class TestChannelMappingIntegration:
    """Integration tests for channel mapping"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock repository"""
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create service"""
        return ChannelMappingService(mock_repository)
    
    @pytest.mark.asyncio
    async def test_channel_mapping_workflow(self, service, mock_repository):
        """Test complete channel mapping workflow"""
        # Arrange
        mapping = MagicMock()
        mapping.email = "user@example.com"
        mock_repository.get_by_channel_id.return_value = mapping
        
        # Act - Get email by channel ID
        email = await service.get_email_by_channel_id(
            ChannelType.TELEGRAM,
            "123456"
        )
        
        # Assert
        assert email == "user@example.com"
        
        # Act - Create new mapping
        await service.map_channel_to_email(
            ChannelType.WHATSAPP,
            "+5511999999999",
            "user@example.com"
        )
        
        # Assert
        mock_repository.create_or_update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_channels_for_user(self, service, mock_repository):
        """Test retrieving all channels for a user"""
        # Arrange
        mapping1 = MagicMock()
        mapping1.channel = ChannelType.TELEGRAM
        mapping1.channel_user_id = "123456"
        
        mapping2 = MagicMock()
        mapping2.channel = ChannelType.WHATSAPP
        mapping2.channel_user_id = "+5511999999999"
        
        mapping3 = MagicMock()
        mapping3.channel = ChannelType.WEB
        mapping3.channel_user_id = "web_user_123"
        
        mock_repository.get_by_email.return_value = [mapping1, mapping2, mapping3]
        
        # Act
        channels = await service.get_channels_for_email("user@example.com")
        
        # Assert
        assert len(channels) == 3
        assert channels['telegram'] == "123456"
        assert channels['whatsapp'] == "+5511999999999"
        assert channels['web'] == "web_user_123"
