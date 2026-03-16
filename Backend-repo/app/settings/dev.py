"""
Development environment configuration settings.
"""

from .base import BaseConfig


class DevConfig(BaseConfig):
    """Development environment configuration."""
    
    # Application Settings
    DEBUG: bool = True
    
    # Database Configuration
    DATABASE_ECHO: bool = True  # Enable SQL query logging in development
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis Configuration
    REDIS_SOCKET_TIMEOUT: int = 10
    REDIS_MAX_CONNECTIONS: int = 20
    
    # JWT Configuration - Shorter expiry for development testing
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password Security - Lower rounds for faster development
    BCRYPT_ROUNDS: int = 10
    
    # Rate Limiting - More lenient for development
    RATE_LIMIT_REQUESTS: int = 1000
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 10
    RATE_LIMIT_LOGIN_WINDOW: int = 300  # 5 minutes
    
    # CORS Configuration - Allow all origins in development
    CORS_ORIGINS: list = ["*"]
    
    # Logging Configuration
    LOG_LEVEL: str = "DEBUG"
    
    # Audit Configuration
    AUDIT_LOG_RETENTION_DAYS: int = 30  # Shorter retention in development
    
    # Feature Toggle Configuration
    FEATURE_TOGGLES_CACHE_TTL: int = 60  # 1 minute for faster development iteration
    
    # Development-specific settings
    RELOAD: bool = True
    WORKERS: int = 1
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"