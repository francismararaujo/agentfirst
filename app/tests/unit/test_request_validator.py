"""Unit tests for request validator - Test HMAC validation, JSON parsing, and model validation"""

import pytest
import json
import hmac
import hashlib
from pydantic import BaseModel
from fastapi import HTTPException
from app.core.request_validator import RequestValidator, ResponseValidator


class SampleModel(BaseModel):
    """Sample Pydantic model for testing"""
    name: str
    email: str
    age: int


@pytest.mark.unit
class TestRequestValidatorHMAC:
    """Tests for HMAC signature validation"""

    def test_validate_hmac_signature_valid(self):
        """Test validating a valid HMAC signature"""
        body = "test body"
        secret = "test_secret"

        # Generate valid signature
        signature = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        result = RequestValidator.validate_hmac_signature(body, signature, secret)
        assert result is True

    def test_validate_hmac_signature_invalid(self):
        """Test validating an invalid HMAC signature"""
        body = "test body"
        secret = "test_secret"
        invalid_signature = "invalid_signature"

        result = RequestValidator.validate_hmac_signature(body, invalid_signature, secret)
        assert result is False

    def test_validate_hmac_signature_wrong_secret(self):
        """Test validating with wrong secret"""
        body = "test body"
        secret = "test_secret"
        wrong_secret = "wrong_secret"

        # Generate signature with correct secret
        signature = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        # Validate with wrong secret
        result = RequestValidator.validate_hmac_signature(body, signature, wrong_secret)
        assert result is False

    def test_validate_hmac_signature_different_algorithms(self):
        """Test HMAC validation with different algorithms"""
        body = "test body"
        secret = "test_secret"

        # Test with SHA256 (default)
        signature_sha256 = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        result = RequestValidator.validate_hmac_signature(
            body, signature_sha256, secret, algorithm="sha256"
        )
        assert result is True

        # Test with SHA1
        signature_sha1 = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha1
        ).hexdigest()

        result = RequestValidator.validate_hmac_signature(
            body, signature_sha1, secret, algorithm="sha1"
        )
        assert result is True


@pytest.mark.unit
class TestRequestValidatorJSON:
    """Tests for JSON body validation"""

    def test_validate_json_body_valid(self):
        """Test validating valid JSON body"""
        body = '{"name": "John", "email": "john@example.com"}'

        result = RequestValidator.validate_json_body(body)

        assert result["name"] == "John"
        assert result["email"] == "john@example.com"

    def test_validate_json_body_invalid(self):
        """Test validating invalid JSON body"""
        body = "invalid json"

        with pytest.raises(HTTPException) as exc_info:
            RequestValidator.validate_json_body(body)

        assert exc_info.value.status_code == 400

    def test_validate_json_body_empty(self):
        """Test validating empty JSON body"""
        body = "{}"

        result = RequestValidator.validate_json_body(body)

        assert result == {}

    def test_validate_json_body_complex(self):
        """Test validating complex JSON body"""
        body = json.dumps({
            "user": {
                "name": "John",
                "email": "john@example.com"
            },
            "items": [1, 2, 3],
            "active": True
        })

        result = RequestValidator.validate_json_body(body)

        assert result["user"]["name"] == "John"
        assert result["items"] == [1, 2, 3]
        assert result["active"] is True


@pytest.mark.unit
class TestRequestValidatorModel:
    """Tests for Pydantic model validation"""

    def test_validate_model_valid(self):
        """Test validating valid data against model"""
        data = {
            "name": "John",
            "email": "john@example.com",
            "age": 30
        }

        result = RequestValidator.validate_model(data, SampleModel)

        assert isinstance(result, SampleModel)
        assert result.name == "John"
        assert result.email == "john@example.com"
        assert result.age == 30

    def test_validate_model_missing_field(self):
        """Test validating data with missing required field"""
        data = {
            "name": "John",
            "email": "john@example.com"
            # Missing 'age'
        }

        with pytest.raises(HTTPException) as exc_info:
            RequestValidator.validate_model(data, SampleModel)

        assert exc_info.value.status_code == 422

    def test_validate_model_invalid_type(self):
        """Test validating data with invalid type"""
        data = {
            "name": "John",
            "email": "john@example.com",
            "age": "thirty"  # Should be int
        }

        with pytest.raises(HTTPException) as exc_info:
            RequestValidator.validate_model(data, SampleModel)

        assert exc_info.value.status_code == 422

    def test_validate_model_extra_fields(self):
        """Test validating data with extra fields"""
        data = {
            "name": "John",
            "email": "john@example.com",
            "age": 30,
            "extra_field": "extra_value"
        }

        result = RequestValidator.validate_model(data, SampleModel)

        assert isinstance(result, SampleModel)
        assert result.name == "John"


