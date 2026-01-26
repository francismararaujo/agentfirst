"""
Integration tests for response adapter service.

Tests complete workflows for response adaptation across channels.
"""

import pytest

from app.omnichannel.response_adapter import ResponseAdapter
from app.omnichannel.models import ChannelType


@pytest.mark.integration
class TestResponseAdapterIntegration:
    """Integration tests for ResponseAdapter"""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter instance"""
        return ResponseAdapter()
    
    @pytest.mark.asyncio
    async def test_complete_telegram_workflow(self, adapter):
        """Test complete Telegram response workflow"""
        # Arrange
        original_text = "Você tem 3 pedidos no iFood"
        
        # Act
        adapted = await adapter.adapt_response(
            original_text,
            ChannelType.TELEGRAM,
            add_emojis=True
        )
        
        # Assert
        assert len(adapted) <= adapter.CHANNEL_LIMITS[ChannelType.TELEGRAM]
        assert "pedidos" in adapted.lower()
        assert adapter.EMOJI_MAP['order'] in adapted
    
    @pytest.mark.asyncio
    async def test_complete_whatsapp_workflow(self, adapter):
        """Test complete WhatsApp response workflow"""
        # Arrange
        original_text = "Seu faturamento foi R$ 2.847,50"
        
        # Act
        adapted = await adapter.adapt_response(
            original_text,
            ChannelType.WHATSAPP,
            add_emojis=True
        )
        
        # Assert
        assert len(adapted) <= adapter.CHANNEL_LIMITS[ChannelType.WHATSAPP]
        assert "faturamento" in adapted.lower()
        assert adapter.EMOJI_MAP['money'] in adapted
    
    @pytest.mark.asyncio
    async def test_complete_sms_workflow(self, adapter):
        """Test complete SMS response workflow"""
        # Arrange
        original_text = "✅ Pedido confirmado com sucesso"
        
        # Act
        adapted = await adapter.adapt_response(
            original_text,
            ChannelType.SMS,
            add_emojis=True
        )
        
        # Assert
        assert len(adapted) <= adapter.CHANNEL_LIMITS[ChannelType.SMS]
        # SMS should not have emojis
        for emoji in adapter.EMOJI_MAP.values():
            assert emoji not in adapted
    
    @pytest.mark.asyncio
    async def test_complete_email_workflow(self, adapter):
        """Test complete Email response workflow"""
        # Arrange
        original_text = "📦 Você tem 3 pedidos no iFood"
        
        # Act
        adapted = await adapter.adapt_response(
            original_text,
            ChannelType.EMAIL,
            add_emojis=True
        )
        
        # Assert
        assert len(adapted) <= adapter.CHANNEL_LIMITS[ChannelType.EMAIL]
        # Email should not have emojis
        for emoji in adapter.EMOJI_MAP.values():
            assert emoji not in adapted
    
    @pytest.mark.asyncio
    async def test_long_response_split_telegram(self, adapter):
        """Test splitting long response for Telegram"""
        # Arrange
        # Create text that exceeds Telegram limit (4096)
        long_text = "Você tem os seguintes pedidos:\n\n" + (
            "Pedido #1 - R$ 50,00 com descrição longa do produto\n\n"
        ) * 200
        
        # Act
        messages = adapter.split_long_response(long_text, ChannelType.TELEGRAM)
        
        # Assert
        assert len(messages) > 1
        for message in messages:
            assert len(message) <= adapter.CHANNEL_LIMITS[ChannelType.TELEGRAM]
    
    @pytest.mark.asyncio
    async def test_long_response_split_sms(self, adapter):
        """Test splitting long response for SMS"""
        # Arrange
        # Create text that exceeds SMS limit (160)
        long_text = "Você tem os seguintes pedidos: " + (
            "Pedido #1 - R$ 50,00. "
        ) * 20
        
        # Act
        messages = adapter.split_long_response(long_text, ChannelType.SMS)
        
        # Assert
        assert len(messages) > 1
        for message in messages:
            assert len(message) <= adapter.CHANNEL_LIMITS[ChannelType.SMS]
    
    @pytest.mark.asyncio
    async def test_multi_channel_same_content(self, adapter):
        """Test adapting same content for multiple channels"""
        # Arrange
        original_text = "Confirmado com sucesso"
        
        # Act
        telegram_response = await adapter.adapt_response(
            original_text,
            ChannelType.TELEGRAM,
            add_emojis=True
        )
        whatsapp_response = await adapter.adapt_response(
            original_text,
            ChannelType.WHATSAPP,
            add_emojis=True
        )
        sms_response = await adapter.adapt_response(
            original_text,
            ChannelType.SMS,
            add_emojis=True
        )
        
        # Assert
        assert len(telegram_response) <= adapter.CHANNEL_LIMITS[ChannelType.TELEGRAM]
        assert len(whatsapp_response) <= adapter.CHANNEL_LIMITS[ChannelType.WHATSAPP]
        assert len(sms_response) <= adapter.CHANNEL_LIMITS[ChannelType.SMS]
        
        # Telegram and WhatsApp should have emojis
        assert adapter.EMOJI_MAP['success'] in telegram_response
        assert adapter.EMOJI_MAP['success'] in whatsapp_response
        
        # SMS should not have emojis
        for emoji in adapter.EMOJI_MAP.values():
            assert emoji not in sms_response
    
    @pytest.mark.asyncio
    async def test_error_message_adaptation(self, adapter):
        """Test adapting error messages"""
        # Arrange
        error_text = "Erro ao processar pedido"
        
        # Act
        telegram_response = await adapter.adapt_response(
            error_text,
            ChannelType.TELEGRAM,
            add_emojis=True
        )
        
        # Assert
        assert adapter.EMOJI_MAP['error'] in telegram_response
        assert "erro" in telegram_response.lower()
    
    @pytest.mark.asyncio
    async def test_order_message_adaptation(self, adapter):
        """Test adapting order messages"""
        # Arrange
        order_text = "Você tem 5 pedidos pendentes"
        
        # Act
        telegram_response = await adapter.adapt_response(
            order_text,
            ChannelType.TELEGRAM,
            add_emojis=True
        )
        
        # Assert
        assert adapter.EMOJI_MAP['order'] in telegram_response
        assert "pedidos" in telegram_response.lower()
    
    @pytest.mark.asyncio
    async def test_money_message_adaptation(self, adapter):
        """Test adapting money messages"""
        # Arrange
        money_text = "Seu faturamento total foi R$ 5.000,00"
        
        # Act
        telegram_response = await adapter.adapt_response(
            money_text,
            ChannelType.TELEGRAM,
            add_emojis=True
        )
        
        # Assert
        assert adapter.EMOJI_MAP['money'] in telegram_response
        assert "faturamento" in telegram_response.lower()
    
    @pytest.mark.asyncio
    async def test_channel_limit_enforcement_all_channels(self, adapter):
        """Test character limit enforcement for all channels"""
        # Arrange
        very_long_text = "x" * 100000
        
        # Act & Assert
        for channel in [ChannelType.TELEGRAM, ChannelType.WHATSAPP, ChannelType.SMS, ChannelType.EMAIL]:
            adapted = await adapter.adapt_response(very_long_text, channel)
            limit = adapter.get_channel_limit(channel)
            assert len(adapted) <= limit, f"Channel {channel} exceeded limit"
    
    @pytest.mark.asyncio
    async def test_emoji_support_consistency(self, adapter):
        """Test emoji support is consistent across channels"""
        # Arrange
        text_with_emoji = "✅ Confirmado"
        
        # Act
        for channel in [ChannelType.TELEGRAM, ChannelType.WHATSAPP, ChannelType.SMS, ChannelType.EMAIL]:
            supports = adapter.supports_emojis(channel)
            adapted = await adapter.adapt_response(text_with_emoji, channel, add_emojis=False)
            
            # Assert
            if not supports:
                # Channel doesn't support emojis, so they should be removed
                for emoji in adapter.EMOJI_MAP.values():
                    assert emoji not in adapted or channel in [ChannelType.TELEGRAM, ChannelType.WHATSAPP, ChannelType.WEB, ChannelType.APP]