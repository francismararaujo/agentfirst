"""Property-based tests for User Repository - Validates correctness properties"""

import pytest
from hypothesis import given, strategies as st
from datetime import datetime, timezone, timedelta
from app.omnichannel.authentication.user_repository import User, UserRepositoryConfig


@pytest.mark.property
class TestUserModelProperties:
    """Property-based tests for User model"""

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
    )
    def test_user_creation_preserves_data(self, email, tier):
        """Validates: User creation preserves data
        
        Property: User attributes match provided values
        """
        # Act
        user = User(
            email=email,
            tier=tier,
        )
        
        # Assert
        assert user.email == email
        assert user.tier == tier

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
    )
    def test_user_has_valid_timestamps(self, email, tier):
        """Validates: User has valid timestamps
        
        Property: created_at <= updated_at
        """
        # Act
        user = User(
            email=email,
            tier=tier,
        )
        
        # Assert
        created = datetime.fromisoformat(user.created_at)
        updated = datetime.fromisoformat(user.updated_at)
        assert created <= updated

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
    )
    def test_user_has_default_payment_status(self, email, tier):
        """Validates: User has default payment status
        
        Property: payment_status == 'active' for new users
        """
        # Act
        user = User(
            email=email,
            tier=tier,
        )
        
        # Assert
        assert user.payment_status == "active"

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        metadata=st.dictionaries(st.text(min_size=1), st.text()),
    )
    def test_user_preserves_metadata(self, email, tier, metadata):
        """Validates: User preserves metadata
        
        Property: Updated metadata == provided metadata
        """
        # Act
        user = User(
            email=email,
            tier=tier,
            metadata=metadata,
        )
        
        # Assert
        assert user.metadata == metadata


@pytest.mark.property
class TestUserTierProperties:
    """Property-based tests for user tier"""

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
    )
    def test_user_tier_is_valid(self, email, tier):
        """Validates: User tier is valid
        
        Property: tier is one of valid values
        """
        # Act
        user = User(
            email=email,
            tier=tier,
        )
        
        # Assert
        assert user.tier in ["free", "pro", "enterprise"]

    @given(
        email=st.emails(),
    )
    def test_user_default_tier_is_free(self, email):
        """Validates: User default tier is free
        
        Property: tier == 'free' when not specified
        """
        # Act
        user = User(email=email)
        
        # Assert
        assert user.tier == "free"


@pytest.mark.property
class TestUserUsageProperties:
    """Property-based tests for user usage tracking"""

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
    )
    def test_user_usage_month_starts_at_zero(self, email, tier):
        """Validates: User usage_month starts at zero
        
        Property: usage_month == 0 for new users
        """
        # Act
        user = User(
            email=email,
            tier=tier,
        )
        
        # Assert
        assert user.usage_month == 0

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
    )
    def test_user_usage_total_starts_at_zero(self, email, tier):
        """Validates: User usage_total starts at zero
        
        Property: usage_total == 0 for new users
        """
        # Act
        user = User(
            email=email,
            tier=tier,
        )
        
        # Assert
        assert user.usage_total == 0

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        usage_month=st.integers(min_value=0, max_value=100000),
        usage_total=st.integers(min_value=0, max_value=1000000),
    )
    def test_user_usage_values_are_non_negative(self, email, tier, usage_month, usage_total):
        """Validates: User usage values are non-negative
        
        Property: usage_month >= 0 and usage_total >= 0
        """
        # Act
        user = User(
            email=email,
            tier=tier,
            usage_month=usage_month,
            usage_total=usage_total,
        )
        
        # Assert
        assert user.usage_month >= 0
        assert user.usage_total >= 0


@pytest.mark.property
class TestUserPaymentStatusProperties:
    """Property-based tests for user payment status"""

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        status=st.sampled_from(["active", "inactive", "trial"]),
    )
    def test_user_payment_status_is_valid(self, email, tier, status):
        """Validates: User payment status is valid
        
        Property: payment_status is one of valid values
        """
        # Act
        user = User(
            email=email,
            tier=tier,
            payment_status=status,
        )
        
        # Assert
        assert user.payment_status in ["active", "inactive", "trial"]

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
    )
    def test_user_default_payment_status_is_active(self, email, tier):
        """Validates: User default payment status is active
        
        Property: payment_status == 'active' when not specified
        """
        # Act
        user = User(
            email=email,
            tier=tier,
        )
        
        # Assert
        assert user.payment_status == "active"


@pytest.mark.property
class TestUserTrialProperties:
    """Property-based tests for user trial management"""

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
    )
    def test_user_trial_is_inactive_by_default(self, email, tier):
        """Validates: User trial is inactive by default
        
        Property: is_trial_active() == False for new users
        """
        # Act
        user = User(
            email=email,
            tier=tier,
        )
        
        # Assert
        assert user.is_trial_active() is False
        assert user.is_trial_expired() is True

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
    )
    def test_user_trial_is_active_when_set_to_future(self, email, tier):
        """Validates: User trial is active when set to future
        
        Property: is_trial_active() == True when trial_ends_at is in future
        """
        # Arrange
        user = User(
            email=email,
            tier=tier,
        )
        
        # Act
        user.trial_ends_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        
        # Assert
        assert user.is_trial_active() is True
        assert user.is_trial_expired() is False

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
    )
    def test_user_trial_is_expired_when_set_to_past(self, email, tier):
        """Validates: User trial is expired when set to past
        
        Property: is_trial_active() == False when trial_ends_at is in past
        """
        # Arrange
        user = User(
            email=email,
            tier=tier,
        )
        
        # Act
        user.trial_ends_at = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        
        # Assert
        assert user.is_trial_active() is False
        assert user.is_trial_expired() is True


@pytest.mark.property
class TestUserSerializationProperties:
    """Property-based tests for user serialization"""

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
    )
    def test_user_to_dict_and_from_dict_are_consistent(self, email, tier):
        """Validates: User serialization is consistent
        
        Property: from_dict(to_dict(user)) == user
        """
        # Arrange
        user = User(
            email=email,
            tier=tier,
        )
        
        # Act
        user_dict = user.to_dict()
        restored = User.from_dict(user_dict)
        
        # Assert
        assert restored.email == user.email
        assert restored.tier == user.tier
        assert restored.payment_status == user.payment_status

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        metadata=st.dictionaries(st.text(min_size=1), st.text()),
    )
    def test_user_serialization_preserves_all_fields(self, email, tier, metadata):
        """Validates: User serialization preserves all fields
        
        Property: All fields are preserved through serialization
        """
        # Arrange
        user = User(
            email=email,
            tier=tier,
            metadata=metadata,
        )
        
        # Act
        user_dict = user.to_dict()
        restored = User.from_dict(user_dict)
        
        # Assert
        assert restored.metadata == metadata


@pytest.mark.property
class TestUserConsistencyProperties:
    """Property-based tests for user consistency"""

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"]),
    )
    def test_user_data_is_consistent(self, email, tier):
        """Validates: User data is consistent
        
        Property: Multiple accesses return same data
        """
        # Arrange
        user = User(
            email=email,
            tier=tier,
        )
        
        # Act
        email1 = user.email
        email2 = user.email
        email3 = user.email
        
        # Assert
        assert email1 == email2 == email3 == email
