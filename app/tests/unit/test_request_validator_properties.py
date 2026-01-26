"""Property-based tests for Request Validator - Validates correctness properties"""

import pytest
from hypothesis import given, strategies as st
import hmac
import hashlib
import json
from app.core.request_validator import RequestValidator, ResponseValidator


@pytest.mark.property
class TestHMACSignatureProperties:
    """Property-based tests for HMAC signature validation"""

    @given(
        body=st.text(min_size=1, max_size=1000),
        secret=st.text(min_size=1, max_size=100),
    )
    def test_hmac_signature_is_deterministic(self, body, secret):
        """Validates: HMAC signature is deterministic
        
        Property: Same body and secret always produce same signature
        """
        # Act
        sig1 = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        sig2 = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Assert
        assert sig1 == sig2

    @given(
        body=st.text(min_size=1, max_size=1000),
        secret=st.text(min_size=1, max_size=100),
    )
    def test_hmac_signature_validation_accepts_valid_signature(self, body, secret):
        """Validates: Valid HMAC signature is accepted
        
        Property: validate_hmac_signature returns True for valid signature
        """
        # Arrange
        signature = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Act
        result = RequestValidator.validate_hmac_signature(body, signature, secret)
        
        # Assert
        assert result is True

    @given(
        body=st.text(min_size=1, max_size=1000),
        secret=st.text(min_size=1, max_size=100),
        wrong_body=st.text(min_size=1, max_size=1000),
    )
    def test_hmac_signature_validation_rejects_invalid_signature(self, body, secret, wrong_body):
        """Validates: Invalid HMAC signature is rejected
        
        Property: validate_hmac_signature returns False for invalid signature
        """
        # Arrange - create signature with different body
        if body == wrong_body:
            pytest.skip("Bodies are identical")
        
        signature = hmac.new(
            secret.encode(),
            wrong_body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Act
        result = RequestValidator.validate_hmac_signature(body, signature, secret)
        
        # Assert
        assert result is False

    @given(
        body=st.text(min_size=1, max_size=1000),
        secret=st.text(min_size=1, max_size=100),
    )
    def test_hmac_signature_is_hexadecimal(self, body, secret):
        """Validates: HMAC signature is valid hexadecimal string
        
        Property: Signature can be converted to bytes from hex
        """
        # Act
        signature = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Assert
        try:
            bytes.fromhex(signature)
        except ValueError:
            pytest.fail(f"Signature {signature} is not valid hexadecimal")


@pytest.mark.property
class TestJSONValidationProperties:
    """Property-based tests for JSON validation"""

    @given(
        data=st.dictionaries(st.text(min_size=1), st.text()),
    )
    def test_json_body_validation_accepts_valid_json(self, data):
        """Validates: Valid JSON is accepted
        
        Property: validate_json_body returns parsed dict for valid JSON
        """
        # Arrange
        body = json.dumps(data)
        
        # Act
        result = RequestValidator.validate_json_body(body)
        
        # Assert
        assert result == data

    @given(
        data=st.dictionaries(st.text(min_size=1), st.text()),
    )
    def test_json_roundtrip_preserves_data(self, data):
        """Validates: JSON roundtrip preserves data
        
        Property: json.loads(json.dumps(data)) == data
        """
        # Act
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        
        # Assert
        assert parsed == data


@pytest.mark.property
class TestStatusCodeValidationProperties:
    """Property-based tests for status code validation"""

    @given(
        status_code=st.integers(min_value=100, max_value=599),
    )
    def test_status_code_validation_accepts_valid_codes(self, status_code):
        """Validates: Valid HTTP status codes are accepted
        
        Property: validate_status_code returns True for 100-599
        """
        # Act
        result = ResponseValidator.validate_status_code(status_code)
        
        # Assert
        assert result is True

    @given(
        status_code=st.integers(max_value=99) | st.integers(min_value=600),
    )
    def test_status_code_validation_rejects_invalid_codes(self, status_code):
        """Validates: Invalid HTTP status codes are rejected
        
        Property: validate_status_code raises ValueError for invalid codes
        """
        # Act & Assert
        with pytest.raises(ValueError):
            ResponseValidator.validate_status_code(status_code)

    @given(
        status_code=st.sampled_from([200, 201, 204, 301, 302, 400, 401, 403, 404, 500, 502, 503]),
    )
    def test_status_code_validation_accepts_common_codes(self, status_code):
        """Validates: Common HTTP status codes are accepted
        
        Property: All common status codes are valid
        """
        # Act
        result = ResponseValidator.validate_status_code(status_code)
        
        # Assert
        assert result is True
