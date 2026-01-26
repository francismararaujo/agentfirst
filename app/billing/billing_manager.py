"""Billing Manager - Manages billing operations and tier updates"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum
from app.billing.tier_validator import TierValidator, TierType
from app.billing.usage_tracker import UsageTracker
from app.billing.limit_enforcer import LimitEnforcer


class BillingStatus(str, Enum):
    """Billing status types"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIAL = "trial"
    SUSPENDED = "suspended"


@dataclass
class BillingInfo:
    """Billing information for a user"""
    email: str
    tier: str
    status: BillingStatus
    messages_used: int
    messages_limit: int
    messages_remaining: int
    upgrade_url: Optional[str] = None
    trial_ends_at: Optional[str] = None


class BillingManagerConfig:
    """Configuration for Billing Manager"""

    def __init__(
        self,
        upgrade_base_url: str = "https://agentfirst.com/upgrade",
        trial_duration_days: int = 14,
    ):
        """Initialize billing manager config"""
        self.upgrade_base_url = upgrade_base_url
        self.trial_duration_days = trial_duration_days


class BillingManager:
    """Service for managing billing operations"""

    def __init__(
        self,
        usage_tracker: UsageTracker,
        limit_enforcer: LimitEnforcer,
        config: Optional[BillingManagerConfig] = None,
    ):
        """Initialize billing manager"""
        self.usage_tracker = usage_tracker
        self.limit_enforcer = limit_enforcer
        self.config = config or BillingManagerConfig()

    async def get_billing_info(self, email: str) -> BillingInfo:
        """Get billing information for a user"""
        # Get tier
        tier = await self.usage_tracker.get_user_tier(email)

        # Get usage
        usage = await self.usage_tracker.get_usage(email)
        messages_used = usage.message_count if usage else 0

        # Get limit
        messages_limit = TierValidator.get_tier_limit(tier)

        # Calculate remaining
        messages_remaining = max(0, messages_limit - messages_used)

        # Determine status
        status = self._determine_status(tier, messages_remaining)

        # Generate upgrade URL if needed
        upgrade_url = None
        if tier != TierType.ENTERPRISE.value:
            upgrade_url = self._generate_upgrade_url(email, tier)

        return BillingInfo(
            email=email,
            tier=tier,
            status=status,
            messages_used=messages_used,
            messages_limit=messages_limit,
            messages_remaining=messages_remaining,
            upgrade_url=upgrade_url,
        )

    async def check_tier_and_limits(self, email: str) -> Dict[str, Any]:
        """Check tier and limits for a user"""
        billing_info = await self.get_billing_info(email)

        return {
            "email": email,
            "tier": billing_info.tier,
            "status": billing_info.status.value,
            "messages_used": billing_info.messages_used,
            "messages_limit": billing_info.messages_limit,
            "messages_remaining": billing_info.messages_remaining,
            "can_send_messages": billing_info.messages_remaining > 0,
            "upgrade_url": billing_info.upgrade_url,
        }

    async def generate_upgrade_link(self, email: str, target_tier: str) -> str:
        """Generate upgrade link for a user"""
        # Validate target tier
        if not TierValidator.validate_tier(target_tier):
            raise ValueError(f"Invalid tier: {target_tier}")

        # Get current tier
        current_tier = await self.usage_tracker.get_user_tier(email)

        # Check if upgrade is valid
        if not TierValidator.is_tier_upgrade(current_tier, target_tier):
            raise ValueError(
                f"Cannot upgrade from {current_tier} to {target_tier}"
            )

        # Generate upgrade URL
        return self._generate_upgrade_url(email, target_tier)

    async def update_tier_after_payment(
        self, email: str, new_tier: str, payment_id: str
    ) -> Dict[str, Any]:
        """Update tier after payment"""
        # Validate new tier
        if not TierValidator.validate_tier(new_tier):
            raise ValueError(f"Invalid tier: {new_tier}")

        # Get current tier
        current_tier = await self.usage_tracker.get_user_tier(email)

        # Check if upgrade is valid
        if not TierValidator.is_tier_upgrade(current_tier, new_tier):
            raise ValueError(
                f"Cannot upgrade from {current_tier} to {new_tier}"
            )

        # Update tier in usage tracker
        await self.usage_tracker.update_user_tier(email, new_tier)

        # Get updated billing info
        billing_info = await self.get_billing_info(email)

        return {
            "email": email,
            "previous_tier": current_tier,
            "new_tier": new_tier,
            "payment_id": payment_id,
            "status": "success",
            "billing_info": {
                "tier": billing_info.tier,
                "messages_limit": billing_info.messages_limit,
                "messages_remaining": billing_info.messages_remaining,
            },
        }

    def _determine_status(self, tier: str, messages_remaining: int) -> BillingStatus:
        """Determine billing status"""
        if tier == TierType.FREE.value:
            if messages_remaining > 0:
                return BillingStatus.TRIAL
            else:
                return BillingStatus.SUSPENDED
        else:
            if messages_remaining > 0:
                return BillingStatus.ACTIVE
            else:
                return BillingStatus.SUSPENDED

    def _generate_upgrade_url(self, email: str, tier: str) -> str:
        """Generate upgrade URL for a user"""
        return f"{self.config.upgrade_base_url}?email={email}&tier={tier}"
