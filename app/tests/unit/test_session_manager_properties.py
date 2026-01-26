"""Property-based tests for Session Manager - Validates correctness properties"""

import pytest
from hypothesis import given, strategies as st
from datetime import datetime, timezone, timedelta
from app.omnichannel.authentication.session_manager import Session, SessionConfig


@pytest.mark.property
class TestSessionModelProperties:
    """Property-based tests for Session model"""

    @given(
        session_id=st.text(min_size=1, max_size=100),
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
    )
    def test_session_creation_preserves_data(self, session_id, email, channel, channel_id):
        """Validates: Session creation preserves data
        
        Property: Session attributes match provided values
        """
        # Act
        session = Session(
            session_id=session_id,
            email=email,
            channel=channel,
            channel_id=channel_id,
        )
        
        # Assert
        assert session.session_id == session_id
        assert session.email == email
        assert session.channel == channel
        assert session.channel_id == channel_id

    @given(
        session_id=st.text(min_size=1, max_size=100),
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
    )
    def test_session_has_valid_timestamps(self, session_id, email, channel, channel_id):
        """Validates: Session has valid timestamps
        
        Property: created_at <= updated_at <= expires_at
        """
        # Act
        session = Session(
            session_id=session_id,
            email=email,
            channel=channel,
            channel_id=channel_id,
        )
        
        # Assert
        created = datetime.fromisoformat(session.created_at)
        updated = datetime.fromisoformat(session.updated_at)
        expires = datetime.fromisoformat(session.expires_at)
        
        assert created <= updated <= expires

    @given(
        session_id=st.text(min_size=1, max_size=100),
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
    )
    def test_session_expiration_is_24_hours(self, session_id, email, channel, channel_id):
        """Validates: Session expiration is approximately 24 hours
        
        Property: expires_at - created_at ≈ 24 hours (within 1 minute tolerance)
        """
        # Act
        session = Session(
            session_id=session_id,
            email=email,
            channel=channel,
            channel_id=channel_id,
        )
        
        # Assert
        created = datetime.fromisoformat(session.created_at)
        expires = datetime.fromisoformat(session.expires_at)
        diff = expires - created
        
        # Should be approximately 24 hours (within 1 minute)
        assert timedelta(hours=23, minutes=59) <= diff <= timedelta(hours=24, minutes=1)

    @given(
        session_id=st.text(min_size=1, max_size=100),
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
    )
    def test_new_session_is_valid(self, session_id, email, channel, channel_id):
        """Validates: Newly created session is valid
        
        Property: is_valid() == True for new sessions
        """
        # Act
        session = Session(
            session_id=session_id,
            email=email,
            channel=channel,
            channel_id=channel_id,
        )
        
        # Assert
        assert session.is_valid() is True
        assert session.is_expired() is False


@pytest.mark.property
class TestSessionValidationProperties:
    """Property-based tests for session validation"""

    @given(
        session_id=st.text(min_size=1, max_size=100),
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
    )
    def test_session_validation_is_consistent(self, session_id, email, channel, channel_id):
        """Validates: Session validation is consistent
        
        Property: Multiple validations return same result
        """
        # Arrange
        session = Session(
            session_id=session_id,
            email=email,
            channel=channel,
            channel_id=channel_id,
        )
        
        # Act
        result1 = session.is_valid()
        result2 = session.is_valid()
        result3 = session.is_valid()
        
        # Assert
        assert result1 == result2 == result3 == True

    @given(
        session_id=st.text(min_size=1, max_size=100),
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
    )
    def test_expired_session_is_invalid(self, session_id, email, channel, channel_id):
        """Validates: Expired session is invalid
        
        Property: is_valid() == False for expired sessions
        """
        # Arrange
        session = Session(
            session_id=session_id,
            email=email,
            channel=channel,
            channel_id=channel_id,
        )
        
        # Manually set expires_at to past
        session.expires_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        # Act & Assert
        assert session.is_valid() is False
        assert session.is_expired() is True


