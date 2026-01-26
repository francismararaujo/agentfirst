"""Integration tests for Tier Validator"""

import pytest
from app.billing.tier_validator import TierValidator, TierType


@pytest.mark.integration
class TestTierValidatorWorkflows:
    """Tests for tier validator workflows"""

    def test_complete_tier_upgrade_workflow(self):
        """Test complete tier upgrade workflow"""
        assert TierValidator.validate_tier("free")
        free_limit = TierValidator.get_tier_limit("free")
        assert free_limit == 100
        assert TierValidator.is_tier_upgrade("free", "pro")
        pro_limit = TierValidator.get_tier_limit("pro")
        assert pro_limit == 10000
        free_features = TierValidator.get_tier_features("free")
        pro_features = TierValidator.get_tier_features("pro")
        assert len(pro_features) > len(free_features)

    def test_complete_tier_downgrade_workflow(self):
        """Test complete tier downgrade workflow"""
        assert TierValidator.validate_tier("pro")
        pro_limit = TierValidator.get_tier_limit("pro")
        assert pro_limit == 10000
        assert TierValidator.is_tier_downgrade("pro", "free")
        free_limit = TierValidator.get_tier_limit("free")
        assert free_limit == 100

    def test_tier_upgrade_to_enterprise(self):
        """Test upgrading to enterprise tier"""
        assert TierValidator.is_tier_upgrade("free", "enterprise")
        enterprise_limit = TierValidator.get_tier_limit("enterprise")
        assert enterprise_limit == 999999999
        assert TierValidator.is_tier_upgrade("pro", "enterprise")

    def test_multiple_tier_scenarios(self):
        """Test multiple tier scenarios"""
        tiers = ["free", "pro", "enterprise"]
        for tier in tiers:
            assert TierValidator.validate_tier(tier)
            info = TierValidator.get_tier_info(tier)
            assert info is not None
            assert info.tier == TierType(tier)
            limit = TierValidator.get_tier_limit(tier)
            assert limit > 0
            features = TierValidator.get_tier_features(tier)
            assert len(features) > 0

    def test_tier_comparison_chain(self):
        """Test tier comparison chain"""
        assert TierValidator.compare_tiers("free", "pro") == -1
        assert TierValidator.compare_tiers("pro", "enterprise") == -1
        assert TierValidator.compare_tiers("free", "enterprise") == -1
        assert TierValidator.compare_tiers("pro", "free") == 1
        assert TierValidator.compare_tiers("enterprise", "pro") == 1
        assert TierValidator.compare_tiers("enterprise", "free") == 1

    def test_tier_pricing_structure(self):
        """Test tier pricing structure"""
        free_price = TierValidator.get_tier_price("free")
        pro_price = TierValidator.get_tier_price("pro")
        enterprise_price = TierValidator.get_tier_price("enterprise")
        assert free_price == 0.0
        assert pro_price > 0
        assert pro_price == 99.0
        assert enterprise_price is None

    def test_tier_feature_progression(self):
        """Test tier feature progression"""
        free_features = TierValidator.get_tier_features("free")
        pro_features = TierValidator.get_tier_features("pro")
        enterprise_features = TierValidator.get_tier_features("enterprise")
        assert len(free_features) <= len(pro_features)
        assert len(pro_features) <= len(enterprise_features)
        assert any("100 messages" in f for f in free_features)
        assert any("10,000 messages" in f for f in pro_features)
        assert any("Unlimited" in f for f in enterprise_features)

    def test_all_tiers_configuration(self):
        """Test all tiers configuration"""
        all_tiers = TierValidator.get_all_tiers()
        assert len(all_tiers) == 3
        assert "free" in all_tiers
        assert "pro" in all_tiers
        assert "enterprise" in all_tiers
        for tier_key, tier_info in all_tiers.items():
            assert tier_info.tier is not None
            assert tier_info.name is not None
            assert tier_info.description is not None
            assert tier_info.message_limit > 0
            assert tier_info.features is not None
            assert len(tier_info.features) > 0


@pytest.mark.integration
class TestTierValidatorErrorHandling:
    """Tests for tier validator error handling"""

    def test_invalid_tier_operations(self):
        """Test operations with invalid tier"""
        invalid_tier = "invalid_tier"
        assert not TierValidator.validate_tier(invalid_tier)
        assert TierValidator.get_tier_info(invalid_tier) is None
        with pytest.raises(ValueError):
            TierValidator.get_tier_limit(invalid_tier)
        with pytest.raises(ValueError):
            TierValidator.get_tier_price(invalid_tier)
        with pytest.raises(ValueError):
            TierValidator.get_tier_features(invalid_tier)

    def test_invalid_tier_comparisons(self):
        """Test comparisons with invalid tier"""
        with pytest.raises(ValueError):
            TierValidator.is_tier_upgrade("invalid", "pro")
        with pytest.raises(ValueError):
            TierValidator.is_tier_downgrade("invalid", "free")
        with pytest.raises(ValueError):
            TierValidator.compare_tiers("invalid", "pro")
        with pytest.raises(ValueError):
            TierValidator.is_tier_upgrade("free", "invalid")
        with pytest.raises(ValueError):
            TierValidator.is_tier_downgrade("pro", "invalid")
        with pytest.raises(ValueError):
            TierValidator.compare_tiers("free", "invalid")

    def test_tier_name_and_description_invalid(self):
        """Test name and description with invalid tier"""
        with pytest.raises(ValueError):
            TierValidator.get_tier_name("invalid")
        with pytest.raises(ValueError):
            TierValidator.get_tier_description("invalid")


@pytest.mark.integration
class TestTierValidatorConsistency:
    """Tests for tier validator consistency"""

    def test_tier_info_consistency(self):
        """Test tier info consistency across methods"""
        for tier in ["free", "pro", "enterprise"]:
            info = TierValidator.get_tier_info(tier)
            limit = TierValidator.get_tier_limit(tier)
            name = TierValidator.get_tier_name(tier)
            description = TierValidator.get_tier_description(tier)
            features = TierValidator.get_tier_features(tier)
            assert info.message_limit == limit
            assert info.name == name
            assert info.description == description
            assert info.features == features

    def test_tier_comparison_consistency(self):
        """Test tier comparison consistency"""
        assert TierValidator.compare_tiers("free", "pro") == -1
        assert TierValidator.compare_tiers("pro", "free") == 1
        assert TierValidator.compare_tiers("free", "pro") == -1
        assert TierValidator.compare_tiers("pro", "enterprise") == -1
        assert TierValidator.compare_tiers("free", "enterprise") == -1
        assert TierValidator.compare_tiers("free", "free") == 0
        assert TierValidator.compare_tiers("free", "free") == 0

    def test_upgrade_downgrade_consistency(self):
        """Test upgrade/downgrade consistency"""
        assert TierValidator.is_tier_upgrade("free", "pro")
        assert TierValidator.is_tier_downgrade("pro", "free")
        assert not TierValidator.is_tier_upgrade("pro", "free")
        assert not TierValidator.is_tier_downgrade("free", "pro")
        assert not TierValidator.is_tier_upgrade("free", "free")
        assert not TierValidator.is_tier_downgrade("free", "free")

    def test_tier_limit_ordering(self):
        """Test tier limit ordering"""
        free_limit = TierValidator.get_tier_limit("free")
        pro_limit = TierValidator.get_tier_limit("pro")
        enterprise_limit = TierValidator.get_tier_limit("enterprise")
        assert free_limit < pro_limit
        assert pro_limit < enterprise_limit
        assert free_limit < enterprise_limit
