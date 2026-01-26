"""
Performance tests for Telegram channel adapter.

Tests latency, throughput, and resource usage of Telegram operations.
"""

import pytest
import time
import hmac
import hashlib
import asyncio
from app.omnichannel.channel_adapters.telegram_adapter import TelegramAdapter


@pytest.mark.performance
class TestTelegramPerformance:
    """Performance tests for Telegram adapter"""
    
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
    
    def test_webhook_signature_validation_latency(self, adapter):
        """Test signature validation latency (< 10ms)"""
        # Arrange
        body = '{"message": {"text": "test"}}'
        signature = hmac.new(
            adapter.bot_token.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        start_time = time.time()
        
        # Act
        adapter.validate_webhook_signature(body, signature)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert elapsed < 0.01, f"Signature validation took {elapsed}s, expected < 10ms"
    
    @pytest.mark.asyncio
    async def test_message_parsing_latency(self, adapter, valid_payload):
        """Test message parsing latency (< 10ms)"""
        # Arrange
        start_time = time.time()
        
        # Act
        await adapter.parse_webhook(valid_payload)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert elapsed < 0.01, f"Message parsing took {elapsed}s, expected < 10ms"
    
    def test_response_formatting_latency(self, adapter):
        """Test response formatting latency (< 5ms)"""
        # Arrange
        text = "Você tem 3 pedidos no iFood"
        start_time = time.time()
        
        # Act
        adapter.format_response(text)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert elapsed < 0.005, f"Response formatting took {elapsed}s, expected < 5ms"
    
    @pytest.mark.asyncio
    async def test_send_message_latency(self, adapter):
        """Test sending message latency (< 10ms)"""
        # Arrange
        start_time = time.time()
        
        # Act
        await adapter.send_message("987654321", "Test message")
        
        elapsed = time.time() - start_time
        
        # Assert
        assert elapsed < 0.01, f"Send message took {elapsed}s, expected < 10ms"
    
    def test_signature_validation_throughput(self, adapter):
        """Test signature validation throughput"""
        # Arrange
        body = '{"message": {"text": "test"}}'
        signature = hmac.new(
            adapter.bot_token.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        num_validations = 1000
        start_time = time.time()
        
        # Act
        for _ in range(num_validations):
            adapter.validate_webhook_signature(body, signature)
        
        elapsed = time.time() - start_time
        throughput = num_validations / elapsed
        
        # Assert - Should validate at least 10,000 signatures per second
        assert throughput >= 10000, f"Throughput {throughput} sig/s, expected >= 10000 sig/s"
    
    @pytest.mark.asyncio
    async def test_message_parsing_throughput(self, adapter, valid_payload):
        """Test message parsing throughput"""
        # Arrange
        num_messages = 100
        start_time = time.time()
        
        # Act
        for i in range(num_messages):
            payload = valid_payload.copy()
            payload['update_id'] = 100 + i
            await adapter.parse_webhook(payload)
        
        elapsed = time.time() - start_time
        throughput = num_messages / elapsed
        
        # Assert - Should parse at least 1000 messages per second
        assert throughput >= 1000, f"Throughput {throughput} msg/s, expected >= 1000 msg/s"
    
    @pytest.mark.asyncio
    async def test_concurrent_message_parsing(self, adapter, valid_payload):
        """Test concurrent message parsing"""
        # Arrange
        num_concurrent = 50
        start_time = time.time()
        
        # Act
        tasks = [
            adapter.parse_webhook(valid_payload)
            for _ in range(num_concurrent)
        ]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert len(results) == num_concurrent
        assert elapsed < 0.5, f"Concurrent parsing took {elapsed}s, expected < 500ms"
    
    def test_response_formatting_with_long_text(self, adapter):
        """Test response formatting with long text"""
        # Arrange
        long_text = "x" * 5000
        start_time = time.time()
        
        # Act
        result = adapter.format_response(long_text)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert len(result) <= adapter.MESSAGE_CHAR_LIMIT
        assert elapsed < 0.01, f"Formatting long text took {elapsed}s, expected < 10ms"
    
    def test_extract_chat_id_latency(self, adapter, valid_payload):
        """Test extracting chat ID latency (< 5ms)"""
        # Arrange
        start_time = time.time()
        
        # Act
        adapter.extract_chat_id(valid_payload)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert elapsed < 0.005, f"Extract chat ID took {elapsed}s, expected < 5ms"
    
    def test_extract_user_id_latency(self, adapter, valid_payload):
        """Test extracting user ID latency (< 5ms)"""
        # Arrange
        start_time = time.time()
        
        # Act
        adapter.extract_user_id(valid_payload)
        
        elapsed = time.time() - start_time
        
        # Assert
        assert elapsed < 0.005, f"Extract user ID took {elapsed}s, expected < 5ms"
    
    @pytest.mark.asyncio
    async def test_complete_webhook_workflow_latency(self, adapter, valid_payload):
        """Test complete webhook workflow latency (< 50ms)"""
        # Arrange
        body = '{"message": {"text": "test"}}'
        signature = hmac.new(
            adapter.bot_token.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        start_time = time.time()
        
        # Act
        is_valid = adapter.validate_webhook_signature(body, signature)
        message = await adapter.parse_webhook(valid_payload)
        chat_id = adapter.extract_chat_id(valid_payload)
        formatted = adapter.format_response("Test response")
        
        elapsed = time.time() - start_time
        
        # Assert
        assert is_valid is True
        assert message is not None
        assert chat_id is not None
        assert elapsed < 0.05, f"Complete workflow took {elapsed}s, expected < 50ms"
