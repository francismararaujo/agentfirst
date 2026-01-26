"""
Unit tests for response adapter service.

Tests response formatting, emoji adaptation, and channel-specific constraints.
"""

import pytest
from hypothesis import given, strategies as st

from app.omnichannel.response_adapter import ResponseAdapter
from app.omnichannel.models import ChannelType


@pytest.mark.unit
class TestResponseAdapter:
    """Tests for ResponseAdapter"""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter instance"""
        return ResponseAdapter()
    
    @pytest.mark.asyncio
    async def test_adapt_response_telegram(self, adapter):
        """Test adapting response for Telegram"""
        # Act
        result = await adapter.adapt_response(
            "Você tem 3 pedidos no iFood",
            ChannelType.TELEGRAM,
            add_emojis=True
        )
        
        # Assert
        assert "pedidos" in result.lower()
        assert len(result) <= adapter.CHANNEL_LIMITS[ChannelType.TELEGRAM]
    
    @pytest.mark.asyncio
    async def test_adapt_response_whatsapp(self, adapter):
        """Test adapting response for WhatsApp"""
        # Act
        result = await adapter.adapt_response(
            "Você tem 3 pedidos no iFood",
            ChannelType.WHATSAPP,
            add_emojis=True
        )
        
        # Assert
        assert "pedidos" in result.lower()
        assert len(result) <= adapter.CHANNEL_LIMITS[ChannelType.WHATSAPP]
    
    @pytest.mark.asyncio
    async def test_adapt_response_sms(self, adapter):
        """Test adapting response for SMS"""
        # Act
        result = await adapter.adapt_response(
            "Você tem 3 pedidos",
            ChannelType.SMS,
            add_emojis=True
        )
        
        # Assert
        assert len(result) <= adapter.CHANNEL_LIMITS[ChannelType.SMS]
        # SMS should not have emojis
        for emoji in adapter.EMOJI_MAP.values():
            assert emoji not in result
    
    @pytest.mark.asyncio
    async def test_adapt_response_email(self, adapter):
        """Test adapting response for Email"""
        # Act
        result = await adapter.adapt_response(
            "Você tem 3 pedidos",
            ChannelType.EMAIL,
            add_emojis=True
        )
        
        # Assert
        assert len(result) <= adapter.CHANNEL_LIMITS[ChannelType.EMAIL]
        # Email should not have emojis
        for emoji in adapter.EMOJI_MAP.values():
            assert emoji not in result
    
    @pytest.mark.asyncio
    async def test_add_emojis_success_message(self, adapter):
        """Test adding emoji to success message"""
        # Act
        result = adapter._add_emojis("Confirmado com sucesso")
        
        # Assert
        assert adapter.EMOJI_MAP['success'] in result
    
    @pytest.mark.asyncio
    async def test_add_emojis_error_message(self, adapter):
        """Test adding emoji to error message"""
        # Act
        result = adapter._add_emojis("Erro ao processar pedido")
        
        # Assert
        assert adapter.EMOJI_MAP['error'] in result
    
    @pytest.mark.asyncio
    async def test_add_emojis_order_message(self, adapter):
        """Test adding emoji to order message"""
        # Act
        result = adapter._add_emojis("Você tem 3 pedidos")
        
        # Assert
        assert adapter.EMOJI_MAP['order'] in result
    
    @pytest.mark.asyncio
    async def test_add_emojis_money_message(self, adapter):
        """Test adding emoji to money message"""
        # Act
        result = adapter._add_emojis("Seu faturamento foi R$ 1000")
        
        # Assert
        assert adapter.EMOJI_MAP['money'] in result
    
    @pytest.mark.asyncio
    async def test_enforce_limit_within_limit(self, adapter):
        """Test enforcing limit when text is within limit"""
        # Act
        result = adapter._enforce_limit("Short text", 100)
        
        # Assert
        assert result == "Short text"
    
    @pytest.mark.asyncio
    async def test_enforce_limit_exceeds_limit(self, adapter):
        """Test enforcing limit when text exceeds limit"""
        # Act
        result = adapter._enforce_limit("x" * 100, 50)
        
        # Assert
        assert len(result) == 50
        assert result.endswith("...")
    
    @pytest.mark.asyncio
    async def test_split_long_response_short(self, adapter):
        """Test splitting short response"""
        # Act
        result = adapter.split_long_response("Short text", ChannelType.TELEGRAM)
        
        # Assert
        assert len(result) == 1
        assert result[0] == "Short text"
    
    @pytest.mark.asyncio
    async def test_split_long_response_long(self, adapter):
        """Test splitting long response"""
        # Arrange
        # Create text that exceeds Telegram limit (4096)
        long_text = "This is a very long paragraph that will be repeated many times to exceed the character limit for Telegram. " * 50
        
        # Act
        result = adapter.split_long_response(long_text, ChannelType.TELEGRAM)
        
        # Assert
        assert len(result) > 1
        for message in result:
            assert len(message) <= adapter.CHANNEL_LIMITS[ChannelType.TELEGRAM]
    
    def test_get_channel_limit_telegram(self, adapter):
        """Test getting Telegram limit"""
        # Act
        limit = adapter.get_channel_limit(ChannelType.TELEGRAM)
        
        # Assert
        assert limit == 4096
    
    def test_get_channel_limit_sms(self, adapter):
        """Test getting SMS limit"""
        # Act
        limit = adapter.get_channel_limit(ChannelType.SMS)
        
        # Assert
        assert limit == 160
    
    def test_supports_emojis_telegram(self, adapter):
        """Test emoji support for Telegram"""
        # Act
        result = adapter.supports_emojis(ChannelType.TELEGRAM)
        
        # Assert
        assert result is True
    
    def test_supports_emojis_sms(self, adapter):
        """Test emoji support for SMS"""
        # Act
        result = adapter.supports_emojis(ChannelType.SMS)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_format_telegram(self, adapter):
        """Test Telegram formatting"""
        # Act
        result = adapter._format_telegram("**bold text**")
        
        # Assert
        assert "*bold text*" in result
    
    @pytest.mark.asyncio
    async def test_format_whatsapp(self, adapter):
        """Test WhatsApp formatting"""
        # Act
        result = adapter._format_whatsapp("**bold text**")
        
        # Assert
        assert "*bold text*" in result
    
    @pytest.mark.asyncio
    async def test_format_sms_removes_emojis(self, adapter):
        """Test SMS formatting removes emojis"""
        # Act
        result = adapter._format_sms("✅ Confirmado")
        
        # Assert
        assert "✅" not in result
        assert "Confirmado" in result
    
    @pytest.mark.asyncio
    async def test_format_email_removes_emojis(self, adapter):
        """Test Email formatting removes emojis"""
        # Act
        result = adapter._format_email("✅ Confirmado")
        
        # Assert
        assert "✅" not in result
        assert "Confirmado" in result


@pytest.mark.property
class TestResponseAdapterProperties:
    """Property-based tests for ResponseAdapter"""
    
    @given(st.text(min_size=1, max_size=100))
    def test_adapted_response_never_exceeds_limit(self, text):
        """Validates: Adapted response never exceeds channel limit
        
        Property: len(adapt_response(text, channel)) <= CHANNEL_LIMITS[channel]
        """
        # Arrange
        adapter = ResponseAdapter()
        
        # Act
        import asyncio
        result = asyncio.run(adapter.adapt_response(text, ChannelType.TELEGRAM))
        
        # Assert
        assert len(result) <= adapter.CHANNEL_LIMITS[ChannelType.TELEGRAM]
    
    @given(st.sampled_from([ChannelType.TELEGRAM, ChannelType.WHATSAPP, ChannelType.SMS]))
    def test_channel_limit_is_positive(self, channel):
        """Validates: Channel limit is always positive
        
        Property: get_channel_limit(channel) > 0
        """
        # Arrange
        adapter = ResponseAdapter()
        
        # Act
        limit = adapter.get_channel_limit(channel)
        
        # Assert
        assert limit > 0
    
    @given(st.text(min_size=1, max_size=100))
    def test_split_response_respects_limit(self, text):
        """Validates: Split response respects channel limit
        
        Property: all(len(msg) <= limit for msg in split_long_response(text, channel))
        """
        # Arrange
        adapter = ResponseAdapter()
        channel = ChannelType.TELEGRAM
        limit = adapter.get_channel_limit(channel)
        
        # Act
        messages = adapter.split_long_response(text, channel)
        
        # Assert
        for message in messages:
            assert len(message) <= limit
