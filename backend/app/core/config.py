from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str = "fleetwise"
    
    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application
    APP_NAME: str = "FleetWise"
    DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Security Settings (Phase 5)
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    
    # Password Policy
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Rate Limiting
    RATE_LIMIT_LOGIN: str = "30/minute"
    RATE_LIMIT_REGISTER: str = "15/minute"
    RATE_LIMIT_API: str = "200/minute"
    RATE_LIMIT_CHATBOT: str = "100/minute"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_RETENTION_DAYS: int = 90
    LOG_MAX_BYTES: int = 104857600  # 100MB
    LOG_BACKUP_COUNT: int = 10
    
    # Session Settings
    MAX_CONCURRENT_SESSIONS: int = 3
    SESSION_TIMEOUT_MINUTES: int = 30
    
    # Email (for Phase 5)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()