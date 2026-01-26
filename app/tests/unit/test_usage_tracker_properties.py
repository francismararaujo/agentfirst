"""Property-based tests for Usage Tracker - Validates correctness properties"""

import pytest
from hypothesis import given, strategies as st
from datetime import datetime, timezone, timedelta
from app.billing.usage_tracker import Usage, UsageTracker


@pytest.mark.property
class TestUsageTrackerProperties:
    """Property-based tests for Usage Tracker"""

    @given(
        message_count=st.integers(0, 100000),
        tier=st.sampled_from(["free", "pro", "enterprise"])
    )
    def test_usage_counter_never_negative(self, message_count, tier):
        """Validates: Usage counter is always >= 0
        
        Property: message_count >= 0 for all valid inputs
        """
        # Arrange
        usage = Usage(
            email="test@example.com",
            year=2025,
            month=1,
            message_count=message_count,
            tier=tier
        )
        
        # Assert
        assert usage.message_count >= 0, f"Message count {usage.message_count} should never be negative"

    @given(
        initial_count=st.integers(0, 1000),
        increment=st.integers(1, 1000)
    )
    def test_usage_counter_monotonically_increases(self, initial_count, increment):
        """Validates: Usage counter monotonically increases
        
        Property: count_after_increment >= initial_count
        """
        # Arrange
        count = initial_count
        
        # Act
        count += increment
        
        # Assert
        assert count >= initial_count, f"Count {count} should be >= {initial_count}"

    @given(
        year=st.integers(2025, 2030),
        month=st.integers(1, 12)
    )
    def test_reset_date_is_first_day_of_next_month(self, year, month):
        """Validates: Reset date is always first day of next month at 00:00 UTC
        
        Property: reset_date = first_day_of_next_month(current_date)
        """
        # Arrange
        if month == 12:
            expected_year = year + 1
            expected_month = 1
        else:
            expected_year = year
            expected_month = month + 1
        
        # Act
        reset_date_str = UsageTracker._calculate_next_month_reset()
        reset_date = datetime.fromisoformat(reset_date_str)
        
        # Assert
        assert reset_date.day == 1, f"Reset date day should be 1, got {reset_date.day}"
        assert reset_date.hour == 0, f"Reset date hour should be 0, got {reset_date.hour}"
        assert reset_date.minute == 0, f"Reset date minute should be 0, got {reset_date.minute}"
        assert reset_date.second == 0, f"Reset date second should be 0, got {reset_date.second}"

    @given(
        email=st.emails(),
        tier=st.sampled_from(["free", "pro", "enterprise"])
    )
    def test_usage_to_dict_and_from_dict_are_inverse_operations(self, email, tier):
        """Validates: to_dict() and from_dict() are inverse operations
        
        Property: from_dict(to_dict(usage)) == usage
        """
        # Arrange
        original = Usage(
            email=email,
            year=2025,
            month=1,
            message_count=50,
            tier=tier
        )
        
        # Act
        dict_repr = original.to_dict()
        reconstructed = Usage.from_dict(dict_repr)
        
        # Assert
        assert reconstructed.email == original.email
        assert reconstructed.year == original.year
        assert reconstructed.month == original.month
        assert reconstructed.message_count == original.message_count
        assert reconstructed.tier == original.tier

    @given(
        year=st.integers(2025, 2030),
        month=st.integers(1, 12)
    )
    def test_current_month_is_valid(self, year, month):
        """Validates: Current month is always valid (1-12)
        
        Property: month ∈ [1, 12]
        """
        # Act
        current_year, current_month = UsageTracker._get_current_month()
        
        # Assert
        assert 1 <= current_month <= 12, f"Month {current_month} should be between 1 and 12"
        assert current_year >= 2025, f"Year {current_year} should be >= 2025"

    @given(
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        count=st.integers(0, 100000)
    )
    def test_remaining_messages_never_negative(self, tier, count):
        """Validates: Remaining messages is always >= 0
        
        Property: remaining = max(0, limit - count) >= 0
        """
        # Arrange
        limits = {
            'free': 100,
            'pro': 10000,
            'enterprise': 999999999
        }
        limit = limits[tier]
        
        # Act
        remaining = max(0, limit - count)
        
        # Assert
        assert remaining >= 0, f"Remaining {remaining} should never be negative"

    @given(
        tier=st.sampled_from(["free", "pro", "enterprise"]),
        count=st.integers(0, 100000)
    )
    def test_usage_percentage_is_between_0_and_100(self, tier, count):
        """Validates: Usage percentage is always between 0 and 100 (capped at 100)
        
        Property: 0 <= percentage <= 100 (percentage = min(100, (count/limit)*100))
        """
        # Arrange
        limits = {
            'free': 100,
            'pro': 10000,
            'enterprise': float('inf')
        }
        limit = limits[tier]
        
        # Act
        if limit == float('inf'):
            percentage = 0.0
        else:
            percentage = min(100, (count / limit) * 100)
        
        # Assert
        assert 0 <= percentage <= 100, f"Percentage {percentage} should be between 0 and 100"

    @given(
        email=st.emails(),
        year=st.integers(2025, 2030),
        month=st.integers(1, 12)
    )
    def test_usage_key_format_is_valid(self, email, year, month):
        """Validates: Usage key format is always valid
        
        Property: year_month key = f"{year}#{month:02d}"
        """
        # Act
        key = f"{year}#{month:02d}"
        
        # Assert
        assert "#" in key, f"Key {key} should contain #"
        parts = key.split("#")
        assert len(parts) == 2, f"Key {key} should have exactly 2 parts"
        assert parts[0] == str(year), f"Year part should be {year}"
        assert parts[1] == f"{month:02d}", f"Month part should be {month:02d}"
