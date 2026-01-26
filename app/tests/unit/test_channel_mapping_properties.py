"""Property-based tests for Channel Mapping - Validates correctness properties"""

import pytest
from hypothesis import given, strategies as st
from app.omnichannel.authentication.channel_mapping import ChannelMapping, ChannelMappingService


@pytest.mark.property
class TestChannelMappingModelProperties:
    """Property-based tests for ChannelMapping model"""

    @given(
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
    )
    def test_mapping_creation_preserves_data(self, email, channel, channel_id):
        """Validates: Mapping creation preserves data
        
        Property: Mapping attributes match provided values
        """
        # Act
        mapping = ChannelMapping(
            email=email,
            channel=channel,
            channel_id=channel_id,
        )
        
        # Assert
        assert mapping.email == email
        assert mapping.channel == channel
        assert mapping.channel_id == channel_id

    @given(
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
    )
    def test_mapping_has_valid_timestamps(self, email, channel, channel_id):
        """Validates: Mapping has valid timestamps
        
        Property: created_at <= updated_at
        """
        # Act
        mapping = ChannelMapping(
            email=email,
            channel=channel,
            channel_id=channel_id,
        )
        
        # Assert
        from datetime import datetime
        created = datetime.fromisoformat(mapping.created_at)
        updated = datetime.fromisoformat(mapping.updated_at)
        assert created <= updated

    @given(
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
        metadata=st.dictionaries(st.text(min_size=1), st.text()),
    )
    def test_mapping_preserves_metadata(self, email, channel, channel_id, metadata):
        """Validates: Mapping preserves metadata
        
        Property: Updated metadata == provided metadata
        """
        # Act
        mapping = ChannelMapping(
            email=email,
            channel=channel,
            channel_id=channel_id,
            metadata=metadata,
        )
        
        # Assert
        assert mapping.metadata == metadata


@pytest.mark.property
class TestChannelValidationProperties:
    """Property-based tests for channel validation"""

    @given(
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app", "email", "sms", "voice"]),
    )
    def test_channel_validation_accepts_valid_channels(self, channel):
        """Validates: Channel validation accepts valid channels
        
        Property: _validate_channel returns True for valid channels
        """
        # Act
        result = ChannelMappingService._validate_channel(channel)
        
        # Assert
        assert result is True

    @given(
        invalid_channel=st.text(min_size=1, max_size=100).filter(
            lambda x: x.lower() not in {"telegram", "whatsapp", "web", "app", "email", "sms", "voice"}
        ),
    )
    def test_channel_validation_rejects_invalid_channels(self, invalid_channel):
        """Validates: Channel validation rejects invalid channels
        
        Property: _validate_channel returns False for invalid channels
        """
        # Act
        result = ChannelMappingService._validate_channel(invalid_channel)
        
        # Assert
        assert result is False

    @given(
        channel_id=st.integers(min_value=100000000, max_value=999999999999),
    )
    def test_telegram_channel_id_validation_accepts_numeric_ids(self, channel_id):
        """Validates: Telegram channel ID validation accepts numeric IDs
        
        Property: _validate_channel_id returns True for numeric Telegram IDs
        """
        # Act
        result = ChannelMappingService._validate_channel_id("telegram", str(channel_id))
        
        # Assert
        assert result is True

    @given(
        channel_id=st.text(min_size=1, max_size=100).filter(lambda x: not x.isdigit()),
    )
    def test_telegram_channel_id_validation_rejects_non_numeric_ids(self, channel_id):
        """Validates: Telegram channel ID validation rejects non-numeric IDs
        
        Property: _validate_channel_id returns False for non-numeric Telegram IDs
        """
        # Act
        result = ChannelMappingService._validate_channel_id("telegram", channel_id)
        
        # Assert
        assert result is False


@pytest.mark.property
class TestChannelMappingSerializationProperties:
    """Property-based tests for channel mapping serialization"""

    @given(
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
    )
    def test_mapping_to_dict_and_from_dict_are_consistent(self, email, channel, channel_id):
        """Validates: Mapping serialization is consistent
        
        Property: from_dict(to_dict(mapping)) == mapping
        """
        # Arrange
        mapping = ChannelMapping(
            email=email,
            channel=channel,
            channel_id=channel_id,
        )
        
        # Act
        mapping_dict = mapping.to_dict()
        restored = ChannelMapping.from_dict(mapping_dict)
        
        # Assert
        assert restored.email == mapping.email
        assert restored.channel == mapping.channel
        assert restored.channel_id == mapping.channel_id

    @given(
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
        metadata=st.dictionaries(st.text(min_size=1), st.text()),
    )
    def test_mapping_serialization_preserves_all_fields(self, email, channel, channel_id, metadata):
        """Validates: Mapping serialization preserves all fields
        
        Property: All fields are preserved through serialization
        """
        # Arrange
        mapping = ChannelMapping(
            email=email,
            channel=channel,
            channel_id=channel_id,
            metadata=metadata,
        )
        
        # Act
        mapping_dict = mapping.to_dict()
        restored = ChannelMapping.from_dict(mapping_dict)
        
        # Assert
        assert restored.metadata == metadata


@pytest.mark.property
class TestChannelMappingConsistencyProperties:
    """Property-based tests for channel mapping consistency"""

    @given(
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
    )
    def test_mapping_data_is_consistent(self, email, channel, channel_id):
        """Validates: Mapping data is consistent
        
        Property: Multiple accesses return same data
        """
        # Arrange
        mapping = ChannelMapping(
            email=email,
            channel=channel,
            channel_id=channel_id,
        )
        
        # Act
        email1 = mapping.email
        email2 = mapping.email
        email3 = mapping.email
        
        # Assert
        assert email1 == email2 == email3 == email
