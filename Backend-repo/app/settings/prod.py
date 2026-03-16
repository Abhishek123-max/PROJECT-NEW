"""
Production environment configuration settings.
"""

from .base import BaseConfig


class ProdConfig(BaseConfig):
    """Production environment configuration."""
    
    # Application Settings
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_ECHO: bool = False  # Disable SQL query logging in production
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # Redis Configuration
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_MAX_CONNECTIONS: int = 100
    
    # JWT Configuration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Password Security - Higher rounds for production security
    BCRYPT_ROUNDS: int = 12
    
    # Rate Limiting - Strict limits for production
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_WINDOW: int = 900  # 15 minutes
    
    # CORS Configuration - Restrict origins in production
    CORS_ORIGINS: list = []  # Should be set via environment variables
    
    # Security Headers
    SECURITY_HEADERS: bool = True
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    # Audit Configuration
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 365
    
    # Feature Toggle Configuration
    FEATURE_TOGGLES_CACHE_TTL: int = 300  # 5 minutes
    
    # Production-specific settings
    RELOAD: bool = False
    WORKERS: int = 4
    
    # Health Check Configuration
    HEALTH_CHECK_TIMEOUT: int = 10
    
    # Performance Settings
    KEEP_ALIVE: int = 2
    MAX_REQUESTS: int = 1000
    MAX_REQUESTS_JITTER: int = 100
    PRELOAD_APP: bool = True
    
    # SSL/TLS Settings
    SSL_KEYFILE: str = ""
    SSL_CERTFILE: str = ""
    SSL_VERSION: int = 2  # TLS 1.2
    SSL_CERT_REQS: int = 0
    SSL_CA_CERTS: str = ""
    SSL_CIPHERS: str = "TLSv1.2"
    
    class Config:
        env_file = ".env.prod"
        env_file_encoding = "utf-8"