"""
Unit tests for universal message processor.

Tests message processing, email extraction, context retrieval,
and UniversalMessage creation.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, strategies as st

from app.omnichannel.models import UniversalMessage, ChannelType, MessageContext
from app.omnichannel.universal_message_processor import UniversalMessageProcessor
from app.omnichannel.channel_mapping_service import ChannelMappingService


@pytest.mark.unit
class TestUniversalMessageProcessor:
    """Tests for UniversalMessageProcessor"""
    
    @pytest.fixture
    def mock_channel_mapping(self):
        """Mock channel mapping service"""
        return AsyncMock(spec=ChannelMappingService)
    
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
    async def test_process_message_success(
        self,
        processor,
        mock_channel_mapping,
        mock_session_manager,
        mock_memory_service
    ):
        """Test successful message processing"""
        # Arrange
        mock_channel_mapping.get_email_by_channel_id.return_value = "user@example.com"
        mock_session = MagicMock()
        mock_session.session_id = "session_123"
        mock_session_manager.get.return_value = mock_session
        mock_memory_service.get_context.return_value = {
            'last_intent': 'check_orders',
            'last_connector': 'ifood',
            'conversation_history': []
        }
        
        # Act
        result = await processor.process_message(
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            message_text="Quantos pedidos tenho?",
            message_id="msg_123"
        )
        
        # Assert
        assert isinstance(result, UniversalMessage)
        assert result.email == "user@example.com"
        assert result.text == "Quantos pedidos tenho?"
        assert result.channel == ChannelType.TELEGRAM
        assert result.channel_user_id == "123456"
        assert result.session_id == "session_123"
        assert result.context['last_intent'] == 'check_orders'
    
    @pytest.mark.asyncio
    async def test_process_message_email_not_found(
        self,
        processor,
        mock_channel_mapping
    ):
        """Test error when email cannot be extracted"""
        # Arrange
        mock_channel_mapping.get_email_by_channel_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot extract email"):
            await processor.process_message(
                channel=ChannelType.TELEGRAM,
                channel_user_id="unknown_id",
                message_text="Test",
                message_id="msg_123"
            )
    
    @pytest.mark.asyncio
    async def test_process_message_session_not_found(
        self,
        processor,
        mock_channel_mapping,
        mock_session_manager
    ):
        """Test error when session not found"""
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
    
    @pytest.mark.asyncio
    async def test_process_message_with_metadata(
        self,
        processor,
        mock_channel_mapping,
        mock_session_manager,
        mock_memory_service
    ):
        """Test message processing with channel-specific metadata"""
        # Arrange
        mock_channel_mapping.get_email_by_channel_id.return_value = "user@example.com"
        mock_session = MagicMock()
        mock_session.session_id = "session_123"
        mock_session_manager.get.return_value = mock_session
        mock_memory_service.get_context.return_value = {}
        
        metadata = {'reply_to': 'msg_456', 'edit_date': 1234567890}
        
        # Act
        result = await processor.process_message(
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            message_text="Test",
            message_id="msg_123",
            metadata=metadata
        )
        
        # Assert
        assert result.metadata == metadata
    
    @pytest.mark.asyncio
    async def test_update_context_with_intent(
        self,
        processor,
        mock_memory_service
    ):
        """Test updating context with new intent"""
        # Act
        await processor.update_context(
            email="user@example.com",
            intent="check_orders",
            connector="ifood"
        )
        
        # Assert
        mock_memory_service.update_context.assert_called_once()
        call_args = mock_memory_service.update_context.call_args
        assert call_args[0][0] == "user@example.com"
        assert call_args[0][1]['last_intent'] == "check_orders"
        assert call_args[0][1]['last_connector'] == "ifood"
    
    @pytest.mark.asyncio
    async def test_update_context_with_history(
        self,
        processor,
        mock_memory_service
    ):
        """Test updating context with conversation history"""
        # Act
        await processor.update_context(
            email="user@example.com",
            add_to_history="User asked about orders"
        )
        
        # Assert
        mock_memory_service.update_context.assert_called_once()
        call_args = mock_memory_service.update_context.call_args
        assert call_args[0][1]['add_to_history'] == "User asked about orders"
    
    @pytest.mark.asyncio
    async def test_retrieve_context_empty(
        self,
        processor,
        mock_memory_service
    ):
        """Test retrieving context when none exists"""
        # Arrange
        mock_memory_service.get_context.return_value = None
        
        # Act
        context = await processor._retrieve_context("user@example.com")
        
        # Assert
        assert context['last_intent'] is None
        assert context['last_connector'] is None
        assert context['conversation_history'] == []
        assert context['user_preferences'] == {}
    
    @pytest.mark.asyncio
    async def test_retrieve_context_with_data(
        self,
        processor,
        mock_memory_service
    ):
        """Test retrieving context with existing data"""
        # Arrange
        mock_memory_service.get_context.return_value = {
            'last_intent': 'check_orders',
            'last_connector': 'ifood',
            'last_order_id': '12345',
            'conversation_history': ['msg1', 'msg2'],
            'user_preferences': {'language': 'pt-BR'}
        }
        
        # Act
        context = await processor._retrieve_context("user@example.com")
        
        # Assert
        assert context['last_intent'] == 'check_orders'
        assert context['last_connector'] == 'ifood'
        assert context['last_order_id'] == '12345'
        assert len(context['conversation_history']) == 2
        assert context['user_preferences']['language'] == 'pt-BR'


@pytest.mark.unit
class TestUniversalMessage:
    """Tests for UniversalMessage model"""
    
    def test_universal_message_creation(self):
        """Test creating UniversalMessage"""
        # Arrange
        now = datetime.now()
        
        # Act
        msg = UniversalMessage(
            text="Test message",
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            message_id="msg_123",
            timestamp=now,
            email="user@example.com"
        )
        
        # Assert
        assert msg.text == "Test message"
        assert msg.channel == ChannelType.TELEGRAM
        assert msg.email == "user@example.com"
        assert msg.timestamp == now
    
    def test_universal_message_to_dict(self):
        """Test converting UniversalMessage to dict"""
        # Arrange
        now = datetime.now()
        msg = UniversalMessage(
            text="Test",
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            message_id="msg_123",
            timestamp=now,
            email="user@example.com"
        )
        
        # Act
        data = msg.to_dict()
        
        # Assert
        assert data['text'] == "Test"
        assert data['channel'] == "telegram"
        assert data['email'] == "user@example.com"
        assert isinstance(data['timestamp'], str)
    
    def test_universal_message_from_dict(self):
        """Test creating UniversalMessage from dict"""
        # Arrange
        now = datetime.now()
        data = {
            'text': 'Test',
            'channel': 'telegram',
            'channel_user_id': '123456',
            'message_id': 'msg_123',
            'timestamp': now.isoformat(),
            'email': 'user@example.com',
            'session_id': None,
            'context': {},
            'metadata': {}
        }
        
        # Act
        msg = UniversalMessage.from_dict(data)
        
        # Assert
        assert msg.text == 'Test'
        assert msg.channel == ChannelType.TELEGRAM
        assert msg.email == 'user@example.com'


@pytest.mark.unit
class TestChannelMappingService:
    """Tests for ChannelMappingService"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock channel mapping repository"""
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create service instance"""
        return ChannelMappingService(mock_repository)
    
    @pytest.mark.asyncio
    async def test_get_email_by_channel_id(self, service, mock_repository):
        """Test getting email by channel ID"""
        # Arrange
        mapping = MagicMock()
        mapping.email = "user@example.com"
        mock_repository.get_by_channel_id.return_value = mapping
        
        # Act
        email = await service.get_email_by_channel_id(
            ChannelType.TELEGRAM,
            "123456"
        )
        
        # Assert
        assert email == "user@example.com"
    
    @pytest.mark.asyncio
    async def test_get_email_by_channel_id_not_found(self, service, mock_repository):
        """Test getting email when mapping not found"""
        # Arrange
        mock_repository.get_by_channel_id.return_value = None
        
        # Act
        email = await service.get_email_by_channel_id(
            ChannelType.TELEGRAM,
            "unknown"
        )
        
        # Assert
        assert email is None
    
    @pytest.mark.asyncio
    async def test_map_channel_to_email(self, service, mock_repository):
        """Test creating channel to email mapping"""
        # Act
        await service.map_channel_to_email(
            ChannelType.TELEGRAM,
            "123456",
            "user@example.com"
        )
        
        # Assert
        mock_repository.create_or_update.assert_called_once_with(
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            email="user@example.com"
        )
    
    @pytest.mark.asyncio
    async def test_get_channels_for_email(self, service, mock_repository):
        """Test getting all channels for email"""
        # Arrange
        mapping1 = MagicMock()
        mapping1.channel = ChannelType.TELEGRAM
        mapping1.channel_user_id = "123456"
        
        mapping2 = MagicMock()
        mapping2.channel = ChannelType.WHATSAPP
        mapping2.channel_user_id = "+5511999999999"
        
        mock_repository.get_by_email.return_value = [mapping1, mapping2]
        
        # Act
        channels = await service.get_channels_for_email("user@example.com")
        
        # Assert
        assert channels['telegram'] == "123456"
        assert channels['whatsapp'] == "+5511999999999"


@pytest.mark.property
class TestUniversalMessageProperties:
    """Property-based tests for UniversalMessage"""
    
    @given(
        text=st.text(min_size=1, max_size=1000),
        channel_user_id=st.text(min_size=1, max_size=100)
    )
    def test_universal_message_preserves_data(self, text, channel_user_id):
        """Validates: UniversalMessage preserves all input data
        
        Property: All fields set during creation are preserved
        """
        # Arrange
        now = datetime.now()
        
        # Act
        msg = UniversalMessage(
            text=text,
            channel=ChannelType.TELEGRAM,
            channel_user_id=channel_user_id,
            message_id="msg_123",
            timestamp=now,
            email="user@example.com"
        )
        
        # Assert
        assert msg.text == text
        assert msg.channel_user_id == channel_user_id
        assert msg.email == "user@example.com"
    
    @given(st.sampled_from([ChannelType.TELEGRAM, ChannelType.WHATSAPP, ChannelType.WEB]))
    def test_channel_type_is_valid(self, channel):
        """Validates: Channel type is always valid
        
        Property: Channel is one of supported types
        """
        # Act
        msg = UniversalMessage(
            text="Test",
            channel=channel,
            channel_user_id="123",
            message_id="msg_123",
            timestamp=datetime.now()
        )
        
        # Assert
        assert msg.channel in [ChannelType.TELEGRAM, ChannelType.WHATSAPP, ChannelType.WEB]
    
    def test_universal_message_serialization_consistency(self):
        """Validates: Serialization and deserialization are consistent
        
        Property: msg == UniversalMessage.from_dict(msg.to_dict())
        """
        # Arrange
        now = datetime.now()
        original = UniversalMessage(
            text="Test message",
            channel=ChannelType.TELEGRAM,
            channel_user_id="123456",
            message_id="msg_123",
            timestamp=now,
            email="user@example.com",
            context={'key': 'value'}
        )
        
        # Act
        data = original.to_dict()
        restored = UniversalMessage.from_dict(data)
        
        # Assert
        assert restored.text == original.text
        assert restored.channel == original.channel
        assert restored.email == original.email
        assert restored.context == original.context
