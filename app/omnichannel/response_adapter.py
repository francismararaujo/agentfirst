"""
Response adaptation service for formatting responses for different channels.

Adapts responses to channel-specific constraints and formatting requirements.
"""

from app.omnichannel.models import ChannelType


class ResponseAdapter:
    """
    Adapts responses for different channels.
    
    Handles:
    1. Character limit enforcement
    2. Emoji adaptation
    3. Formatting for channel-specific requirements
    4. Link formatting
    5. Message splitting for long responses
    """
    
    # Channel-specific constraints
    CHANNEL_LIMITS = {
        ChannelType.TELEGRAM: 4096,
        ChannelType.WHATSAPP: 4096,
        ChannelType.WEB: 10000,
        ChannelType.APP: 10000,
        ChannelType.EMAIL: 50000,
        ChannelType.SMS: 160
    }
    
    # Emoji support by channel
    EMOJI_SUPPORT = {
        ChannelType.TELEGRAM: True,
        ChannelType.WHATSAPP: True,
        ChannelType.WEB: True,
        ChannelType.APP: True,
        ChannelType.EMAIL: False,
        ChannelType.SMS: False
    }
    
    # Emoji mappings for responses
    EMOJI_MAP = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'order': '📦',
        'money': '💰',
        'chart': '📊',
        'list': '📋',
        'clock': '⏰',
        'user': '👤',
        'store': '🏪',
        'phone': '📞',
        'email': '📧',
        'link': '🔗',
        'arrow': '➡️',
        'star': '⭐',
        'fire': '🔥',
        'thumbs_up': '👍',
        'thumbs_down': '👎'
    }
    
    def __init__(self):
        """Initialize response adapter"""
        pass
    
    async def adapt_response(
        self,
        text: str,
        channel: ChannelType,
        add_emojis: bool = True
    ) -> str:
        """
        Adapt response for specific channel.
        
        Args:
            text: Response text
            channel: Target channel
            add_emojis: Whether to add emojis
        
        Returns:
            Adapted response text
        """
        # 1. Add emojis if supported
        if add_emojis and self.EMOJI_SUPPORT.get(channel, False):
            text = self._add_emojis(text)
        
        # 2. Enforce character limit
        limit = self.CHANNEL_LIMITS.get(channel, 4096)
        text = self._enforce_limit(text, limit)
        
        # 3. Format for channel
        text = self._format_for_channel(text, channel)
        
        return text
    
    def _add_emojis(self, text: str) -> str:
        """
        Add emojis to response text.
        
        Args:
            text: Response text
        
        Returns:
            Text with emojis added
        """
        # Add emoji for success messages
        if any(word in text.lower() for word in ['confirmado', 'sucesso', 'ok', 'pronto']):
            if not text.startswith(self.EMOJI_MAP['success']):
                text = f"{self.EMOJI_MAP['success']} {text}"
        
        # Add emoji for error messages
        if any(word in text.lower() for word in ['erro', 'falha', 'problema', 'não']):
            if not text.startswith(self.EMOJI_MAP['error']):
                text = f"{self.EMOJI_MAP['error']} {text}"
        
        # Add emoji for order-related messages
        if any(word in text.lower() for word in ['pedido', 'pedidos', 'order']):
            if not text.startswith(self.EMOJI_MAP['order']):
                text = f"{self.EMOJI_MAP['order']} {text}"
        
        # Add emoji for money-related messages
        if any(word in text.lower() for word in ['faturamento', 'receita', 'ganho', 'lucro', 'r$']):
            if not text.startswith(self.EMOJI_MAP['money']):
                text = f"{self.EMOJI_MAP['money']} {text}"
        
        return text
    
    def _enforce_limit(self, text: str, limit: int) -> str:
        """
        Enforce character limit.
        
        Args:
            text: Response text
            limit: Character limit
        
        Returns:
            Text truncated to limit
        """
        if len(text) <= limit:
            return text
        
        # Truncate and add ellipsis
        return text[:limit - 3] + "..."
    
    def _format_for_channel(self, text: str, channel: ChannelType) -> str:
        """
        Format response for specific channel.
        
        Args:
            text: Response text
            channel: Target channel
        
        Returns:
            Formatted text
        """
        if channel == ChannelType.TELEGRAM:
            return self._format_telegram(text)
        elif channel == ChannelType.WHATSAPP:
            return self._format_whatsapp(text)
        elif channel == ChannelType.WEB:
            return self._format_web(text)
        elif channel == ChannelType.APP:
            return self._format_app(text)
        elif channel == ChannelType.EMAIL:
            return self._format_email(text)
        elif channel == ChannelType.SMS:
            return self._format_sms(text)
        
        return text
    
    def _format_telegram(self, text: str) -> str:
        """Format for Telegram"""
        # Telegram supports markdown
        # Convert **text** to *text* for bold
        text = text.replace('**', '*')
        return text
    
    def _format_whatsapp(self, text: str) -> str:
        """Format for WhatsApp"""
        # WhatsApp supports *bold*, _italic_, ~strikethrough~
        # Convert **text** to *text* for bold
        text = text.replace('**', '*')
        return text
    
    def _format_web(self, text: str) -> str:
        """Format for Web"""
        # Web can use HTML
        # Keep markdown for now, will be converted to HTML by frontend
        return text
    
    def _format_app(self, text: str) -> str:
        """Format for App"""
        # App can use rich text
        return text
    
    def _format_email(self, text: str) -> str:
        """Format for Email"""
        # Email should be plain text or HTML
        # Remove emojis for email
        for emoji in self.EMOJI_MAP.values():
            text = text.replace(emoji, '')
        return text.strip()
    
    def _format_sms(self, text: str) -> str:
        """Format for SMS"""
        # SMS is plain text only
        # Remove emojis and special formatting
        for emoji in self.EMOJI_MAP.values():
            text = text.replace(emoji, '')
        # Remove markdown
        text = text.replace('**', '')
        text = text.replace('*', '')
        text = text.replace('_', '')
        return text.strip()
    
    def split_long_response(
        self,
        text: str,
        channel: ChannelType
    ) -> list:
        """
        Split long response into multiple messages.
        
        Args:
            text: Response text
            channel: Target channel
        
        Returns:
            List of message chunks
        """
        limit = self.CHANNEL_LIMITS.get(channel, 4096)
        
        if len(text) <= limit:
            return [text]
        
        # Split by paragraphs first (double newlines)
        paragraphs = text.split('\n\n')
        messages = []
        current_message = ""
        
        for paragraph in paragraphs:
            # If single paragraph is too long, split by sentences
            if len(paragraph) > limit:
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    if len(current_message) + len(sentence) + 2 <= limit:
                        if current_message:
                            current_message += ". "
                        current_message += sentence
                    else:
                        if current_message:
                            messages.append(current_message)
                        current_message = sentence
            else:
                if len(current_message) + len(paragraph) + 2 <= limit:
                    if current_message:
                        current_message += "\n\n"
                    current_message += paragraph
                else:
                    if current_message:
                        messages.append(current_message)
                    current_message = paragraph
        
        if current_message:
            messages.append(current_message)
        
        return messages
    
    def get_channel_limit(self, channel: ChannelType) -> int:
        """
        Get character limit for channel.
        
        Args:
            channel: Target channel
        
        Returns:
            Character limit
        """
        return self.CHANNEL_LIMITS.get(channel, 4096)
    
    def supports_emojis(self, channel: ChannelType) -> bool:
        """
        Check if channel supports emojis.
        
        Args:
            channel: Target channel
        
        Returns:
            True if emojis are supported
        """
        return self.EMOJI_SUPPORT.get(channel, False)
