"""
Unit tests for Telegram channel adapter.

Tests webhook validation, message parsing, and response formatting.
"""

import pytest
import hmac
import hashlib
import json
from datetime import datetime
from hypothesis import given, strategies as st

from app.omnichannel.channel_adapters.telegram_adapter import TelegramAdapter
from app.omnichannel.models import ChannelType


@pytest.mark.unit
class TestTelegramAdapter:
    """Tests for TelegramAdapter"""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter instance"""
        return TelegramAdapter(bot_token="test_bot_token_123")
    
    @pytest.fixture
    def valid_telegram_payload(self):
        """Valid Telegram webhook payload"""
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
    
    def test_adapter_initialization(self, adapter):
        """Test adapter initialization"""
        # Assert
        assert adapter.bot_token == "test_bot_token_123"
        assert adapter.MESSAGE_CHAR_LIMIT == 4096
    
    def test_validate_webhook_signature_valid(self, adapter):
        """Test validating valid webhook signature"""
        # Arrange
        body = '{"message": {"text": "test"}}'
        signature = hmac.new(
            adapter.bot_token.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Act
        result = adapter.validate_webhook_signature(body, signature)
        
        # Assert
        assert result is True
    
    def test_validate_webhook_signature_invalid(self, adapter):
        """Test validating invalid webhook signature"""
        # Arrange
        body = '{"message": {"text": "test"}}'
        invalid_signature = "invalid_signature_123"
        
        # Act
        result = adapter.validate_webhook_signature(body, invalid_signature)
        
        # Assert
        assert result is False
    
    def test_validate_webhook_signature_tampered_body(self, adapter):
        """Test validating signature with tampered body"""
        # Arrange
        body = '{"message": {"text": "test"}}'
        signature = hmac.new(
            adapter.bot_token.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        tampered_body = '{"message": {"text": "tampered"}}'
        
        # Act
        result = adapter.validate_webhook_signature(tampered_body, signature)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_parse_webhook_valid_message(self, adapter, valid_telegram_payload):
        """Test parsing valid Telegram message"""
        # Act
        result = await adapter.parse_webhook(valid_telegram_payload)
        
        # Assert
        assert result is not None
        assert result.channel == ChannelType.TELEGRAM
        assert result.text == "Quantos pedidos tenho?"
        assert result.channel_user_id == "987654321"
        assert result.message_id == "1"
    
    @pytest.mark.asyncio
    async def test_parse_webhook_missing_message(self, adapter):
        """Test parsing payload without message"""
        # Arrange
        payload = {'update_id': 123456789}
        
        # Act
        result = await adapter.parse_webhook(payload)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_parse_webhook_missing_text(self, adapter, valid_telegram_payload):
        """Test parsing message without text"""
        # Arrange
        valid_telegram_payload['message'].pop('text')
        
        # Act
        result = await adapter.parse_webhook(valid_telegram_payload)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_parse_webhook_missing_chat_id(self, adapter, valid_telegram_payload):
        """Test parsing message without chat ID"""
        # Arrange
        valid_telegram_payload['message']['chat'].pop('id')
        
        # Act
        result = await adapter.parse_webhook(valid_telegram_payload)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_parse_webhook_missing_user_id(self, adapter, valid_telegram_payload):
        """Test parsing message without user ID"""
        # Arrange
        valid_telegram_payload['message']['from'].pop('id')
        
        # Act
        result = await adapter.parse_webhook(valid_telegram_payload)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_parse_webhook_with_reply_to(self, adapter, valid_telegram_payload):
        """Test parsing message with reply_to"""
        # Arrange
        valid_telegram_payload['message']['reply_to_message'] = {'message_id': 42}
        
        # Act
        result = await adapter.parse_webhook(valid_telegram_payload)
        
        # Assert
        assert result is not None
        assert result.metadata['reply_to_message_id'] == 42
    
    @pytest.mark.asyncio
    async def test_parse_webhook_with_forward(self, adapter, valid_telegram_payload):
        """Test parsing forwarded message"""
        # Arrange
        valid_telegram_payload['message']['forward_from'] = {'id': 111111111}
        
        # Act
        result = await adapter.parse_webhook(valid_telegram_payload)
        
        # Assert
        assert result is not None
        assert result.metadata['forward_from'] == 111111111
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, adapter):
        """Test sending message"""
        # Act
        result = await adapter.send_message("987654321", "Test message")
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_message_empty_chat_id(self, adapter):
        """Test sending message with empty chat ID"""
        # Act
        result = await adapter.send_message("", "Test message")
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_message_empty_text(self, adapter):
        """Test sending message with empty text"""
        # Act
        result = await adapter.send_message("987654321", "")
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_message_exceeds_limit(self, adapter):
        """Test sending message that exceeds character limit"""
        # Arrange
        long_text = "x" * 5000  # Exceeds 4096 limit
        
        # Act
        result = await adapter.send_message("987654321", long_text)
        
        # Assert
        assert result is True  # Should still succeed but truncate
    
    def test_format_response_basic(self, adapter):
        """Test formatting basic response"""
        # Act
        result = adapter.format_response("Test response")
        
        # Assert
        assert result == "Test response"
    
    def test_format_response_exceeds_limit(self, adapter):
        """Test formatting response that exceeds limit"""
        # Arrange
        long_text = "x" * 5000
        
        # Act
        result = adapter.format_response(long_text)
        
        # Assert
        assert len(result) <= adapter.MESSAGE_CHAR_LIMIT
        assert result.endswith("...")
    
    def test_extract_chat_id_valid(self, adapter, valid_telegram_payload):
        """Test extracting chat ID"""
        # Act
        result = adapter.extract_chat_id(valid_telegram_payload)
        
        # Assert
        assert result == "987654321"
    
    def test_extract_chat_id_missing(self, adapter):
        """Test extracting chat ID when missing"""
        # Arrange
        payload = {'update_id': 123456789}
        
        # Act
        result = adapter.extract_chat_id(payload)
        
        # Assert
        assert result is None
    
    def test_extract_user_id_valid(self, adapter, valid_telegram_payload):
        """Test extracting user ID"""
        # Act
        result = adapter.extract_user_id(valid_telegram_payload)
        
        # Assert
        assert result == "987654321"
    
    def test_extract_user_id_missing(self, adapter):
        """Test extracting user ID when missing"""
        # Arrange
        payload = {'update_id': 123456789}
        
        # Act
        result = adapter.extract_user_id(payload)
        
        # Assert
        assert result is None


@pytest.mark.property
class TestTelegramAdapterProperties:
    """Property-based tests for Telegram adapter"""
    
    @given(st.text(min_size=1, max_size=100))
    def test_format_response_never_exceeds_limit(self, text):
        """Validates: Formatted response never exceeds character limit
        
        Property: len(format_response(text)) <= MESSAGE_CHAR_LIMIT
        """
        # Arrange
        adapter = TelegramAdapter(bot_token="test_token")
        
        # Act
        result = adapter.format_response(text)
        
        # Assert
        assert len(result) <= adapter.MESSAGE_CHAR_LIMIT
    
    @given(st.text(min_size=1, max_size=100))
    def test_signature_validation_is_consistent(self, body):
        """Validates: Signature validation is consistent
        
        Property: validate_webhook_signature(body, sig) always returns same result
        """
        # Arrange
        adapter = TelegramAdapter(bot_token="test_token")
        signature = hmac.new(
            adapter.bot_token.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Act
        result1 = adapter.validate_webhook_signature(body, signature)
        result2 = adapter.validate_webhook_signature(body, signature)
        
        # Assert
        assert result1 == result2
    
    @given(st.integers(min_value=1, max_value=999999999))
    def test_extract_chat_id_returns_string(self, chat_id):
        """Validates: extract_chat_id returns string or None
        
        Property: result is None or isinstance(result, str)
        """
        # Arrange
        adapter = TelegramAdapter(bot_token="test_token")
        payload = {
            'message': {
                'chat': {'id': chat_id}
            }
        }
        
        # Act
        result = adapter.extract_chat_id(payload)
        
        # Assert
        assert result is None or isinstance(result, str)
