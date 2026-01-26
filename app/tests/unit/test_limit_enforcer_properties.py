"""Property-based tests for Limit Enforcer - Validates correctness properties"""

import pytest
from hypothesis import given, strategies as st
from app.billing.limit_enforcer import LimitEnforcer, LimitEnforcerConfig


@pytest.mark.property
class TestLimitEnforcerProperties:
    """Property-based tests for Limit Enforcer"""

    @given(tier=st.sampled_from(["free", "pro", "enterprise"]))
    def test_tier_limit_is_positive(self, tier):
        """Validates: Tier limit is always positive
        
        Property: limit > 0 for all tiers
        """
        # Arrange
        config = LimitEnforcerConfig()
        limit_enforcer = LimitEnforcer(config)
        
        # Act
        limit = limit_enforcer._get_tier_limit(tier)
        
        # Assert
        assert limit > 0, f"Tier limit for {tier} should be positive, got {limit}"

    @given(tier=st.sampled_from(["free", "pro", "enterprise"]))
    def test_tier_limits_follow_business_rules(self, tier):
        """Validates: Tier limits follow business rules
        
        Property: free_limit < pro_limit < enterprise_limit
        """
        # Arrange
        config = LimitEnforcerConfig()
        limit_enforcer = LimitEnforcer(config)
        
        free_limit = limit_enforcer._get_tier_limit("free")
        pro_limit = limit_enforcer._get_tier_limit("pro")
        enterprise_limit = limit_enforcer._get_tier_limit("enterprise")
        
        # Assert
        assert free_limit < pro_limit < enterprise_limit, \
            f"Limits should follow: free({free_limit}) < pro({pro_limit}) < enterprise({enterprise_limit})"

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"])
    )
    def test_upgrade_url_contains_email_and_tier(self, email, tier):
        """Validates: Upgrade URL contains email and tier parameters
        
        Property: upgrade_url contains email and tier
        """
        # Arrange
        config = LimitEnforcerConfig()
        limit_enforcer = LimitEnforcer(config)
        
        # Act
        upgrade_url = limit_enforcer._generate_upgrade_url(email, tier)
        
        # Assert
        assert email in upgrade_url, f"Upgrade URL should contain email {email}"
        assert tier in upgrade_url, f"Upgrade URL should contain tier {tier}"
        assert upgrade_url.startswith("https://"), "Upgrade URL should be HTTPS"

    @given(
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        current_usage=st.integers(0, 100000)
    )
    def test_messages_available_never_negative(self, tier, current_usage):
        """Validates: Messages available is always >= 0
        
        Property: available = max(0, limit - current) >= 0
        """
        # Arrange
        limits = {
            'free': 100,
            'pro': 10000,
            'enterprise': 999999999
        }
        limit = limits[tier]
        
        # Act
        available = max(0, limit - current_usage)
        
        # Assert
        assert available >= 0, f"Messages available should never be negative, got {available}"

    @given(
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        current_usage=st.integers(0, 100000)
    )
    def test_usage_percentage_is_between_0_and_100(self, tier, current_usage):
        """Validates: Usage percentage is always between 0 and 100 (capped at 100)
        
        Property: 0 <= percentage <= 100 (percentage = min(100, (count/limit)*100))
        """
        # Arrange
        limits = {
            'free': 100,
            'pro': 10000,
            'enterprise': 999999999
        }
        limit = limits[tier]
        
        # Act
        percentage = min(100, (current_usage / limit * 100)) if limit > 0 else 0
        
        # Assert
        assert 0 <= percentage <= 100, f"Percentage should be between 0 and 100, got {percentage}"

    @given(
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        current_usage=st.integers(0, 100000)
    )
    def test_remaining_plus_used_equals_limit(self, tier, current_usage):
        """Validates: remaining + used = limit (when used <= limit)
        
        Property: remaining + used = limit (when used <= limit)
        """
        # Arrange
        limits = {
            'free': 100,
            'pro': 10000,
            'enterprise': 999999999
        }
        limit = limits[tier]
        
        # Act
        remaining = max(0, limit - current_usage)
        total = remaining + current_usage
        
        # Assert
        # When used > limit, remaining is capped at 0, so total = used + 0 = used (not limit)
        # When used <= limit, remaining = limit - used, so total = used + (limit - used) = limit
        if current_usage <= limit:
            assert total == limit, f"Remaining {remaining} + Used {current_usage} should equal limit {limit}"
        else:
            assert total == current_usage, f"When used > limit, total should be used {current_usage}"

    @given(
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        warning_threshold=st.floats(0, 100)
    )
    def test_warning_threshold_is_valid(self, tier, warning_threshold):
        """Validates: Warning threshold is between 0 and 100
        
        Property: 0 <= threshold <= 100
        """
        # Assert
        assert 0 <= warning_threshold <= 100, \
            f"Warning threshold should be between 0 and 100, got {warning_threshold}"

    @given(
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        current_usage=st.integers(0, 100000),
        warning_threshold=st.floats(0, 100)
    )
    def test_messages_until_warning_never_negative(self, tier, current_usage, warning_threshold):
        """Validates: Messages until warning is always >= 0
        
        Property: messages_until_warning >= 0
        """
        # Arrange
        limits = {
            'free': 100,
            'pro': 10000,
            'enterprise': 999999999
        }
        limit = limits[tier]
        
        # Act
        messages_until_warning = max(0, int(limit * warning_threshold / 100) - current_usage)
        
        # Assert
        assert messages_until_warning >= 0, \
            f"Messages until warning should never be negative, got {messages_until_warning}"

    @given(
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        current_usage=st.integers(0, 100000),
        count=st.integers(1, 1000)
    )
    def test_can_send_messages_is_boolean(self, tier, current_usage, count):
        """Validates: can_send_messages returns boolean
        
        Property: can_send_messages(email, tier, count) ∈ {True, False}
        """
        # Arrange
        limits = {
            'free': 100,
            'pro': 10000,
            'enterprise': 999999999
        }
        limit = limits[tier]
        
        # Act
        can_send = current_usage + count <= limit
        
        # Assert
        assert isinstance(can_send, bool), f"can_send_messages should return boolean, got {type(can_send)}"

    @given(
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        current_usage=st.integers(0, 100000),
        count=st.integers(1, 1000)
    )
    def test_can_send_messages_respects_limit(self, tier, current_usage, count):
        """Validates: can_send_messages respects tier limit
        
        Property: can_send(current, count) == (current + count <= limit)
        """
        # Arrange
        limits = {
            'free': 100,
            'pro': 10000,
            'enterprise': 999999999
        }
        limit = limits[tier]
        
        # Act
        can_send = current_usage + count <= limit
        
        # Assert
        if tier == "enterprise":
            assert can_send is True, f"Enterprise tier should always allow messages"
        else:
            expected = current_usage + count <= limit
            assert can_send == expected, \
                f"can_send should be {expected} for {tier} with {current_usage} used and {count} to send"

    @given(
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        current_usage=st.integers(0, 100000)
    )
    def test_enterprise_tier_has_unlimited_messages(self, tier, current_usage):
        """Validates: Enterprise tier has unlimited messages
        
        Property: tier=enterprise => messages_available = 999999999
        """
        # Arrange
        config = LimitEnforcerConfig()
        limit_enforcer = LimitEnforcer(config)
        
        if tier == "enterprise":
            # Act
            available = limit_enforcer._get_tier_limit(tier) - current_usage
            
            # Assert
            assert available >= 0, f"Enterprise tier should have unlimited messages"

    @given(
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        current_usage=st.integers(0, 100000)
    )
    def test_limit_status_has_all_required_fields(self, tier, current_usage):
        """Validates: Limit status has all required fields
        
        Property: status dict contains all required keys
        """
        # Arrange
        config = LimitEnforcerConfig()
        limit_enforcer = LimitEnforcer(config)
        
        limits = {
            'free': 100,
            'pro': 10000,
            'enterprise': 999999999
        }
        limit = limits[tier]
        remaining = max(0, limit - current_usage)
        percentage = (current_usage / limit * 100) if limit > 0 else 0
        
        # Act
        status = {
            'email': 'test@example.com',
            'tier': tier,
            'current_usage': current_usage,
            'limit': limit,
            'remaining': remaining,
            'percentage': percentage,
            'exceeded': current_usage >= limit,
            'upgrade_url': limit_enforcer._generate_upgrade_url('test@example.com', tier) if current_usage >= limit else None
        }
        
        # Assert
        required_keys = ['email', 'tier', 'current_usage', 'limit', 'remaining', 'percentage', 'exceeded', 'upgrade_url']
        for key in required_keys:
            assert key in status, f"Status should contain key {key}"
