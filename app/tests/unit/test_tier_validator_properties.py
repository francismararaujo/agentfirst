"""Property-based tests for Tier Validator - Validates correctness properties"""

import pytest
from hypothesis import given, strategies as st
from app.billing.tier_validator import TierValidator


@pytest.mark.property
class TestTierValidatorProperties:
    """Property-based tests for Tier Validator"""

    @given(tier=st.sampled_from(["free", "pro", "enterprise"]))
    def test_valid_tier_validation_is_consistent(self, tier):
        """Validates: Valid tier validation is consistent
        
        Property: validate_tier(tier) returns True for all valid tiers
        """
        # Act
        result = TierValidator.validate_tier(tier)
        
        # Assert
        assert result is True, f"Tier {tier} should be valid"

    @given(tier=st.text().filter(lambda x: x not in ["free", "pro", "enterprise"]))
    def test_invalid_tier_validation_is_consistent(self, tier):
        """Validates: Invalid tier validation is consistent
        
        Property: validate_tier(invalid_tier) returns False
        """
        # Act
        result = TierValidator.validate_tier(tier)
        
        # Assert
        assert result is False, f"Tier {tier} should be invalid"

    @given(tier=st.sampled_from(["free", "pro", "enterprise"]))
    def test_get_tier_info_returns_non_none_for_valid_tier(self, tier):
        """Validates: get_tier_info returns non-None for valid tiers
        
        Property: get_tier_info(valid_tier) != None
        """
        # Act
        info = TierValidator.get_tier_info(tier)
        
        # Assert
        assert info is not None, f"Tier info for {tier} should not be None"
        assert info.tier.value == tier, f"Tier info tier should be {tier}"

    @given(tier=st.text().filter(lambda x: x not in ["free", "pro", "enterprise"]))
    def test_get_tier_info_returns_none_for_invalid_tier(self, tier):
        """Validates: get_tier_info returns None for invalid tiers
        
        Property: get_tier_info(invalid_tier) == None
        """
        # Act
        info = TierValidator.get_tier_info(tier)
        
        # Assert
        assert info is None, f"Tier info for invalid tier {tier} should be None"

    @given(tier=st.sampled_from(["free", "pro", "enterprise"]))
    def test_tier_limit_is_positive(self, tier):
        """Validates: Tier limit is always positive
        
        Property: limit > 0 for all tiers
        """
        # Act
        limit = TierValidator.get_tier_limit(tier)
        
        # Assert
        assert limit > 0, f"Tier limit for {tier} should be positive, got {limit}"

    @given(tier=st.sampled_from(["free", "pro", "enterprise"]))
    def test_tier_limits_follow_business_rules(self, tier):
        """Validates: Tier limits follow business rules
        
        Property: free_limit < pro_limit < enterprise_limit
        """
        # Arrange
        free_limit = TierValidator.get_tier_limit("free")
        pro_limit = TierValidator.get_tier_limit("pro")
        enterprise_limit = TierValidator.get_tier_limit("enterprise")
        
        # Assert
        assert free_limit < pro_limit < enterprise_limit, \
            f"Limits should follow: free({free_limit}) < pro({pro_limit}) < enterprise({enterprise_limit})"

    @given(tier=st.sampled_from(["free", "pro", "enterprise"]))
    def test_tier_price_is_non_negative(self, tier):
        """Validates: Tier price is always non-negative
        
        Property: price >= 0 for all tiers
        """
        # Act
        price = TierValidator.get_tier_price(tier)
        
        # Assert
        assert price is None or price >= 0, f"Tier price for {tier} should be non-negative, got {price}"

    @given(tier=st.sampled_from(["free", "pro", "enterprise"]))
    def test_tier_features_is_non_empty_list(self, tier):
        """Validates: Tier features is always a non-empty list
        
        Property: features is list and len(features) > 0
        """
        # Act
        features = TierValidator.get_tier_features(tier)
        
        # Assert
        assert isinstance(features, list), f"Features for {tier} should be a list"
        assert len(features) > 0, f"Features for {tier} should not be empty"

    @given(
        from_tier=st.sampled_from(["free", "pro", "enterprise"]),
        to_tier=st.sampled_from(["free", "pro", "enterprise"])
    )
    def test_upgrade_and_downgrade_are_mutually_exclusive(self, from_tier, to_tier):
        """Validates: Upgrade and downgrade are mutually exclusive
        
        Property: is_upgrade(a, b) XOR is_downgrade(a, b) OR (a == b)
        """
        # Act
        is_upgrade = TierValidator.is_tier_upgrade(from_tier, to_tier)
        is_downgrade = TierValidator.is_tier_downgrade(from_tier, to_tier)
        
        # Assert
        if from_tier == to_tier:
            assert not is_upgrade and not is_downgrade, \
                f"Same tier should not be upgrade or downgrade"
        else:
            assert is_upgrade != is_downgrade, \
                f"Upgrade and downgrade should be mutually exclusive for {from_tier} -> {to_tier}"

    @given(tier=st.sampled_from(["free", "pro", "enterprise"]))
    def test_get_tier_name_returns_non_empty_string(self, tier):
        """Validates: get_tier_name returns non-empty string
        
        Property: name is string and len(name) > 0
        """
        # Act
        name = TierValidator.get_tier_name(tier)
        
        # Assert
        assert isinstance(name, str), f"Tier name should be string"
        assert len(name) > 0, f"Tier name should not be empty"

    @given(tier=st.sampled_from(["free", "pro", "enterprise"]))
    def test_get_tier_description_returns_non_empty_string(self, tier):
        """Validates: get_tier_description returns non-empty string
        
        Property: description is string and len(description) > 0
        """
        # Act
        description = TierValidator.get_tier_description(tier)
        
        # Assert
        assert isinstance(description, str), f"Tier description should be string"
        assert len(description) > 0, f"Tier description should not be empty"

    @given(
        tier1=st.sampled_from(["free", "pro", "enterprise"]),
        tier2=st.sampled_from(["free", "pro", "enterprise"])
    )
    def test_compare_tiers_returns_valid_result(self, tier1, tier2):
        """Validates: compare_tiers returns -1, 0, or 1
        
        Property: compare_tiers(a, b) ∈ {-1, 0, 1}
        """
        # Act
        result = TierValidator.compare_tiers(tier1, tier2)
        
        # Assert
        assert result in [-1, 0, 1], f"Compare result should be -1, 0, or 1, got {result}"

    @given(
        tier1=st.sampled_from(["free", "pro", "enterprise"]),
        tier2=st.sampled_from(["free", "pro", "enterprise"])
    )
    def test_compare_tiers_is_consistent(self, tier1, tier2):
        """Validates: compare_tiers is consistent
        
        Property: compare_tiers(a, b) == -compare_tiers(b, a)
        """
        # Act
        result_ab = TierValidator.compare_tiers(tier1, tier2)
        result_ba = TierValidator.compare_tiers(tier2, tier1)
        
        # Assert
        assert result_ab == -result_ba, \
            f"Compare should be consistent: compare({tier1}, {tier2})={result_ab} should equal -compare({tier2}, {tier1})={result_ba}"

    @given(tier=st.sampled_from(["free", "pro", "enterprise"]))
    def test_compare_tier_with_itself_returns_zero(self, tier):
        """Validates: Comparing tier with itself returns 0
        
        Property: compare_tiers(a, a) == 0
        """
        # Act
        result = TierValidator.compare_tiers(tier, tier)
        
        # Assert
        assert result == 0, f"Comparing {tier} with itself should return 0, got {result}"

    def test_get_all_tiers_returns_all_three_tiers(self):
        """Validates: get_all_tiers returns all three tiers
        
        Property: len(get_all_tiers()) == 3
        """
        # Act
        all_tiers = TierValidator.get_all_tiers()
        
        # Assert
        assert len(all_tiers) == 3, f"Should have 3 tiers, got {len(all_tiers)}"
        assert "free" in all_tiers, "Should have free tier"
        assert "pro" in all_tiers, "Should have pro tier"
        assert "enterprise" in all_tiers, "Should have enterprise tier"
