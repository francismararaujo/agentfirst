"""
Channel mapping service for extracting email from channel IDs.

Maps channel-specific user identifiers (Telegram ID, WhatsApp number, etc)
to universal email identifiers for cross-channel context preservation.
"""

from typing import Optional, Dict, Any
from app.omnichannel.models import ChannelType


class ChannelMappingService:
    """
    Maps channel-specific user IDs to email addresses.
    
    Enables universal user identification across channels by mapping
    channel-specific identifiers (Telegram ID, WhatsApp number) to email.
    """
    
    def __init__(self, channel_mapping_repository):
        """
        Initialize with channel mapping repository.
        
        Args:
            channel_mapping_repository: Repository for storing/retrieving channel mappings
        """
        self.repository = channel_mapping_repository
    
    async def get_email_by_channel_id(
        self,
        channel: ChannelType,
        channel_user_id: str
    ) -> Optional[str]:
        """
        Get email address for a channel user ID.
        
        Args:
            channel: Channel type (telegram, whatsapp, etc)
            channel_user_id: User ID from the channel (Telegram ID, WhatsApp number, etc)
        
        Returns:
            Email address if mapping exists, None otherwise
        """
        mapping = await self.repository.get_by_channel_id(channel.value, channel_user_id)
        return mapping.get('email') if mapping else None
    
    async def map_channel_to_email(
        self,
        channel: ChannelType,
        channel_user_id: str,
        email: str
    ) -> None:
        """
        Create or update mapping from channel ID to email.
        
        Args:
            channel: Channel type
            channel_user_id: User ID from the channel
            email: Email address to map to
        """
        await self.repository.create_mapping(
            channel=channel.value,
            channel_user_id=channel_user_id,
            email=email
        )
    
    async def create_mapping(
        self,
        email: str,
        channel: str,
        channel_user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create mapping from channel ID to email (alias for compatibility).
        
        Args:
            email: Email address
            channel: Channel type as string
            channel_user_id: User ID from the channel
            metadata: Optional metadata (ignored for now)
            
        Returns:
            Created mapping
        """
        # Note: metadata is ignored for now since repository doesn't support it
        return await self.repository.create_mapping(
            channel=channel,
            channel_user_id=channel_user_id,
            email=email
        )
    
    async def get_channels_for_email(self, email: str) -> dict:
        """
        Get all channel mappings for an email address.
        
        Enables sending notifications to all channels where user is connected.
        
        Args:
            email: Email address
        
        Returns:
            Dictionary mapping channel types to channel user IDs
            Example: {'telegram': '123456', 'whatsapp': '+5511999999999'}
        """
        mappings = await self.repository.get_by_email(email)
        return {
            mapping['channel']: mapping['channel_user_id']
            for mapping in mappings
        }
