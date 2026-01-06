from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://hindsight:hindsight_dev@localhost:5432/hindsight"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # FRED API
    fred_api_key: str = ""
    
    # Application
    secret_key: str = "dev-secret-key"
    environment: str = "development"
    frontend_url: str = "http://localhost:3000"
    app_base_url: str = "http://localhost:3000"  # Same as frontend_url, used for magic links
    
    # Authentication
    resend_api_key: str = ""
    jwt_secret: str = "jwt-dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    magic_link_expires_minutes: int = 15
    session_expires_days: int = 30
    
    # Data pipeline config
    shiller_url: str = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
    lookback_months: int = 24
    forward_months: int = 12
    
    # Scoring config
    benchmark_stocks: int = 60
    benchmark_bonds: int = 40
    benchmark_cash: int = 0
    benchmark_gold: int = 0
    
    # Validation config
    min_rationale_chars: int = 50
    max_rationale_chars: int = 500
    confidence_min: float = 0.50
    confidence_max: float = 1.00

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


