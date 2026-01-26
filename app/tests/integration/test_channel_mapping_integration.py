"""Integration tests for Channel Mapping Service"""

import pytest
from unittest.mock import patch, MagicMock
from app.omnichannel.authentication import (
    ChannelMappingService,
    ChannelMappingConfig,
)


@pytest.mark.integration
class TestChannelMappingIntegration:
    """Integration tests for channel mapping"""

    @pytest.fixture
    def config(self):
        """Create config"""
        return ChannelMappingConfig()

    @pytest.fixture
    def service(self, config):
        """Create service"""
        with patch("boto3.resource"):
            return ChannelMappingService(config)

    @pytest.mark.asyncio
    async def test_complete_channel_mapping_lifecycle(self, service):
        """Test complete channel mapping lifecycle"""
        email = "user@example.com"
        channel = "telegram"
        channel_id = "123456"

        # Mock DynamoDB responses
        service.table.put_item = MagicMock()
        service.table.query = MagicMock(return_value={"Items": []})
        service.table.update_item = MagicMock()
        service.table.delete_item = MagicMock()

        # 1. Create mapping
        mapping = await service.create_mapping(email, channel, channel_id)
        assert mapping.email == email
        assert mapping.channel == channel
        assert mapping.channel_id == channel_id

        # 2. Get email by channel
        service.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": email,
                        "channel": channel,
                        "channel_id": channel_id,
                        "created_at": mapping.created_at,
                        "updated_at": mapping.updated_at,
                        "metadata": {},
                    }
                ]
            }
        )

        retrieved_email = await service.get_email_by_channel(channel, channel_id)
        assert retrieved_email == email

        # 3. Update mapping
        service.table.update_item = MagicMock()
        updated_mapping = await service.update_mapping(
            email, channel, channel_id, metadata={"verified": True}
        )
        assert updated_mapping is not None

        # 4. Delete mapping
        service.table.delete_item = MagicMock(
            return_value={"Attributes": {"email": email}}
        )
        result = await service.delete_mapping(email, channel)
        assert result is True

    @pytest.mark.asyncio
    async def test_multiple_channels_for_same_user(self, service):
        """Test multiple channels for same user"""
        email = "user@example.com"

        service.table.put_item = MagicMock()
        service.table.query = MagicMock(return_value={"Items": []})

        # Create Telegram mapping
        telegram_mapping = await service.create_mapping(email, "telegram", "123456")
        assert telegram_mapping.channel == "telegram"

        # Create WhatsApp mapping
        whatsapp_mapping = await service.create_mapping(
            email, "whatsapp", "5511999999999"
        )
        assert whatsapp_mapping.channel == "whatsapp"

        # Get all channels
        service.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": email,
                        "channel": "telegram",
                        "channel_id": "123456",
                        "created_at": telegram_mapping.created_at,
                        "updated_at": telegram_mapping.updated_at,
                        "metadata": {},
                    },
                    {
                        "email": email,
                        "channel": "whatsapp",
                        "channel_id": "5511999999999",
                        "created_at": whatsapp_mapping.created_at,
                        "updated_at": whatsapp_mapping.updated_at,
                        "metadata": {},
                    },
                ]
            }
        )

        channels = await service.get_all_channels_for_email(email)
        assert len(channels) == 2
        assert "telegram" in channels
        assert "whatsapp" in channels

    @pytest.mark.asyncio
    async def test_channel_mapping_with_metadata(self, service):
        """Test channel mapping with metadata"""
        email = "user@example.com"
        metadata = {"phone": "+5511999999999", "verified": True, "language": "pt-BR"}

        service.table.put_item = MagicMock()
        service.table.query = MagicMock(return_value={"Items": []})

        mapping = await service.create_mapping(
            email, "whatsapp", "5511999999999", metadata=metadata
        )

        assert mapping.metadata["phone"] == "+5511999999999"
        assert mapping.metadata["verified"] is True
        assert mapping.metadata["language"] == "pt-BR"

    @pytest.mark.asyncio
    async def test_get_mapping_by_different_channels(self, service):
        """Test getting mappings by different channels"""
        email = "user@example.com"

        # Telegram mapping
        service.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": email,
                        "channel": "telegram",
                        "channel_id": "123456",
                        "created_at": "2024-01-01T10:00:00",
                        "updated_at": "2024-01-01T10:00:00",
                        "metadata": {},
                    }
                ]
            }
        )

        telegram_mapping = await service.get_mapping_by_channel("telegram", "123456")
        assert telegram_mapping.channel == "telegram"

        # WhatsApp mapping
        service.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": email,
                        "channel": "whatsapp",
                        "channel_id": "5511999999999",
                        "created_at": "2024-01-01T10:00:00",
                        "updated_at": "2024-01-01T10:00:00",
                        "metadata": {},
                    }
                ]
            }
        )

        whatsapp_mapping = await service.get_mapping_by_channel(
            "whatsapp", "5511999999999"
        )
        assert whatsapp_mapping.channel == "whatsapp"

    @pytest.mark.asyncio
    async def test_channel_mapping_case_insensitive(self, service):
        """Test channel mapping is case insensitive"""
        email = "user@example.com"

        service.table.put_item = MagicMock()
        service.table.query = MagicMock(return_value={"Items": []})

        # Create with uppercase
        mapping = await service.create_mapping(email, "TELEGRAM", "123456")
        assert mapping.channel == "telegram"  # Should be lowercase

    @pytest.mark.asyncio
    async def test_channel_exists_for_email_workflow(self, service):
        """Test checking if channel exists for email"""
        email = "user@example.com"

        # Channel doesn't exist
        service.table.query = MagicMock(return_value={"Items": []})
        exists = await service.channel_exists_for_email(email, "telegram")
        assert exists is False

        # Channel exists
        service.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": email,
                        "channel": "telegram",
                        "channel_id": "123456",
                        "created_at": "2024-01-01T10:00:00",
                        "updated_at": "2024-01-01T10:00:00",
                        "metadata": {},
                    }
                ]
            }
        )
        exists = await service.channel_exists_for_email(email, "telegram")
        assert exists is True


