"""Tier Validator - Validates tier configurations and provides tier information"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class TierType(str, Enum):
    """Supported tier types"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class TierInfo:
    """Information about a tier"""
    tier: TierType
    name: str
    description: str
    message_limit: int
    price_per_month: Optional[float] = None
    features: List[str] = None

    def __post_init__(self):
        """Initialize features list if not provided"""
        if self.features is None:
            self.features = []


class TierValidator:
    """Service for validating and managing tier configurations"""

    # Tier configurations
    TIER_CONFIGS = {
        TierType.FREE: TierInfo(
            tier=TierType.FREE,
            name="Free",
            description="Free tier with limited messages",
            message_limit=100,
            price_per_month=0.0,
            features=[
                "100 messages/month",
                "1 domain (Retail)",
                "1 channel (Telegram)",
                "Basic support",
            ]
        ),
        TierType.PRO: TierInfo(
            tier=TierType.PRO,
            name="Pro",
            description="Professional tier with more messages",
            message_limit=10000,
            price_per_month=99.0,
            features=[
                "10,000 messages/month",
                "All domains",
                "All channels",
                "Priority support",
                "Analytics",
            ]
        ),
        TierType.ENTERPRISE: TierInfo(
            tier=TierType.ENTERPRISE,
            name="Enterprise",
            description="Enterprise tier with unlimited messages",
            message_limit=999999999,
            price_per_month=None,
            features=[
                "Unlimited messages",
                "All domains",
                "All channels",
                "24/7 support",
                "Custom integrations",
                "SLA guarantee",
            ]
        ),
    }

    @staticmethod
    def validate_tier(tier: str) -> bool:
        """Validate if tier is valid"""
        try:
            TierType(tier)
            return True
        except ValueError:
            return False

    @staticmethod
    def get_tier_info(tier: str) -> Optional[TierInfo]:
        """Get tier information"""
        if not TierValidator.validate_tier(tier):
            return None

        tier_type = TierType(tier)
        return TierValidator.TIER_CONFIGS.get(tier_type)

    @staticmethod
    def get_tier_limit(tier: str) -> int:
        """Get message limit for tier"""
        info = TierValidator.get_tier_info(tier)
        if info is None:
            raise ValueError(f"Invalid tier: {tier}")
        return info.message_limit

    @staticmethod
    def get_tier_price(tier: str) -> Optional[float]:
        """Get price for tier"""
        info = TierValidator.get_tier_info(tier)
        if info is None:
            raise ValueError(f"Invalid tier: {tier}")
        return info.price_per_month

    @staticmethod
    def get_tier_features(tier: str) -> List[str]:
        """Get features for tier"""
        info = TierValidator.get_tier_info(tier)
        if info is None:
            raise ValueError(f"Invalid tier: {tier}")
        return info.features

    @staticmethod
    def get_all_tiers() -> Dict[str, TierInfo]:
        """Get all tier configurations"""
        return {tier.value: info for tier, info in TierValidator.TIER_CONFIGS.items()}

    @staticmethod
    def is_tier_upgrade(from_tier: str, to_tier: str) -> bool:
        """Check if upgrade is valid (from lower to higher tier)"""
        if not TierValidator.validate_tier(from_tier) or not TierValidator.validate_tier(to_tier):
            raise ValueError("Invalid tier")

        tier_order = [TierType.FREE, TierType.PRO, TierType.ENTERPRISE]
        from_idx = tier_order.index(TierType(from_tier))
        to_idx = tier_order.index(TierType(to_tier))

        return to_idx > from_idx

    @staticmethod
    def is_tier_downgrade(from_tier: str, to_tier: str) -> bool:
        """Check if downgrade is valid (from higher to lower tier)"""
        if not TierValidator.validate_tier(from_tier) or not TierValidator.validate_tier(to_tier):
            raise ValueError("Invalid tier")

        tier_order = [TierType.FREE, TierType.PRO, TierType.ENTERPRISE]
        from_idx = tier_order.index(TierType(from_tier))
        to_idx = tier_order.index(TierType(to_tier))

        return to_idx < from_idx

    @staticmethod
    def get_tier_name(tier: str) -> str:
        """Get display name for tier"""
        info = TierValidator.get_tier_info(tier)
        if info is None:
            raise ValueError(f"Invalid tier: {tier}")
        return info.name

    @staticmethod
    def get_tier_description(tier: str) -> str:
        """Get description for tier"""
        info = TierValidator.get_tier_info(tier)
        if info is None:
            raise ValueError(f"Invalid tier: {tier}")
        return info.description

    @staticmethod
    def compare_tiers(tier1: str, tier2: str) -> int:
        """Compare two tiers. Returns -1 if tier1 < tier2, 0 if equal, 1 if tier1 > tier2"""
        if not TierValidator.validate_tier(tier1) or not TierValidator.validate_tier(tier2):
            raise ValueError("Invalid tier")

        tier_order = [TierType.FREE, TierType.PRO, TierType.ENTERPRISE]
        idx1 = tier_order.index(TierType(tier1))
        idx2 = tier_order.index(TierType(tier2))

        if idx1 < idx2:
            return -1
        elif idx1 > idx2:
            return 1
        else:
            return 0

