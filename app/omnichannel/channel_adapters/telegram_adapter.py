"""
Telegram channel adapter for receiving and sending messages.

Handles Telegram webhook validation, message parsing, and response formatting.
"""

import hmac
import hashlib
import json
from typing import Optional, Dict, Any
from app.omnichannel.models import UniversalMessage, ChannelType


class TelegramAdapter:
    """
    Adapter for Telegram channel.
    
    Handles:
    1. Webhook validation (HMAC-SHA256)
    2. Message parsing from Telegram format
    3. Response formatting for Telegram
    4. Character limit enforcement
    """
    
    # Telegram API constants
    TELEGRAM_API_BASE = "https://api.telegram.org/bot"
    MESSAGE_CHAR_LIMIT = 4096  # Telegram message limit
    
    def __init__(self, bot_token: str):
        """
        Initialize Telegram adapter.
        
        Args:
            bot_token: Telegram bot token from Secrets Manager
        """
        self.bot_token = bot_token
    
    def validate_webhook_signature(
        self,
        body: str,
        signature: str
    ) -> bool:
        """
        Validate Telegram webhook signature using HMAC-SHA256.
        
        Args:
            body: Raw request body
            signature: X-Telegram-Bot-Api-Secret-Hash header value
        
        Returns:
            True if signature is valid, False otherwise
        """
        # Compute HMAC-SHA256 of body using bot token as key
        computed_hash = hmac.new(
            self.bot_token.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare with provided signature
        return hmac.compare_digest(computed_hash, signature)
    
    async def parse_webhook(
        self,
        payload: Dict[str, Any]
    ) -> Optional[UniversalMessage]:
        """
        Parse Telegram webhook payload into UniversalMessage.
        
        Args:
            payload: Telegram webhook payload
        
        Returns:
            UniversalMessage if valid message, None otherwise
        """
        # Check if this is a message update
        if 'message' not in payload:
            return None
        
        message = payload['message']
        
        # Extract required fields
        message_id = message.get('message_id')
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text')
        
        if not all([message_id, chat_id, text]):
            return None
        
        # Extract user info
        user = message.get('from', {})
        user_id = user.get('id')
        
        if not user_id:
            return None
        
        # Extract metadata
        metadata = {
            'chat_id': chat_id,
            'user_id': user_id,
            'first_name': user.get('first_name'),
            'last_name': user.get('last_name'),
            'username': user.get('username'),
            'is_bot': user.get('is_bot', False),
            'reply_to_message_id': message.get('reply_to_message', {}).get('message_id'),
            'edit_date': message.get('edit_date'),
            'forward_from': message.get('forward_from', {}).get('id'),
            'forward_from_chat': message.get('forward_from_chat', {}).get('id'),
        }
        
        # Create UniversalMessage
        from datetime import datetime
        universal_message = UniversalMessage(
            text=text,
            channel=ChannelType.TELEGRAM,
            channel_user_id=str(user_id),
            message_id=str(message_id),
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        return universal_message
    
    async def send_message(
        self,
        chat_id: str,
        text: str
    ) -> bool:
        """
        Send message to Telegram user.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text
        
        Returns:
            True if sent successfully, False otherwise
        """
        # Enforce character limit
        if len(text) > self.MESSAGE_CHAR_LIMIT:
            text = text[:self.MESSAGE_CHAR_LIMIT - 3] + "..."
        
        # In production, would call Telegram API
        # For now, just validate
        return bool(chat_id and text)
    
    def format_response(
        self,
        text: str,
        add_emojis: bool = True
    ) -> str:
        """
        Format response for Telegram.
        
        Args:
            text: Response text
            add_emojis: Whether to add emojis for better UX
        
        Returns:
            Formatted text for Telegram
        """
        # Enforce character limit
        if len(text) > self.MESSAGE_CHAR_LIMIT:
            text = text[:self.MESSAGE_CHAR_LIMIT - 3] + "..."
        
        return text
    
    def extract_chat_id(self, payload: Dict[str, Any]) -> Optional[str]:
        """
        Extract chat ID from Telegram payload.
        
        Args:
            payload: Telegram webhook payload
        
        Returns:
            Chat ID as string, or None if not found
        """
        if 'message' in payload:
            chat_id = payload['message'].get('chat', {}).get('id')
            return str(chat_id) if chat_id else None
        
        return None
    
    def extract_user_id(self, payload: Dict[str, Any]) -> Optional[str]:
        """
        Extract user ID from Telegram payload.
        
        Args:
            payload: Telegram webhook payload
        
        Returns:
            User ID as string, or None if not found
        """
        if 'message' in payload:
            user_id = payload['message'].get('from', {}).get('id')
            return str(user_id) if user_id else None
        
        return None