@pytest.mark.integration
class TestChannelMappingErrorHandling:
    """Integration tests for channel mapping error handling"""

    @pytest.fixture
    def config(self):
        """Create config"""
        return ChannelMappingConfig()

    @pytest.fixture
    def service(self, config):
        """Create service"""
        with patch("boto3.resource"):
            return ChannelMappingService(config)

    @pytest.mark.asyncio
    async def test_invalid_email_formats(self, service):
        """Test with various invalid email formats"""
        invalid_emails = [
            "invalid",
            "user@",
            "@example.com",
            "user@.com",
            "user @example.com",
        ]

        for email in invalid_emails:
            with pytest.raises(ValueError):
                await service.create_mapping(email, "telegram", "123456")

    @pytest.mark.asyncio
    async def test_invalid_channel_ids_by_type(self, service):
        """Test invalid channel IDs for different channel types"""
        email = "user@example.com"

        # Invalid Telegram ID (non-numeric)
        with pytest.raises(ValueError):
            await service.create_mapping(email, "telegram", "abc")

        # Invalid WhatsApp ID (too short)
        with pytest.raises(ValueError):
            await service.create_mapping(email, "whatsapp", "123")

        # Invalid Email channel ID
        with pytest.raises(ValueError):
            await service.create_mapping(email, "email", "invalid-email")

    @pytest.mark.asyncio
    async def test_duplicate_mapping_prevention(self, service):
        """Test preventing duplicate mappings"""
        email = "user@example.com"

        service.table.put_item = MagicMock()
        service.table.query = MagicMock(return_value={"Items": []})

        # Create first mapping
        await service.create_mapping(email, "telegram", "123456")

        # Try to create duplicate
        service.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": email,
                        "channel": "telegram",
                        "channel_id": "123456",
                        "created_at": "2024-01-01T10:00:00",
                        "updated_at": "2024-01-01T10:00:00",
                        "metadata": {},
                    }
                ]
            }
        )

        with pytest.raises(ValueError):
            await service.create_mapping(email, "telegram", "123456")

    @pytest.mark.asyncio
    async def test_update_nonexistent_mapping(self, service):
        """Test updating non-existent mapping"""
        service.table.query = MagicMock(return_value={"Items": []})

        with pytest.raises(ValueError):
            await service.update_mapping("user@example.com", "telegram", "999999")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_mapping(self, service):
        """Test deleting non-existent mapping"""
        service.table.delete_item = MagicMock(return_value={})

        result = await service.delete_mapping("user@example.com", "telegram")

        assert result is False
