"""Request/Response validation for AgentFirst2 MVP

This module provides request and response validation for API endpoints,
including HMAC signature validation for webhooks.
"""

import hmac
import hashlib
import json
import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, ValidationError
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class RequestValidator:
    """Validates incoming requests and webhook signatures"""

    @staticmethod
    def validate_hmac_signature(
        body: str,
        signature: str,
        secret: str,
        algorithm: str = "sha256"
    ) -> bool:
        """
        Validate HMAC signature for webhook requests

        Args:
            body: Request body as string
            signature: Signature from request header
            secret: Secret key for HMAC
            algorithm: HMAC algorithm (default: sha256)

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Compute expected signature
            expected_signature = hmac.new(
                secret.encode(),
                body.encode(),
                getattr(hashlib, algorithm)
            ).hexdigest()

            # Compare signatures (constant-time comparison)
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error validating HMAC signature: {str(e)}")
            return False

    @staticmethod
    def validate_json_body(body: str) -> Dict[str, Any]:
        """
        Validate and parse JSON body

        Args:
            body: Request body as string

        Returns:
            Parsed JSON body

        Raises:
            HTTPException: If JSON is invalid
        """
        try:
            return json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON body: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON body"
            )

    @staticmethod
    def validate_model(data: Dict[str, Any], model: type) -> BaseModel:
        """
        Validate data against Pydantic model

        Args:
            data: Data to validate
            model: Pydantic model class

        Returns:
            Validated model instance

        Raises:
            HTTPException: If validation fails
        """
        try:
            return model(**data)
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.errors()
            )

    @staticmethod
    def validate_required_headers(
        headers: Dict[str, str],
        required_headers: list
    ) -> bool:
        """
        Validate that required headers are present

        Args:
            headers: Request headers
            required_headers: List of required header names

        Returns:
            True if all required headers are present

        Raises:
            HTTPException: If required headers are missing
        """
        missing_headers = [
            h for h in required_headers
            if h.lower() not in {k.lower(): v for k, v in headers.items()}
        ]

        if missing_headers:
            logger.error(f"Missing required headers: {missing_headers}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required headers: {', '.join(missing_headers)}"
            )

        return True

    @staticmethod
    def validate_content_type(
        content_type: Optional[str],
        expected_type: str = "application/json"
    ) -> bool:
        """
        Validate Content-Type header

        Args:
            content_type: Content-Type header value
            expected_type: Expected content type

        Returns:
            True if content type matches

        Raises:
            HTTPException: If content type doesn't match
        """
        if not content_type or expected_type not in content_type:
            logger.error(f"Invalid Content-Type: {content_type}")
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Content-Type must be {expected_type}"
            )

        return True


class ResponseValidator:
    """Validates outgoing responses"""

    @staticmethod
    def validate_response_model(data: Dict[str, Any], model: type) -> BaseModel:
        """
        Validate response data against Pydantic model

        Args:
            data: Response data
            model: Pydantic model class

        Returns:
            Validated model instance

        Raises:
            ValueError: If validation fails
        """
        try:
            return model(**data)
        except ValidationError as e:
            logger.error(f"Response validation error: {str(e)}")
            raise ValueError(f"Invalid response: {str(e)}")

    @staticmethod
    def validate_status_code(status_code: int) -> bool:
        """
        Validate HTTP status code

        Args:
            status_code: HTTP status code

        Returns:
            True if status code is valid

        Raises:
            ValueError: If status code is invalid
        """
        if not (100 <= status_code < 600):
            raise ValueError(f"Invalid status code: {status_code}")

        return True