@pytest.mark.property
class TestSessionContextProperties:
    """Property-based tests for session context management"""

    @given(
        session_id=st.text(min_size=1, max_size=100),
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
        context=st.dictionaries(st.text(min_size=1), st.text()),
    )
    def test_session_context_is_preserved(self, session_id, email, channel, channel_id, context):
        """Validates: Session context is preserved
        
        Property: Updated context == provided context
        """
        # Act
        session = Session(
            session_id=session_id,
            email=email,
            channel=channel,
            channel_id=channel_id,
            context=context,
        )
        
        # Assert
        assert session.context == context

    @given(
        session_id=st.text(min_size=1, max_size=100),
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
        context=st.dictionaries(st.text(min_size=1), st.text()),
    )
    def test_session_context_defaults_to_empty_dict(self, session_id, email, channel, channel_id, context):
        """Validates: Session context defaults to empty dict
        
        Property: context is dict type
        """
        # Act
        session = Session(
            session_id=session_id,
            email=email,
            channel=channel,
            channel_id=channel_id,
        )
        
        # Assert
        assert isinstance(session.context, dict)
        assert session.context == {}


@pytest.mark.property
class TestSessionMetadataProperties:
    """Property-based tests for session metadata management"""

    @given(
        session_id=st.text(min_size=1, max_size=100),
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
        metadata=st.dictionaries(st.text(min_size=1), st.text()),
    )
    def test_session_metadata_is_preserved(self, session_id, email, channel, channel_id, metadata):
        """Validates: Session metadata is preserved
        
        Property: Updated metadata == provided metadata
        """
        # Act
        session = Session(
            session_id=session_id,
            email=email,
            channel=channel,
            channel_id=channel_id,
            metadata=metadata,
        )
        
        # Assert
        assert session.metadata == metadata

    @given(
        session_id=st.text(min_size=1, max_size=100),
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
    )
    def test_session_metadata_defaults_to_empty_dict(self, session_id, email, channel, channel_id):
        """Validates: Session metadata defaults to empty dict
        
        Property: metadata is dict type
        """
        # Act
        session = Session(
            session_id=session_id,
            email=email,
            channel=channel,
            channel_id=channel_id,
        )
        
        # Assert
        assert isinstance(session.metadata, dict)
        assert session.metadata == {}


@pytest.mark.property
class TestSessionSerializationProperties:
    """Property-based tests for session serialization"""

    @given(
        session_id=st.text(min_size=1, max_size=100),
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
    )
    def test_session_to_dict_and_from_dict_are_consistent(self, session_id, email, channel, channel_id):
        """Validates: Session serialization is consistent
        
        Property: from_dict(to_dict(session)) == session
        """
        # Arrange
        session = Session(
            session_id=session_id,
            email=email,
            channel=channel,
            channel_id=channel_id,
        )
        
        # Act
        session_dict = session.to_dict()
        restored = Session.from_dict(session_dict)
        
        # Assert
        assert restored.session_id == session.session_id
        assert restored.email == session.email
        assert restored.channel == session.channel
        assert restored.channel_id == session.channel_id

    @given(
        session_id=st.text(min_size=1, max_size=100),
        email=st.emails(),
        channel=st.sampled_from(["telegram", "whatsapp", "web", "app"]),
        channel_id=st.text(min_size=1, max_size=100),
        context=st.dictionaries(st.text(min_size=1), st.text()),
        metadata=st.dictionaries(st.text(min_size=1), st.text()),
    )
    def test_session_serialization_preserves_all_fields(self, session_id, email, channel, channel_id, context, metadata):
        """Validates: Session serialization preserves all fields
        
        Property: All fields are preserved through serialization
        """
        # Arrange
        session = Session(
            session_id=session_id,
            email=email,
            channel=channel,
            channel_id=channel_id,
            context=context,
            metadata=metadata,
        )
        
        # Act
        session_dict = session.to_dict()
        restored = Session.from_dict(session_dict)
        
        # Assert
        assert restored.context == context
        assert restored.metadata == metadata
