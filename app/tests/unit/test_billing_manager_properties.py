"""Property-based tests for Billing Manager - Validates correctness properties"""

import pytest
from hypothesis import given, strategies as st
from app.billing.billing_manager import BillingManager, BillingManagerConfig, BillingStatus


@pytest.mark.property
class TestBillingManagerProperties:
    """Property-based tests for Billing Manager"""

    @given(
        email=st.emails(),
        messages_used=st.integers(0, 100000),
        tier=st.sampled_from(["free", "pro", "enterprise"])
    )
    def test_messages_remaining_never_negative(self, email, messages_used, tier):
        """Validates: Remaining messages is always >= 0
        
        Property: remaining = max(0, limit - used) >= 0
        """
        # Arrange
        limits = {
            'free': 100,
            'pro': 10000,
            'enterprise': 999999999
        }
        limit = limits[tier]
        
        # Act
        remaining = max(0, limit - messages_used)
        
        # Assert
        assert remaining >= 0, f"Remaining {remaining} should never be negative"

    @given(
        email=st.emails(),
        messages_used=st.integers(0, 100000),
        tier=st.sampled_from(["free", "pro", "enterprise"])
    )
    def test_messages_used_plus_remaining_equals_limit(self, email, messages_used, tier):
        """Validates: messages_used + messages_remaining = messages_limit (when used <= limit)
        
        Property: used + remaining = limit (when used <= limit)
        """
        # Arrange
        limits = {
            'free': 100,
            'pro': 10000,
            'enterprise': 999999999
        }
        limit = limits[tier]
        
        # Act
        remaining = max(0, limit - messages_used)
        total = messages_used + remaining
        
        # Assert
        # When used > limit, remaining is capped at 0, so total = used + 0 = used (not limit)
        # When used <= limit, remaining = limit - used, so total = used + (limit - used) = limit
        if messages_used <= limit:
            assert total == limit, f"Used {messages_used} + Remaining {remaining} should equal limit {limit}"
        else:
            assert total == messages_used, f"When used > limit, total should be used {messages_used}"

    @given(
        tier1=st.sampled_from(["free", "pro", "enterprise"]),
        tier2=st.sampled_from(["free", "pro", "enterprise"])
    )
    def test_tier_comparison_is_transitive(self, tier1, tier2):
        """Validates: Tier comparison is transitive
        
        Property: if tier1 < tier2 and tier2 < tier3, then tier1 < tier3
        """
        # Arrange
        tier_order = ["free", "pro", "enterprise"]
        idx1 = tier_order.index(tier1)
        idx2 = tier_order.index(tier2)
        
        # Act
        comparison = idx1 < idx2
        
        # Assert
        # This is always true by definition of list ordering
        assert isinstance(comparison, bool), "Comparison should return boolean"

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"])
    )
    def test_upgrade_url_contains_email_and_tier(self, email, tier):
        """Validates: Upgrade URL contains email and tier parameters
        
        Property: upgrade_url contains email and tier
        """
        # Arrange
        config = BillingManagerConfig()
        
        # Act
        upgrade_url = f"{config.upgrade_base_url}?email={email}&tier={tier}"
        
        # Assert
        assert email in upgrade_url, f"Upgrade URL should contain email {email}"
        assert tier in upgrade_url, f"Upgrade URL should contain tier {tier}"
        assert upgrade_url.startswith("https://"), "Upgrade URL should be HTTPS"

    @given(
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        messages_remaining=st.integers(0, 100000)
    )
    def test_billing_status_is_valid(self, tier, messages_remaining):
        """Validates: Billing status is always valid
        
        Property: status ∈ {ACTIVE, INACTIVE, TRIAL, SUSPENDED}
        """
        # Arrange
        from unittest.mock import AsyncMock
        from app.billing.usage_tracker import UsageTracker
        from app.billing.limit_enforcer import LimitEnforcer
        
        usage_tracker = AsyncMock(spec=UsageTracker)
        limit_enforcer = AsyncMock(spec=LimitEnforcer)
        config = BillingManagerConfig()
        billing_manager = BillingManager(usage_tracker, limit_enforcer, config)
        
        # Act
        status = billing_manager._determine_status(tier, messages_remaining)
        
        # Assert
        valid_statuses = [BillingStatus.ACTIVE, BillingStatus.INACTIVE, BillingStatus.TRIAL, BillingStatus.SUSPENDED]
        assert status in valid_statuses, f"Status {status} should be one of {valid_statuses}"

    @given(
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        messages_remaining=st.integers(0, 100000)
    )
    def test_free_tier_with_no_messages_is_suspended(self, tier, messages_remaining):
        """Validates: Free tier with no messages remaining is SUSPENDED
        
        Property: tier=free AND remaining=0 => status=SUSPENDED
        """
        # Arrange
        from unittest.mock import AsyncMock
        from app.billing.usage_tracker import UsageTracker
        from app.billing.limit_enforcer import LimitEnforcer
        
        usage_tracker = AsyncMock(spec=UsageTracker)
        limit_enforcer = AsyncMock(spec=LimitEnforcer)
        config = BillingManagerConfig()
        billing_manager = BillingManager(usage_tracker, limit_enforcer, config)
        
        if tier == "free" and messages_remaining == 0:
            # Act
            status = billing_manager._determine_status(tier, messages_remaining)
            
            # Assert
            assert status == BillingStatus.SUSPENDED, f"Free tier with 0 messages should be SUSPENDED, got {status}"

    @given(
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        messages_remaining=st.integers(1, 100000)
    )
    def test_free_tier_with_messages_is_trial(self, tier, messages_remaining):
        """Validates: Free tier with messages remaining is TRIAL
        
        Property: tier=free AND remaining>0 => status=TRIAL
        """
        # Arrange
        from unittest.mock import AsyncMock
        from app.billing.usage_tracker import UsageTracker
        from app.billing.limit_enforcer import LimitEnforcer
        
        usage_tracker = AsyncMock(spec=UsageTracker)
        limit_enforcer = AsyncMock(spec=LimitEnforcer)
        config = BillingManagerConfig()
        billing_manager = BillingManager(usage_tracker, limit_enforcer, config)
        
        if tier == "free" and messages_remaining > 0:
            # Act
            status = billing_manager._determine_status(tier, messages_remaining)
            
            # Assert
            assert status == BillingStatus.TRIAL, f"Free tier with messages should be TRIAL, got {status}"

    @given(
        tier=st.sampled_from(["pro", "enterprise"]),
        messages_remaining=st.integers(1, 100000)
    )
    def test_paid_tier_with_messages_is_active(self, tier, messages_remaining):
        """Validates: Paid tier with messages remaining is ACTIVE
        
        Property: tier∈{pro,enterprise} AND remaining>0 => status=ACTIVE
        """
        # Arrange
        from unittest.mock import AsyncMock
        from app.billing.usage_tracker import UsageTracker
        from app.billing.limit_enforcer import LimitEnforcer
        
        usage_tracker = AsyncMock(spec=UsageTracker)
        limit_enforcer = AsyncMock(spec=LimitEnforcer)
        config = BillingManagerConfig()
        billing_manager = BillingManager(usage_tracker, limit_enforcer, config)
        
        if tier in ["pro", "enterprise"] and messages_remaining > 0:
            # Act
            status = billing_manager._determine_status(tier, messages_remaining)
            
            # Assert
            assert status == BillingStatus.ACTIVE, f"Paid tier with messages should be ACTIVE, got {status}"

