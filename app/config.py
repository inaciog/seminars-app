"""
Configuration settings for seminars-app.
"""

import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Application
    app_name: str = "Seminars App"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8080
    
    # Database
    database_url: str = "sqlite:///./data/seminars.db"
    
    # Security
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    api_secret: str = "change-me-in-production"
    
    # File uploads
    uploads_dir: str = "./uploads"
    max_upload_size: int = 50 * 1024 * 1024  # 50MB
    
    # Backup
    backup_dir: str = "./backups"
    backup_retention_days: int = 180
    
    # Dropbox (optional)
    dropbox_token: str | None = None


# Role-based permissions
ROLE_PERMISSIONS = {
    "admin": [
        "seminars:read",
        "seminars:write",
        "seminars:planning",
        "seminars:upload",
        "external:read"
    ],
    "seminar_organizer": [
        "seminars:read",
        "seminars:write",
        "seminars:planning",
        "seminars:upload"
    ],
    "seminar_viewer": [
        "seminars:read"
    ],
    "viewer": [
        "seminars:read"
    ]
}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
