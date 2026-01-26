"""
Universal message models for omnichannel processing.

Defines the UniversalMessage model that represents messages from any channel
in a standardized format, enabling channel-agnostic processing.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class ChannelType(str, Enum):
    """Supported channel types"""
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    WEB = "web"
    APP = "app"
    EMAIL = "email"
    SMS = "sms"


@dataclass
class UniversalMessage:
    """
    Universal message format for all channels.
    
    Represents a message from any channel in a standardized format,
    enabling channel-agnostic processing by the Brain and other components.
    """
    
    # Message content
    text: str
    channel: ChannelType
    channel_user_id: str  # Telegram ID, WhatsApp number, etc
    
    # Metadata
    message_id: str  # Unique message ID from channel
    timestamp: datetime
    
    # Optional fields
    email: Optional[str] = None  # Extracted after authentication
    session_id: Optional[str] = None  # Session ID after authentication
    context: Dict[str, Any] = field(default_factory=dict)  # Conversation context
    metadata: Dict[str, Any] = field(default_factory=dict)  # Channel-specific metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling datetime serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['channel'] = self.channel.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UniversalMessage':
        """Create from dictionary, handling datetime deserialization"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['channel'] = ChannelType(data['channel'])
        return cls(**data)


@dataclass
class MessageContext:
    """
    Context information for a message.
    
    Stores conversation state, user preferences, and relevant history
    to enable contextual understanding and multi-turn conversations.
    """
    
    email: str
    channel: ChannelType
    last_intent: Optional[str] = None
    last_connector: Optional[str] = None
    last_order_id: Optional[str] = None
    conversation_history: list = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageContext':
        """Create from dictionary"""
        return cls(**data)
