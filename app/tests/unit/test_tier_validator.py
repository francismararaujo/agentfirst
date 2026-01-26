"""Unit tests for Tier Validator - Test tier validation and configuration"""

import pytest
from app.billing.tier_validator import (
    TierValidator,
    TierType,
    TierInfo,
)


@pytest.mark.unit
class TestTierType:
    """Tests for TierType enum"""

    def test_tier_type_free(self):
        """Test FREE tier type"""
        assert TierType.FREE.value == "free"

    def test_tier_type_pro(self):
        """Test PRO tier type"""
        assert TierType.PRO.value == "pro"

    def test_tier_type_enterprise(self):
        """Test ENTERPRISE tier type"""
        assert TierType.ENTERPRISE.value == "enterprise"


@pytest.mark.unit
class TestTierInfo:
    """Tests for TierInfo dataclass"""

    def test_tier_info_creation(self):
        """Test creating TierInfo"""
        info = TierInfo(
            tier=TierType.FREE,
            name="Free",
            description="Free tier",
            message_limit=100,
            price_per_month=0.0,
            features=["Feature 1", "Feature 2"]
        )
        assert info.tier == TierType.FREE
        assert info.name == "Free"
        assert info.message_limit == 100
        assert len(info.features) == 2

    def test_tier_info_default_features(self):
        """Test TierInfo with default features"""
        info = TierInfo(
            tier=TierType.FREE,
            name="Free",
            description="Free tier",
            message_limit=100
        )
        assert info.features == []


@pytest.mark.unit
class TestTierValidatorValidation:
    """Tests for TierValidator validation methods"""

    def test_validate_tier_free(self):
        """Test validating free tier"""
        assert TierValidator.validate_tier("free") is True

    def test_validate_tier_pro(self):
        """Test validating pro tier"""
        assert TierValidator.validate_tier("pro") is True

    def test_validate_tier_enterprise(self):
        """Test validating enterprise tier"""
        assert TierValidator.validate_tier("enterprise") is True

    def test_validate_tier_invalid(self):
        """Test validating invalid tier"""
        assert TierValidator.validate_tier("invalid") is False

    def test_validate_tier_empty(self):
        """Test validating empty tier"""
        assert TierValidator.validate_tier("") is False

    def test_validate_tier_case_sensitive(self):
        """Test that tier validation is case sensitive"""
        assert TierValidator.validate_tier("FREE") is False
        assert TierValidator.validate_tier("Pro") is False


@pytest.mark.unit
class TestTierValidatorInfo:
    """Tests for TierValidator info methods"""

    def test_get_tier_info_free(self):
        """Test getting free tier info"""
        info = TierValidator.get_tier_info("free")
        assert info is not None
        assert info.tier == TierType.FREE
        assert info.message_limit == 100
        assert info.price_per_month == 0.0

    def test_get_tier_info_pro(self):
        """Test getting pro tier info"""
        info = TierValidator.get_tier_info("pro")
        assert info is not None
        assert info.tier == TierType.PRO
        assert info.message_limit == 10000
        assert info.price_per_month == 99.0

    def test_get_tier_info_enterprise(self):
        """Test getting enterprise tier info"""
        info = TierValidator.get_tier_info("enterprise")
        assert info is not None
        assert info.tier == TierType.ENTERPRISE
        assert info.message_limit == 999999999
        assert info.price_per_month is None

    def test_get_tier_info_invalid(self):
        """Test getting invalid tier info"""
        info = TierValidator.get_tier_info("invalid")
        assert info is None

    def test_get_tier_limit_free(self):
        """Test getting free tier limit"""
        limit = TierValidator.get_tier_limit("free")
        assert limit == 100

    def test_get_tier_limit_pro(self):
        """Test getting pro tier limit"""
        limit = TierValidator.get_tier_limit("pro")
        assert limit == 10000

    def test_get_tier_limit_enterprise(self):
        """Test getting enterprise tier limit"""
        limit = TierValidator.get_tier_limit("enterprise")
        assert limit == 999999999

    def test_get_tier_limit_invalid(self):
        """Test getting invalid tier limit"""
        with pytest.raises(ValueError, match="Invalid tier"):
            TierValidator.get_tier_limit("invalid")

    def test_get_tier_price_free(self):
        """Test getting free tier price"""
        price = TierValidator.get_tier_price("free")
        assert price == 0.0

    def test_get_tier_price_pro(self):
        """Test getting pro tier price"""
        price = TierValidator.get_tier_price("pro")
        assert price == 99.0

    def test_get_tier_price_enterprise(self):
        """Test getting enterprise tier price"""
        price = TierValidator.get_tier_price("enterprise")
        assert price is None

    def test_get_tier_price_invalid(self):
        """Test getting invalid tier price"""
        with pytest.raises(ValueError, match="Invalid tier"):
            TierValidator.get_tier_price("invalid")

    def test_get_tier_features_free(self):
        """Test getting free tier features"""
        features = TierValidator.get_tier_features("free")
        assert len(features) > 0
        assert "100 messages/month" in features

    def test_get_tier_features_pro(self):
        """Test getting pro tier features"""
        features = TierValidator.get_tier_features("pro")
        assert len(features) > 0
        assert "10,000 messages/month" in features

    def test_get_tier_features_enterprise(self):
        """Test getting enterprise tier features"""
        features = TierValidator.get_tier_features("enterprise")
        assert len(features) > 0
        assert "Unlimited messages" in features

    def test_get_tier_features_invalid(self):
        """Test getting invalid tier features"""
        with pytest.raises(ValueError, match="Invalid tier"):
            TierValidator.get_tier_features("invalid")

    def test_get_tier_name_free(self):
        """Test getting free tier name"""
        name = TierValidator.get_tier_name("free")
        assert name == "Free"

    def test_get_tier_name_pro(self):
        """Test getting pro tier name"""
        name = TierValidator.get_tier_name("pro")
        assert name == "Pro"

    def test_get_tier_name_enterprise(self):
        """Test getting enterprise tier name"""
        name = TierValidator.get_tier_name("enterprise")
        assert name == "Enterprise"

    def test_get_tier_name_invalid(self):
        """Test getting invalid tier name"""
        with pytest.raises(ValueError, match="Invalid tier"):
            TierValidator.get_tier_name("invalid")

    def test_get_tier_description_free(self):
        """Test getting free tier description"""
        desc = TierValidator.get_tier_description("free")
        assert "Free tier" in desc

    def test_get_tier_description_pro(self):
        """Test getting pro tier description"""
        desc = TierValidator.get_tier_description("pro")
        assert "Professional" in desc

    def test_get_tier_description_enterprise(self):
        """Test getting enterprise tier description"""
        desc = TierValidator.get_tier_description("enterprise")
        assert "Enterprise" in desc

    def test_get_tier_description_invalid(self):
        """Test getting invalid tier description"""
        with pytest.raises(ValueError, match="Invalid tier"):
            TierValidator.get_tier_description("invalid")

    def test_get_all_tiers(self):
        """Test getting all tiers"""
        tiers = TierValidator.get_all_tiers()
        assert len(tiers) == 3
        assert "free" in tiers
        assert "pro" in tiers
        assert "enterprise" in tiers


