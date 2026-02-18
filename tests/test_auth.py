"""
Tests for authentication.
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.auth import get_current_user, AuthenticatedUser
from app.config import get_settings


def create_test_token(user_id: str = "test-user", role: str = "admin"):
    """Create a test JWT token."""
    settings = get_settings()
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@pytest.mark.asyncio
async def test_get_current_user_with_valid_token():
    """Test authentication with valid token."""
    token = create_test_token()
    
    # Mock request with token in query params
    class MockRequest:
        query_params = {"token": token}
        cookies = {}
    
    user = await get_current_user(MockRequest(), None)
    
    assert user.user_id == "test-user"
    assert user.role == "admin"
    assert "seminars:read" in user.permissions


@pytest.mark.asyncio
async def test_get_current_user_with_missing_token():
    """Test authentication with missing token."""
    from fastapi import HTTPException
    
    class MockRequest:
        query_params = {}
        cookies = {}
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(MockRequest(), None)
    
    assert exc_info.value.status_code == 401
