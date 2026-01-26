"""Channel Mapping Service - Maps channel IDs (Telegram, WhatsApp, etc) to email"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError


@dataclass
class ChannelMapping:
    """Channel mapping model"""
    email: str
    channel: str  # telegram, whatsapp, web, app, email, sms, voice
    channel_id: str  # Telegram ID, WhatsApp ID, etc
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'email': self.email,
            'channel': self.channel,
            'channel_id': self.channel_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ChannelMapping':
        """Create from dictionary"""
        return ChannelMapping(
            email=data['email'],
            channel=data['channel'],
            channel_id=data['channel_id'],
            created_at=data.get('created_at', datetime.now(timezone.utc).isoformat()),
            updated_at=data.get('updated_at', datetime.now(timezone.utc).isoformat()),
            metadata=data.get('metadata', {}),
        )


@dataclass
class ChannelMappingConfig:
    """Configuration for channel mapping"""
    region: str = "us-east-1"
    channel_mapping_table: str = "channel_mappings"
    channel_index: str = "channel_id-index"


class ChannelMappingService:
    """Service for managing channel to email mappings"""

    def __init__(self, config: ChannelMappingConfig = None):
        """Initialize channel mapping service"""
        self.config = config or ChannelMappingConfig()
        self.dynamodb = boto3.resource('dynamodb', region_name=self.config.region)
        self.table = self.dynamodb.Table(self.config.channel_mapping_table)

    @staticmethod
    def _validate_channel(channel: str) -> bool:
        """Validate channel name"""
        valid_channels = {'telegram', 'whatsapp', 'web', 'app', 'email', 'sms', 'voice'}
        return channel.lower() in valid_channels

    @staticmethod
    def _validate_channel_id(channel: str, channel_id: str) -> bool:
        """Validate channel ID format"""
        if not channel_id or not isinstance(channel_id, str):
            return False

        if channel.lower() == 'telegram':
            # Telegram IDs are numeric
            return channel_id.isdigit()
        elif channel.lower() == 'whatsapp':
            # WhatsApp IDs are numeric (phone number)
            return channel_id.isdigit() and len(channel_id) >= 10
        elif channel.lower() == 'email':
            # Email format validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(email_pattern, channel_id))
        elif channel.lower() == 'web':
            # Web IDs are typically UUIDs or session IDs
            return len(channel_id) >= 8
        elif channel.lower() == 'app':
            # App IDs are typically UUIDs or device IDs
            return len(channel_id) >= 8
        elif channel.lower() == 'sms':
            # SMS IDs are phone numbers
            return channel_id.isdigit() and len(channel_id) >= 10
        elif channel.lower() == 'voice':
            # Voice IDs are phone numbers
            return channel_id.isdigit() and len(channel_id) >= 10

        return True

    async def create_mapping(self, email: str, channel: str, channel_id: str,
                            metadata: Dict[str, Any] = None) -> ChannelMapping:
        """Create channel mapping"""
        # Validate inputs
        if not email or '@' not in email:
            raise ValueError("Invalid email format")

        if not self._validate_channel(channel):
            raise ValueError(f"Invalid channel: {channel}")

        if not self._validate_channel_id(channel, channel_id):
            raise ValueError(f"Invalid channel_id for channel {channel}: {channel_id}")

        # Check if mapping already exists
        existing = await self.get_mapping_by_channel(channel, channel_id)
        if existing:
            raise ValueError(f"Mapping already exists for {channel}:{channel_id}")

        # Create mapping
        mapping = ChannelMapping(
            email=email,
            channel=channel.lower(),
            channel_id=channel_id,
            metadata=metadata or {}
        )

        try:
            self.table.put_item(Item=mapping.to_dict())
        except ClientError as e:
            raise ValueError(f"Failed to create mapping: {str(e)}")

        return mapping

    async def get_email_by_channel(self, channel: str, channel_id: str) -> Optional[str]:
        """Get email by channel and channel_id"""
        mapping = await self.get_mapping_by_channel(channel, channel_id)
        return mapping.email if mapping else None

    async def get_mapping_by_channel(self, channel: str, channel_id: str) -> Optional[ChannelMapping]:
        """Get mapping by channel and channel_id"""
        if not self._validate_channel(channel):
            raise ValueError(f"Invalid channel: {channel}")

        if not self._validate_channel_id(channel, channel_id):
            raise ValueError(f"Invalid channel_id for channel {channel}: {channel_id}")

        try:
            response = self.table.query(
                IndexName=self.config.channel_index,
                KeyConditionExpression='channel = :channel AND channel_id = :channel_id',
                ExpressionAttributeValues={
                    ':channel': channel.lower(),
                    ':channel_id': channel_id
                }
            )

            if response['Items']:
                return ChannelMapping.from_dict(response['Items'][0])
            return None
        except ClientError as e:
            raise ValueError(f"Failed to get mapping: {str(e)}")

    async def get_mappings_by_email(self, email: str) -> list:
        """Get all mappings for an email"""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")

        try:
            response = self.table.query(
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )

            return [ChannelMapping.from_dict(item) for item in response['Items']]
        except ClientError as e:
            raise ValueError(f"Failed to get mappings: {str(e)}")

    async def update_mapping(self, email: str, channel: str, channel_id: str,
                            metadata: Dict[str, Any] = None) -> ChannelMapping:
        """Update channel mapping"""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")

        if not self._validate_channel(channel):
            raise ValueError(f"Invalid channel: {channel}")

        if not self._validate_channel_id(channel, channel_id):
            raise ValueError(f"Invalid channel_id for channel {channel}: {channel_id}")

        # Check if mapping exists
        existing = await self.get_mapping_by_channel(channel, channel_id)
        if not existing:
            raise ValueError(f"Mapping not found for {channel}:{channel_id}")

        # Update mapping
        try:
            updates = {
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            if metadata:
                updates['metadata'] = metadata

            self.table.update_item(
                Key={'email': email, 'channel': channel.lower()},
                UpdateExpression='SET ' + ', '.join([f'{k} = :{k}' for k in updates.keys()]),
                ExpressionAttributeValues={f':{k}': v for k, v in updates.items()}
            )

            # Fetch updated mapping
            return await self.get_mapping_by_channel(channel, channel_id)
        except ClientError as e:
            raise ValueError(f"Failed to update mapping: {str(e)}")

    async def delete_mapping(self, email: str, channel: str) -> bool:
        """Delete channel mapping"""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")

        if not self._validate_channel(channel):
            raise ValueError(f"Invalid channel: {channel}")

        try:
            response = self.table.delete_item(
                Key={'email': email, 'channel': channel.lower()},
                ReturnValues='ALL_OLD'
            )

            return 'Attributes' in response
        except ClientError as e:
            raise ValueError(f"Failed to delete mapping: {str(e)}")

    async def get_all_channels_for_email(self, email: str) -> list:
        """Get all channels connected to an email"""
        mappings = await self.get_mappings_by_email(email)
        return [m.channel for m in mappings]

    async def channel_exists_for_email(self, email: str, channel: str) -> bool:
        """Check if channel exists for email"""
        mappings = await self.get_mappings_by_email(email)
        return any(m.channel == channel.lower() for m in mappings)