@pytest.mark.unit
class TestTierValidatorComparison:
    """Tests for TierValidator comparison methods"""

    def test_is_tier_upgrade_free_to_pro(self):
        """Test upgrade from free to pro"""
        assert TierValidator.is_tier_upgrade("free", "pro") is True

    def test_is_tier_upgrade_free_to_enterprise(self):
        """Test upgrade from free to enterprise"""
        assert TierValidator.is_tier_upgrade("free", "enterprise") is True

    def test_is_tier_upgrade_pro_to_enterprise(self):
        """Test upgrade from pro to enterprise"""
        assert TierValidator.is_tier_upgrade("pro", "enterprise") is True

    def test_is_tier_upgrade_same_tier(self):
        """Test upgrade to same tier"""
        assert TierValidator.is_tier_upgrade("free", "free") is False

    def test_is_tier_upgrade_downgrade(self):
        """Test upgrade that is actually downgrade"""
        assert TierValidator.is_tier_upgrade("pro", "free") is False

    def test_is_tier_upgrade_invalid_from(self):
        """Test upgrade with invalid from tier"""
        with pytest.raises(ValueError):
            TierValidator.is_tier_upgrade("invalid", "pro")

    def test_is_tier_upgrade_invalid_to(self):
        """Test upgrade with invalid to tier"""
        with pytest.raises(ValueError):
            TierValidator.is_tier_upgrade("free", "invalid")

    def test_is_tier_downgrade_pro_to_free(self):
        """Test downgrade from pro to free"""
        assert TierValidator.is_tier_downgrade("pro", "free") is True

    def test_is_tier_downgrade_enterprise_to_free(self):
        """Test downgrade from enterprise to free"""
        assert TierValidator.is_tier_downgrade("enterprise", "free") is True

    def test_is_tier_downgrade_enterprise_to_pro(self):
        """Test downgrade from enterprise to pro"""
        assert TierValidator.is_tier_downgrade("enterprise", "pro") is True

    def test_is_tier_downgrade_same_tier(self):
        """Test downgrade to same tier"""
        assert TierValidator.is_tier_downgrade("free", "free") is False

    def test_is_tier_downgrade_upgrade(self):
        """Test downgrade that is actually upgrade"""
        assert TierValidator.is_tier_downgrade("free", "pro") is False

    def test_is_tier_downgrade_invalid_from(self):
        """Test downgrade with invalid from tier"""
        with pytest.raises(ValueError):
            TierValidator.is_tier_downgrade("invalid", "free")

    def test_is_tier_downgrade_invalid_to(self):
        """Test downgrade with invalid to tier"""
        with pytest.raises(ValueError):
            TierValidator.is_tier_downgrade("pro", "invalid")

    def test_compare_tiers_free_pro(self):
        """Test comparing free and pro"""
        result = TierValidator.compare_tiers("free", "pro")
        assert result == -1

    def test_compare_tiers_pro_free(self):
        """Test comparing pro and free"""
        result = TierValidator.compare_tiers("pro", "free")
        assert result == 1

    def test_compare_tiers_same(self):
        """Test comparing same tier"""
        result = TierValidator.compare_tiers("free", "free")
        assert result == 0

    def test_compare_tiers_free_enterprise(self):
        """Test comparing free and enterprise"""
        result = TierValidator.compare_tiers("free", "enterprise")
        assert result == -1

    def test_compare_tiers_enterprise_pro(self):
        """Test comparing enterprise and pro"""
        result = TierValidator.compare_tiers("enterprise", "pro")
        assert result == 1

    def test_compare_tiers_invalid_from(self):
        """Test comparing with invalid from tier"""
        with pytest.raises(ValueError):
            TierValidator.compare_tiers("invalid", "pro")

    def test_compare_tiers_invalid_to(self):
        """Test comparing with invalid to tier"""
        with pytest.raises(ValueError):
            TierValidator.compare_tiers("free", "invalid")

