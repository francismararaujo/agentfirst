"""Unit tests for Channel Mapping Service"""

import pytest
from unittest.mock import patch, MagicMock
from app.omnichannel.authentication import (
    ChannelMappingService,
    ChannelMapping,
    ChannelMappingConfig,
)


@pytest.mark.unit
class TestChannelMappingConfig:
    """Tests for ChannelMappingConfig"""

    def test_config_creation_with_defaults(self):
        """Test creating config with default values"""
        config = ChannelMappingConfig()

        assert config.region == "us-east-1"
        assert config.channel_mapping_table == "channel_mappings"
        assert config.channel_index == "channel_id-index"

    def test_config_creation_with_custom_values(self):
        """Test creating config with custom values"""
        config = ChannelMappingConfig(
            region="eu-west-1",
            channel_mapping_table="custom_mappings",
            channel_index="custom_index",
        )

        assert config.region == "eu-west-1"
        assert config.channel_mapping_table == "custom_mappings"
        assert config.channel_index == "custom_index"


@pytest.mark.unit
class TestChannelMapping:
    """Tests for ChannelMapping model"""

    def test_channel_mapping_creation(self):
        """Test creating channel mapping"""
        mapping = ChannelMapping(
            email="user@example.com",
            channel="telegram",
            channel_id="123456",
        )

        assert mapping.email == "user@example.com"
        assert mapping.channel == "telegram"
        assert mapping.channel_id == "123456"
        assert mapping.created_at is not None
        assert mapping.updated_at is not None

    def test_channel_mapping_to_dict(self):
        """Test converting mapping to dictionary"""
        mapping = ChannelMapping(
            email="user@example.com",
            channel="telegram",
            channel_id="123456",
        )
        mapping_dict = mapping.to_dict()

        assert mapping_dict["email"] == "user@example.com"
        assert mapping_dict["channel"] == "telegram"
        assert mapping_dict["channel_id"] == "123456"
        assert "created_at" in mapping_dict
        assert "updated_at" in mapping_dict

    def test_channel_mapping_from_dict(self):
        """Test creating mapping from dictionary"""
        data = {
            "email": "user@example.com",
            "channel": "telegram",
            "channel_id": "123456",
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T10:00:00",
            "metadata": {"key": "value"},
        }

        mapping = ChannelMapping.from_dict(data)

        assert mapping.email == "user@example.com"
        assert mapping.channel == "telegram"
        assert mapping.channel_id == "123456"
        assert mapping.metadata["key"] == "value"

    def test_channel_mapping_with_metadata(self):
        """Test mapping with metadata"""
        metadata = {"phone": "+5511999999999", "verified": True}
        mapping = ChannelMapping(
            email="user@example.com",
            channel="whatsapp",
            channel_id="5511999999999",
            metadata=metadata,
        )

        assert mapping.metadata["phone"] == "+5511999999999"
        assert mapping.metadata["verified"] is True


