"""Property-based tests for Event Bus - Validates correctness properties"""

import pytest
from hypothesis import given, strategies as st
from app.core.event_bus import EventMessage, EventBusConfig


@pytest.mark.property
class TestEventMessageProperties:
    """Property-based tests for EventMessage"""

    @given(
        event_type=st.text(min_size=1, max_size=100),
        source=st.text(min_size=1, max_size=100),
    )
    def test_event_message_has_valid_correlation_id(self, event_type, source):
        """Validates: Event message always has a valid correlation ID
        
        Property: correlation_id is non-empty string
        """
        # Arrange
        data = {"test": "data"}
        
        # Act
        message = EventMessage(
            event_type=event_type,
            source=source,
            data=data
        )
        
        # Assert
        assert message.correlation_id is not None
        assert isinstance(message.correlation_id, str)
        assert len(message.correlation_id) > 0

    @given(
        event_type=st.text(min_size=1, max_size=100),
        source=st.text(min_size=1, max_size=100),
        correlation_id=st.uuids().map(str),
    )
    def test_event_message_preserves_correlation_id(self, event_type, source, correlation_id):
        """Validates: Event message preserves provided correlation ID
        
        Property: provided correlation_id == message.correlation_id
        """
        # Arrange
        data = {"test": "data"}
        
        # Act
        message = EventMessage(
            event_type=event_type,
            source=source,
            data=data,
            correlation_id=correlation_id
        )
        
        # Assert
        assert message.correlation_id == correlation_id

    @given(
        event_type=st.text(min_size=1, max_size=100),
        source=st.text(min_size=1, max_size=100),
        email=st.emails(),
    )
    def test_event_message_preserves_user_email(self, event_type, source, email):
        """Validates: Event message preserves user email
        
        Property: provided email == message.user_email
        """
        # Arrange
        data = {"test": "data"}
        
        # Act
        message = EventMessage(
            event_type=event_type,
            source=source,
            data=data,
            user_email=email
        )
        
        # Assert
        assert message.user_email == email

    @given(
        event_type=st.text(min_size=1, max_size=100),
        source=st.text(min_size=1, max_size=100),
    )
    def test_event_message_has_valid_timestamp(self, event_type, source):
        """Validates: Event message always has a valid ISO format timestamp
        
        Property: timestamp is valid ISO format datetime string
        """
        from datetime import datetime
        
        # Arrange
        data = {"test": "data"}
        
        # Act
        message = EventMessage(
            event_type=event_type,
            source=source,
            data=data
        )
        
        # Assert
        assert message.timestamp is not None
        try:
            datetime.fromisoformat(message.timestamp)
        except ValueError:
            pytest.fail(f"Timestamp {message.timestamp} is not valid ISO format")

    @given(
        event_type=st.text(min_size=1, max_size=100),
        source=st.text(min_size=1, max_size=100),
    )
    def test_event_message_to_dict_and_from_dict_are_inverse_operations(self, event_type, source):
        """Validates: to_dict() and from_dict() are inverse operations
        
        Property: from_dict(to_dict(message)) == message
        """
        # Arrange
        data = {"test": "data", "nested": {"key": "value"}}
        original = EventMessage(
            event_type=event_type,
            source=source,
            data=data,
            user_email="test@example.com"
        )
        
        # Act
        dict_repr = original.to_dict()
        reconstructed = EventMessage.from_dict(dict_repr)
        
        # Assert
        assert reconstructed.event_type == original.event_type
        assert reconstructed.source == original.source
        assert reconstructed.data == original.data
        assert reconstructed.correlation_id == original.correlation_id
        assert reconstructed.user_email == original.user_email

    @given(
        event_type=st.text(min_size=1, max_size=100),
        source=st.text(min_size=1, max_size=100),
    )
    def test_event_message_to_json_is_valid_json(self, event_type, source):
        """Validates: to_json() produces valid JSON string
        
        Property: json.loads(to_json()) succeeds
        """
        import json
        
        # Arrange
        data = {"test": "data"}
        message = EventMessage(
            event_type=event_type,
            source=source,
            data=data
        )
        
        # Act
        json_str = message.to_json()
        
        # Assert
        try:
            parsed = json.loads(json_str)
            assert parsed["event_type"] == event_type
            assert parsed["source"] == source
        except json.JSONDecodeError:
            pytest.fail(f"to_json() produced invalid JSON: {json_str}")

    @given(
        event_type=st.text(min_size=1, max_size=100),
        source=st.text(min_size=1, max_size=100),
    )
    def test_event_message_metadata_is_dict(self, event_type, source):
        """Validates: Event message metadata is always a dictionary
        
        Property: isinstance(message.metadata, dict)
        """
        # Arrange
        data = {"test": "data"}
        
        # Act
        message = EventMessage(
            event_type=event_type,
            source=source,
            data=data
        )
        
        # Assert
        assert isinstance(message.metadata, dict)


@pytest.mark.property
class TestEventBusConfigProperties:
    """Property-based tests for EventBusConfig"""

    @given(
        region=st.sampled_from(["us-east-1", "us-west-2", "eu-west-1"]),
        message_retention=st.integers(min_value=60, max_value=1209600),
        visibility_timeout=st.integers(min_value=0, max_value=43200),
        dlq_retention=st.integers(min_value=60, max_value=1209600),
    )
    def test_event_bus_config_has_valid_retention_values(
        self, region, message_retention, visibility_timeout, dlq_retention
    ):
        """Validates: EventBusConfig has valid retention values
        
        Property: All retention values are positive integers
        """
        # Act
        config = EventBusConfig(
            region=region,
            message_retention_seconds=message_retention,
            visibility_timeout_seconds=visibility_timeout,
            dlq_retention_seconds=dlq_retention,
        )
        
        # Assert
        assert config.message_retention_seconds > 0
        assert config.visibility_timeout_seconds >= 0
        assert config.dlq_retention_seconds > 0

    @given(
        region=st.sampled_from(["us-east-1", "us-west-2", "eu-west-1"]),
        enable_encryption=st.booleans(),
    )
    def test_event_bus_config_encryption_flag_is_boolean(self, region, enable_encryption):
        """Validates: EventBusConfig encryption flag is always boolean
        
        Property: isinstance(config.enable_encryption, bool)
        """
        # Act
        config = EventBusConfig(
            region=region,
            enable_encryption=enable_encryption,
        )
        
        # Assert
        assert isinstance(config.enable_encryption, bool)

    @given(
        region=st.sampled_from(["us-east-1", "us-west-2", "eu-west-1"]),
    )
    def test_event_bus_config_has_default_values(self, region):
        """Validates: EventBusConfig has sensible default values
        
        Property: All default values are valid
        """
        # Act
        config = EventBusConfig(region=region)
        
        # Assert
        assert config.region == region
        assert config.message_retention_seconds == 345600
        assert config.visibility_timeout_seconds == 300
        assert config.dlq_retention_seconds == 1209600
        assert config.enable_encryption is True
