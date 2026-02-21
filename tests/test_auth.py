"""
Tests for authentication.
"""

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from jose import jwt

from app.main import get_current_user, settings


def create_test_token(user_id: str = "test-user", role: str = "admin"):
    """Create a test JWT token."""
    payload = {
        "sub": user_id,
        "id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=1),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


@pytest.mark.asyncio
async def test_get_current_user_with_valid_token():
    """Test authentication with valid token."""
    token = create_test_token()

    class MockRequest:
        query_params = {"token": token}
        cookies = {}
        method = "GET"
        url = type("URL", (), {"path": "/api/seminars"})()

    user = await get_current_user(MockRequest(), None, token, None)

    assert user["id"] == "test-user"


@pytest.mark.asyncio
async def test_get_current_user_with_missing_token():
    """Test authentication with missing token."""
    class MockRequest:
        query_params = {}
        cookies = {}
        method = "GET"
        url = type("URL", (), {"path": "/api/seminars"})()

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(MockRequest(), None, None, None)

    assert exc_info.value.status_code == 401