@pytest.mark.unit
class TestChannelMappingService:
    """Tests for ChannelMappingService"""

    @pytest.fixture
    def config(self):
        """Create config"""
        return ChannelMappingConfig()

    @pytest.fixture
    def service(self, config):
        """Create service"""
        with patch("boto3.resource"):
            return ChannelMappingService(config)

    def test_validate_channel_valid(self):
        """Test channel validation (valid)"""
        assert ChannelMappingService._validate_channel("telegram") is True
        assert ChannelMappingService._validate_channel("whatsapp") is True
        assert ChannelMappingService._validate_channel("web") is True
        assert ChannelMappingService._validate_channel("app") is True
        assert ChannelMappingService._validate_channel("email") is True
        assert ChannelMappingService._validate_channel("sms") is True
        assert ChannelMappingService._validate_channel("voice") is True

    def test_validate_channel_invalid(self):
        """Test channel validation (invalid)"""
        assert ChannelMappingService._validate_channel("invalid") is False
        assert ChannelMappingService._validate_channel("") is False
        assert ChannelMappingService._validate_channel("facebook") is False

    def test_validate_channel_id_telegram(self):
        """Test channel ID validation for Telegram"""
        assert ChannelMappingService._validate_channel_id("telegram", "123456") is True
        assert ChannelMappingService._validate_channel_id("telegram", "abc") is False
        assert ChannelMappingService._validate_channel_id("telegram", "") is False

    def test_validate_channel_id_whatsapp(self):
        """Test channel ID validation for WhatsApp"""
        assert ChannelMappingService._validate_channel_id("whatsapp", "5511999999999") is True
        assert ChannelMappingService._validate_channel_id("whatsapp", "123") is False
        assert ChannelMappingService._validate_channel_id("whatsapp", "abc") is False

    def test_validate_channel_id_email(self):
        """Test channel ID validation for Email"""
        assert ChannelMappingService._validate_channel_id("email", "user@example.com") is True
        assert ChannelMappingService._validate_channel_id("email", "invalid-email") is False
        assert ChannelMappingService._validate_channel_id("email", "user@") is False

    def test_validate_channel_id_web(self):
        """Test channel ID validation for Web"""
        assert ChannelMappingService._validate_channel_id("web", "session123456") is True
        assert ChannelMappingService._validate_channel_id("web", "short") is False
        assert ChannelMappingService._validate_channel_id("web", "") is False

    @pytest.mark.asyncio
    async def test_create_mapping_success(self, service):
        """Test creating mapping successfully"""
        # First mock returns empty (no existing mapping)
        service.table.query = MagicMock(return_value={"Items": []})
        service.table.put_item = MagicMock()

        mapping = await service.create_mapping(
            "user@example.com", "telegram", "123456"
        )

        assert mapping.email == "user@example.com"
        assert mapping.channel == "telegram"
        assert mapping.channel_id == "123456"
        service.table.put_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_mapping_invalid_email(self, service):
        """Test creating mapping with invalid email"""
        with pytest.raises(ValueError):
            await service.create_mapping("invalid-email", "telegram", "123456")

    @pytest.mark.asyncio
    async def test_create_mapping_invalid_channel(self, service):
        """Test creating mapping with invalid channel"""
        with pytest.raises(ValueError):
            await service.create_mapping("user@example.com", "invalid", "123456")

    @pytest.mark.asyncio
    async def test_create_mapping_invalid_channel_id(self, service):
        """Test creating mapping with invalid channel ID"""
        with pytest.raises(ValueError):
            await service.create_mapping("user@example.com", "telegram", "abc")

    @pytest.mark.asyncio
    async def test_create_mapping_already_exists(self, service):
        """Test creating mapping that already exists"""
        service.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": "user@example.com",
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
            await service.create_mapping("user@example.com", "telegram", "123456")

    @pytest.mark.asyncio
    async def test_get_email_by_channel_success(self, service):
        """Test getting email by channel"""
        service.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": "user@example.com",
                        "channel": "telegram",
                        "channel_id": "123456",
                        "created_at": "2024-01-01T10:00:00",
                        "updated_at": "2024-01-01T10:00:00",
                        "metadata": {},
                    }
                ]
            }
        )

        email = await service.get_email_by_channel("telegram", "123456")

        assert email == "user@example.com"

    @pytest.mark.asyncio
    async def test_get_email_by_channel_not_found(self, service):
        """Test getting email by channel (not found)"""
        service.table.query = MagicMock(return_value={"Items": []})

        email = await service.get_email_by_channel("telegram", "999999")

        assert email is None

    @pytest.mark.asyncio
    async def test_get_mapping_by_channel_success(self, service):
        """Test getting mapping by channel"""
        service.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": "user@example.com",
                        "channel": "telegram",
                        "channel_id": "123456",
                        "created_at": "2024-01-01T10:00:00",
                        "updated_at": "2024-01-01T10:00:00",
                        "metadata": {},
                    }
                ]
            }
        )

        mapping = await service.get_mapping_by_channel("telegram", "123456")

        assert mapping is not None
        assert mapping.email == "user@example.com"
        assert mapping.channel == "telegram"

    @pytest.mark.asyncio
    async def test_get_mapping_by_channel_not_found(self, service):
        """Test getting mapping by channel (not found)"""
        service.table.query = MagicMock(return_value={"Items": []})

        mapping = await service.get_mapping_by_channel("telegram", "999999")

        assert mapping is None

    @pytest.mark.asyncio
    async def test_get_mappings_by_email_success(self, service):
        """Test getting all mappings for email"""
        service.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": "user@example.com",
                        "channel": "telegram",
                        "channel_id": "123456",
                        "created_at": "2024-01-01T10:00:00",
                        "updated_at": "2024-01-01T10:00:00",
                        "metadata": {},
                    },
                    {
                        "email": "user@example.com",
                        "channel": "whatsapp",
                        "channel_id": "5511999999999",
                        "created_at": "2024-01-01T10:00:00",
                        "updated_at": "2024-01-01T10:00:00",
                        "metadata": {},
                    },
                ]
            }
        )

        mappings = await service.get_mappings_by_email("user@example.com")

        assert len(mappings) == 2
        assert mappings[0].channel == "telegram"
        assert mappings[1].channel == "whatsapp"

    @pytest.mark.asyncio
    async def test_get_mappings_by_email_invalid_email(self, service):
        """Test getting mappings with invalid email"""
        with pytest.raises(ValueError):
            await service.get_mappings_by_email("invalid-email")

    @pytest.mark.asyncio
    async def test_update_mapping_success(self, service):
        """Test updating mapping"""
        service.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": "user@example.com",
                        "channel": "telegram",
                        "channel_id": "123456",
                        "created_at": "2024-01-01T10:00:00",
                        "updated_at": "2024-01-01T10:00:00",
                        "metadata": {},
                    }
                ]
            }
        )
        service.table.update_item = MagicMock()

        mapping = await service.update_mapping(
            "user@example.com",
            "telegram",
            "123456",
            metadata={"verified": True},
        )

        assert mapping is not None
        service.table.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_mapping_not_found(self, service):
        """Test updating mapping that doesn't exist"""
        service.table.query = MagicMock(return_value={"Items": []})

        with pytest.raises(ValueError):
            await service.update_mapping(
                "user@example.com", "telegram", "999999"
            )

    @pytest.mark.asyncio
    async def test_delete_mapping_success(self, service):
        """Test deleting mapping"""
        service.table.delete_item = MagicMock(
            return_value={"Attributes": {"email": "user@example.com"}}
        )

        result = await service.delete_mapping("user@example.com", "telegram")

        assert result is True
        service.table.delete_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_mapping_not_found(self, service):
        """Test deleting mapping that doesn't exist"""
        service.table.delete_item = MagicMock(return_value={})

        result = await service.delete_mapping("user@example.com", "telegram")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_channels_for_email(self, service):
        """Test getting all channels for email"""
        service.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": "user@example.com",
                        "channel": "telegram",
                        "channel_id": "123456",
                        "created_at": "2024-01-01T10:00:00",
                        "updated_at": "2024-01-01T10:00:00",
                        "metadata": {},
                    },
                    {
                        "email": "user@example.com",
                        "channel": "whatsapp",
                        "channel_id": "5511999999999",
                        "created_at": "2024-01-01T10:00:00",
                        "updated_at": "2024-01-01T10:00:00",
                        "metadata": {},
                    },
                ]
            }
        )

        channels = await service.get_all_channels_for_email("user@example.com")

        assert len(channels) == 2
        assert "telegram" in channels
        assert "whatsapp" in channels

    @pytest.mark.asyncio
    async def test_channel_exists_for_email_true(self, service):
        """Test checking if channel exists for email (true)"""
        service.table.query = MagicMock(
            return_value={
                "Items": [
                    {
                        "email": "user@example.com",
                        "channel": "telegram",
                        "channel_id": "123456",
                        "created_at": "2024-01-01T10:00:00",
                        "updated_at": "2024-01-01T10:00:00",
                        "metadata": {},
                    }
                ]
            }
        )

        exists = await service.channel_exists_for_email("user@example.com", "telegram")

        assert exists is True

    @pytest.mark.asyncio
    async def test_channel_exists_for_email_false(self, service):
        """Test checking if channel exists for email (false)"""
        service.table.query = MagicMock(return_value={"Items": []})

        exists = await service.channel_exists_for_email("user@example.com", "telegram")

        assert exists is False
