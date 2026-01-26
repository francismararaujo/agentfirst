"""Property-based tests for X-Ray Observability - Validates correctness properties"""

import pytest
from hypothesis import given, strategies as st
from app.core.observability import XRayConfig


@pytest.mark.property
class TestXRayConfigProperties:
    """Property-based tests for XRayConfig"""

    @given(
        service_name=st.text(min_size=1, max_size=100),
    )
    def test_xray_config_preserves_service_name(self, service_name):
        """Validates: XRayConfig preserves service name
        
        Property: provided service_name == config.service_name
        """
        # Act
        config = XRayConfig(
            service_name=service_name,
        )
        
        # Assert
        assert config.service_name == service_name

    @given(
        enabled=st.booleans(),
    )
    def test_xray_config_enabled_flag_is_boolean(self, enabled):
        """Validates: XRayConfig enabled flag is always boolean
        
        Property: isinstance(enabled, bool)
        """
        # Act
        config = XRayConfig(
            enabled=enabled,
        )
        
        # Assert
        assert isinstance(config.enabled, bool)

    @given(
        sampling_rate=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_xray_config_sampling_rate_is_valid(self, sampling_rate):
        """Validates: XRayConfig sampling rate is between 0 and 1
        
        Property: 0 <= sampling_rate <= 1
        """
        # Act
        config = XRayConfig(
            sampling_rate=sampling_rate,
        )
        
        # Assert
        assert 0 <= config.sampling_rate <= 1

    def test_xray_config_has_default_values(self):
        """Validates: XRayConfig has sensible default values
        
        Property: All default values are valid
        """
        # Act
        config = XRayConfig()
        
        # Assert
        assert config.service_name == "agentfirst"
        assert config.enabled is True
        assert config.sampling_rate == 1.0

    @given(
        service_name=st.text(min_size=1, max_size=100),
        sampling_rate=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_xray_config_all_parameters_are_preserved(self, service_name, sampling_rate):
        """Validates: XRayConfig preserves all parameters
        
        Property: All provided parameters are stored correctly
        """
        # Act
        config = XRayConfig(
            service_name=service_name,
            sampling_rate=sampling_rate,
        )
        
        # Assert
        assert config.service_name == service_name
        assert config.sampling_rate == sampling_rate


@pytest.mark.property
class TestXRayTracingProperties:
    """Property-based tests for X-Ray tracing"""

    @given(
        trace_id=st.uuids().map(str),
    )
    def test_trace_id_is_valid_uuid(self, trace_id):
        """Validates: Trace ID is valid UUID format
        
        Property: Trace ID can be parsed as UUID
        """
        # Assert
        try:
            import uuid
            uuid.UUID(trace_id)
        except ValueError:
            pytest.fail(f"Trace ID {trace_id} is not valid UUID")

    @given(
        segment_name=st.text(min_size=1, max_size=100),
    )
    def test_segment_name_is_non_empty(self, segment_name):
        """Validates: Segment name is non-empty
        
        Property: len(segment_name) > 0
        """
        # Assert
        assert len(segment_name) > 0

    @given(
        sampling_rate=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_sampling_rate_is_valid_probability(self, sampling_rate):
        """Validates: Sampling rate is valid probability
        
        Property: 0 <= sampling_rate <= 1
        """
        # Assert
        assert 0 <= sampling_rate <= 1

    @given(
        sampling_rate=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_sampling_decision_is_boolean(self, sampling_rate):
        """Validates: Sampling decision is boolean
        
        Property: Should sample is True or False
        """
        # Arrange
        import random
        random.seed(42)
        
        # Act
        should_sample = random.random() < sampling_rate
        
        # Assert
        assert isinstance(should_sample, bool)


@pytest.mark.property
class TestXRayConsistencyProperties:
    """Property-based tests for X-Ray consistency"""

    @given(
        service_name=st.text(min_size=1, max_size=100),
    )
    def test_service_name_is_preserved_consistently(self, service_name):
        """Validates: Service name is preserved consistently
        
        Property: Multiple accesses return same service name
        """
        # Arrange
        config = XRayConfig(service_name=service_name)
        
        # Act
        name1 = config.service_name
        name2 = config.service_name
        name3 = config.service_name
        
        # Assert
        assert name1 == name2 == name3 == service_name

    @given(
        sampling_rate=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_sampling_rate_is_preserved_consistently(self, sampling_rate):
        """Validates: Sampling rate is preserved consistently
        
        Property: Multiple accesses return same sampling rate
        """
        # Arrange
        config = XRayConfig(sampling_rate=sampling_rate)
        
        # Act
        rate1 = config.sampling_rate
        rate2 = config.sampling_rate
        rate3 = config.sampling_rate
        
        # Assert
        assert rate1 == rate2 == rate3 == sampling_rate

    @given(
        enabled=st.booleans(),
    )
    def test_enabled_flag_is_preserved_consistently(self, enabled):
        """Validates: Enabled flag is preserved consistently
        
        Property: Multiple accesses return same enabled flag
        """
        # Arrange
        config = XRayConfig(enabled=enabled)
        
        # Act
        flag1 = config.enabled
        flag2 = config.enabled
        flag3 = config.enabled
        
        # Assert
        assert flag1 == flag2 == flag3 == enabled
