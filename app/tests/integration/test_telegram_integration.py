"""
Integration tests for Telegram channel adapter.

Tests complete workflows including webhook validation, message parsing,
and response formatting.
"""

import pytest
import hmac
import hashlib
from app.omnichannel.channel_adapters.telegram_adapter import TelegramAdapter
from app.omnichannel.models import ChannelType


@pytest.mark.integration
class TestTelegramIntegration:
    """Integration tests for Telegram adapter"""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter"""
        return TelegramAdapter(bot_token="test_bot_token_123")
    
    @pytest.fixture
    def valid_payload(self):
        """Valid Telegram payload"""
        return {
            'update_id': 123456789,
            'message': {
                'message_id': 1,
                'date': 1234567890,
                'chat': {
                    'id': 987654321,
                    'first_name': 'John',
                    'type': 'private'
                },
                'from': {
                    'id': 987654321,
                    'is_bot': False,
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'username': 'johndoe'
                },
                'text': 'Quantos pedidos tenho?'
            }
        }
    
    @pytest.mark.asyncio
    async def test_complete_webhook_workflow(self, adapter, valid_payload):
        """Test complete webhook processing workflow"""
        # Arrange
        body = '{"message": {"text": "test"}}'
        signature = hmac.new(
            adapter.bot_token.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Act - Validate signature
        is_valid = adapter.validate_webhook_signature(body, signature)
        assert is_valid is True
        
        # Act - Parse message
        message = await adapter.parse_webhook(valid_payload)
        
        # Assert
        assert message is not None
        assert message.channel == ChannelType.TELEGRAM
        assert message.text == "Quantos pedidos tenho?"
    
    @pytest.mark.asyncio
    async def test_message_with_metadata_workflow(self, adapter, valid_payload):
        """Test message parsing with metadata"""
        # Arrange
        valid_payload['message']['reply_to_message'] = {'message_id': 42}
        valid_payload['message']['edit_date'] = 1234567900
        
        # Act
        message = await adapter.parse_webhook(valid_payload)
        
        # Assert
        assert message is not None
        assert message.metadata['reply_to_message_id'] == 42
        assert message.metadata['edit_date'] == 1234567900
        assert message.metadata['username'] == 'johndoe'
    
    @pytest.mark.asyncio
    async def test_send_and_format_response_workflow(self, adapter):
        """Test sending and formatting response"""
        # Arrange
        chat_id = "987654321"
        response_text = "Você tem 3 pedidos no iFood"
        
        # Act - Format response
        formatted = adapter.format_response(response_text)
        
        # Assert
        assert len(formatted) <= adapter.MESSAGE_CHAR_LIMIT
        
        # Act - Send message
        sent = await adapter.send_message(chat_id, formatted)
        
        # Assert
        assert sent is True
    
    @pytest.mark.asyncio
    async def test_extract_user_info_workflow(self, adapter, valid_payload):
        """Test extracting user information"""
        # Act
        chat_id = adapter.extract_chat_id(valid_payload)
        user_id = adapter.extract_user_id(valid_payload)
        
        # Assert
        assert chat_id == "987654321"
        assert user_id == "987654321"
    
    @pytest.mark.asyncio
    async def test_long_message_truncation_workflow(self, adapter):
        """Test handling long messages"""
        # Arrange
        long_text = "x" * 5000
        chat_id = "987654321"
        
        # Act - Format response
        formatted = adapter.format_response(long_text)
        
        # Assert
        assert len(formatted) <= adapter.MESSAGE_CHAR_LIMIT
        assert formatted.endswith("...")
        
        # Act - Send truncated message
        sent = await adapter.send_message(chat_id, formatted)
        
        # Assert
        assert sent is True
    
    @pytest.mark.asyncio
    async def test_security_workflow_invalid_signature(self, adapter):
        """Test security: reject invalid signatures"""
        # Arrange
        body = '{"message": {"text": "test"}}'
        invalid_signature = "invalid_signature_123"
        
        # Act
        is_valid = adapter.validate_webhook_signature(body, invalid_signature)
        
        # Assert
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_security_workflow_tampered_body(self, adapter):
        """Test security: detect tampered body"""
        # Arrange
        original_body = '{"message": {"text": "test"}}'
        signature = hmac.new(
            adapter.bot_token.encode(),
            original_body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        tampered_body = '{"message": {"text": "tampered"}}'
        
        # Act
        is_valid = adapter.validate_webhook_signature(tampered_body, signature)
        
        # Assert
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_multiple_messages_workflow(self, adapter):
        """Test processing multiple messages"""
        # Arrange
        messages = [
            "Quantos pedidos tenho?",
            "Confirme esse pedido",
            "Qual foi meu faturamento?"
        ]
        
        # Act
        results = []
        for i, text in enumerate(messages):
            payload = {
                'update_id': 100 + i,
                'message': {
                    'message_id': i + 1,
                    'date': 1234567890 + i,
                    'chat': {'id': 987654321, 'type': 'private'},
                    'from': {'id': 987654321, 'is_bot': False, 'first_name': 'John'},
                    'text': text
                }
            }
            message = await adapter.parse_webhook(payload)
            results.append(message)
        
        # Assert
        assert len(results) == 3
        assert all(r is not None for r in results)
        assert results[0].text == "Quantos pedidos tenho?"
        assert results[1].text == "Confirme esse pedido"
        assert results[2].text == "Qual foi meu faturamento?"


@pytest.mark.integration
class TestTelegramSecurityIntegration:
    """Security integration tests for Telegram adapter"""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter"""
        return TelegramAdapter(bot_token="secret_bot_token")
    
    @pytest.mark.asyncio
    async def test_hmac_validation_with_different_tokens(self):
        """Test HMAC validation with different tokens"""
        # Arrange
        adapter1 = TelegramAdapter(bot_token="token1")
        adapter2 = TelegramAdapter(bot_token="token2")
        
        body = '{"message": {"text": "test"}}'
        
        # Create signature with token1
        signature = hmac.new(
            adapter1.bot_token.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Act - Validate with token1 (should pass)
        result1 = adapter1.validate_webhook_signature(body, signature)
        
        # Act - Validate with token2 (should fail)
        result2 = adapter2.validate_webhook_signature(body, signature)
        
        # Assert
        assert result1 is True
        assert result2 is False
    
    @pytest.mark.asyncio
    async def test_replay_attack_prevention(self, adapter):
        """Test that same signature cannot be reused with different body"""
        # Arrange
        body1 = '{"message": {"text": "send money"}}'
        body2 = '{"message": {"text": "send more money"}}'
        
        signature = hmac.new(
            adapter.bot_token.encode(),
            body1.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Act
        result1 = adapter.validate_webhook_signature(body1, signature)
        result2 = adapter.validate_webhook_signature(body2, signature)
        
        # Assert
        assert result1 is True
        assert result2 is False
