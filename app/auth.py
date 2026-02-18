"""
JWT Authentication for unified auth system.
"""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import get_settings, ROLE_PERMISSIONS

security = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    """User authenticated via JWT from auth-service."""
    user_id: str  # JWT 'sub' claim
    role: str     # Custom claim
    permissions: list[str]
    authenticated_at: datetime


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthenticatedUser:
    """
    Validate JWT token from auth-service.
    
    Supports:
    - Query parameter: ?token=xxx
    - Authorization header: Bearer xxx
    - Cookie: token=xxx
    """
    settings = get_settings()
    token = None
    
    # Try query parameter (primary method for this architecture)
    token = request.query_params.get("token")
    
    # Try Authorization header
    if not token and credentials:
        token = credentials.credentials
    
    # Try cookie
    if not token:
        token = request.cookies.get("token")
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide token via ?token=xxx parameter.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret, 
            algorithms=[settings.jwt_algorithm]
        )
        
        # Validate required claims
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401, 
                detail="Invalid token: missing sub claim"
            )
        
        # Extract role from custom claim
        role = payload.get("role", "viewer")
        
        # Get permissions for role
        permissions = ROLE_PERMISSIONS.get(role, ["seminars:read"])
        
        return AuthenticatedUser(
            user_id=user_id,
            role=role,
            permissions=permissions,
            authenticated_at=datetime.utcnow()
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthenticatedUser]:
    """Get current user if authenticated, None otherwise."""
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


def require_permission(permission: str):
    """Dependency factory for requiring a specific permission."""
    async def permission_checker(
        user: AuthenticatedUser = Depends(get_current_user)
    ) -> AuthenticatedUser:
        if permission not in user.permissions and "admin" not in user.permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied. Required: {permission}"
            )
        return user
    return permission_checker