@pytest.mark.unit
class TestRequestValidatorHeaders:
    """Tests for header validation"""

    def test_validate_required_headers_present(self):
        """Test validating when all required headers are present"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer token"
        }
        required_headers = ["Content-Type", "Authorization"]

        result = RequestValidator.validate_required_headers(headers, required_headers)

        assert result is True

    def test_validate_required_headers_missing(self):
        """Test validating when required headers are missing"""
        headers = {
            "Content-Type": "application/json"
        }
        required_headers = ["Content-Type", "Authorization"]

        with pytest.raises(HTTPException) as exc_info:
            RequestValidator.validate_required_headers(headers, required_headers)

        assert exc_info.value.status_code == 400

    def test_validate_required_headers_case_insensitive(self):
        """Test that header validation is case-insensitive"""
        headers = {
            "content-type": "application/json",
            "authorization": "Bearer token"
        }
        required_headers = ["Content-Type", "Authorization"]

        result = RequestValidator.validate_required_headers(headers, required_headers)

        assert result is True

    def test_validate_required_headers_empty(self):
        """Test validating with no required headers"""
        headers = {"Content-Type": "application/json"}
        required_headers = []

        result = RequestValidator.validate_required_headers(headers, required_headers)

        assert result is True


@pytest.mark.unit
class TestRequestValidatorContentType:
    """Tests for Content-Type validation"""

    def test_validate_content_type_valid(self):
        """Test validating valid Content-Type"""
        content_type = "application/json"

        result = RequestValidator.validate_content_type(content_type)

        assert result is True

    def test_validate_content_type_with_charset(self):
        """Test validating Content-Type with charset"""
        content_type = "application/json; charset=utf-8"

        result = RequestValidator.validate_content_type(content_type)

        assert result is True

    def test_validate_content_type_invalid(self):
        """Test validating invalid Content-Type"""
        content_type = "text/html"

        with pytest.raises(HTTPException) as exc_info:
            RequestValidator.validate_content_type(content_type)

        assert exc_info.value.status_code == 415

    def test_validate_content_type_none(self):
        """Test validating None Content-Type"""
        content_type = None

        with pytest.raises(HTTPException) as exc_info:
            RequestValidator.validate_content_type(content_type)

        assert exc_info.value.status_code == 415

    def test_validate_content_type_custom_expected(self):
        """Test validating with custom expected Content-Type"""
        content_type = "text/plain"

        result = RequestValidator.validate_content_type(content_type, "text/plain")

        assert result is True


@pytest.mark.unit
class TestResponseValidator:
    """Tests for response validation"""

    def test_validate_response_model_valid(self):
        """Test validating valid response model"""
        data = {
            "name": "John",
            "email": "john@example.com",
            "age": 30
        }

        result = ResponseValidator.validate_response_model(data, SampleModel)

        assert isinstance(result, SampleModel)
        assert result.name == "John"

    def test_validate_response_model_invalid(self):
        """Test validating invalid response model"""
        data = {
            "name": "John",
            "email": "john@example.com"
            # Missing 'age'
        }

        with pytest.raises(ValueError):
            ResponseValidator.validate_response_model(data, SampleModel)

    def test_validate_status_code_valid(self):
        """Test validating valid status codes"""
        assert ResponseValidator.validate_status_code(200) is True
        assert ResponseValidator.validate_status_code(404) is True
        assert ResponseValidator.validate_status_code(500) is True

    def test_validate_status_code_invalid_low(self):
        """Test validating status code too low"""
        with pytest.raises(ValueError):
            ResponseValidator.validate_status_code(99)

    def test_validate_status_code_invalid_high(self):
        """Test validating status code too high"""
        with pytest.raises(ValueError):
            ResponseValidator.validate_status_code(600)
