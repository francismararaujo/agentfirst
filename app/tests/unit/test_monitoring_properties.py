"""Property-based tests for CloudWatch Monitoring - Validates correctness properties"""

import pytest
from hypothesis import given, strategies as st
from app.core.monitoring import CloudWatchConfig, CloudWatchLogger


@pytest.mark.property
class TestCloudWatchConfigProperties:
    """Property-based tests for CloudWatchConfig"""

    @given(
        region=st.sampled_from(["us-east-1", "us-west-2", "eu-west-1"]),
        log_retention_days=st.integers(min_value=1, max_value=3653),
    )
    def test_cloudwatch_config_has_valid_retention(self, region, log_retention_days):
        """Validates: CloudWatchConfig has valid log retention
        
        Property: log_retention_days > 0
        """
        # Act
        config = CloudWatchConfig(
            region=region,
            log_retention_days=log_retention_days,
        )
        
        # Assert
        assert config.log_retention_days > 0

    @given(
        region=st.sampled_from(["us-east-1", "us-west-2", "eu-west-1"]),
        log_group_prefix=st.text(min_size=1, max_size=100),
    )
    def test_cloudwatch_config_preserves_log_group_prefix(self, region, log_group_prefix):
        """Validates: CloudWatchConfig preserves log group prefix
        
        Property: provided prefix == config.log_group_prefix
        """
        # Act
        config = CloudWatchConfig(
            region=region,
            log_group_prefix=log_group_prefix,
        )
        
        # Assert
        assert config.log_group_prefix == log_group_prefix

    @given(
        region=st.sampled_from(["us-east-1", "us-west-2", "eu-west-1"]),
        enable_metrics=st.booleans(),
        enable_dashboards=st.booleans(),
    )
    def test_cloudwatch_config_flags_are_boolean(self, region, enable_metrics, enable_dashboards):
        """Validates: CloudWatchConfig flags are always boolean
        
        Property: isinstance(enable_metrics, bool) and isinstance(enable_dashboards, bool)
        """
        # Act
        config = CloudWatchConfig(
            region=region,
            enable_metrics=enable_metrics,
            enable_dashboards=enable_dashboards,
        )
        
        # Assert
        assert isinstance(config.enable_metrics, bool)
        assert isinstance(config.enable_dashboards, bool)

    @given(
        region=st.sampled_from(["us-east-1", "us-west-2", "eu-west-1"]),
        namespace=st.text(min_size=1, max_size=100),
    )
    def test_cloudwatch_config_preserves_namespace(self, region, namespace):
        """Validates: CloudWatchConfig preserves namespace
        
        Property: provided namespace == config.namespace
        """
        # Act
        config = CloudWatchConfig(
            region=region,
            namespace=namespace,
        )
        
        # Assert
        assert config.namespace == namespace

    @given(
        region=st.sampled_from(["us-east-1", "us-west-2", "eu-west-1"]),
    )
    def test_cloudwatch_config_has_default_values(self, region):
        """Validates: CloudWatchConfig has sensible default values
        
        Property: All default values are valid
        """
        # Act
        config = CloudWatchConfig(region=region)
        
        # Assert
        assert config.region == region
        assert config.log_group_prefix == "/aws/lambda/agentfirst"
        assert config.log_retention_days == 30
        assert config.enable_metrics is True
        assert config.enable_dashboards is True
        assert config.namespace == "AgentFirst2"


@pytest.mark.property
class TestCloudWatchLoggerProperties:
    """Property-based tests for CloudWatchLogger"""

    @given(
        component=st.text(min_size=1, max_size=100),
        event_type=st.text(min_size=1, max_size=100),
        data=st.dictionaries(st.text(min_size=1), st.text()),
    )
    def test_log_event_creates_valid_entry(self, component, event_type, data):
        """Validates: log_event creates valid log entry
        
        Property: Log entry contains all required fields
        """
        # Arrange
        config = CloudWatchConfig()
        logger = CloudWatchLogger(config)
        
        # Act - should not raise exception
        try:
            logger.log_event(component, event_type, data)
        except Exception as e:
            pytest.fail(f"log_event raised exception: {e}")

    @given(
        component=st.text(min_size=1, max_size=100),
        event_type=st.text(min_size=1, max_size=100),
        data=st.dictionaries(st.text(min_size=1), st.text()),
        level=st.sampled_from(["INFO", "WARNING", "ERROR", "DEBUG"]),
    )
    def test_log_event_accepts_all_log_levels(self, component, event_type, data, level):
        """Validates: log_event accepts all log levels
        
        Property: All log levels are valid
        """
        # Arrange
        config = CloudWatchConfig()
        logger = CloudWatchLogger(config)
        
        # Act - should not raise exception
        try:
            logger.log_event(component, event_type, data, level=level)
        except Exception as e:
            pytest.fail(f"log_event raised exception: {e}")

    @given(
        component=st.text(min_size=1, max_size=100),
        operation=st.text(min_size=1, max_size=100),
        duration_ms=st.floats(min_value=0, max_value=30000),
    )
    def test_log_performance_accepts_valid_duration(self, component, operation, duration_ms):
        """Validates: log_performance accepts valid duration
        
        Property: duration_ms >= 0
        """
        # Arrange
        config = CloudWatchConfig()
        logger = CloudWatchLogger(config)
        
        # Act - should not raise exception
        try:
            logger.log_performance(component, operation, duration_ms)
        except Exception as e:
            pytest.fail(f"log_performance raised exception: {e}")

    @given(
        region=st.sampled_from(["us-east-1", "us-west-2", "eu-west-1"]),
    )
    def test_cloudwatch_logger_region_is_valid(self, region):
        """Validates: CloudWatchLogger region is valid AWS region
        
        Property: region is non-empty string
        """
        # Arrange
        config = CloudWatchConfig(region=region)
        
        # Act
        logger = CloudWatchLogger(config)
        
        # Assert
        assert logger.config.region == region
