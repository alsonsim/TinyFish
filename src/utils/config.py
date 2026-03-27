"""Configuration management using pydantic-settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    
    # TinyFish
    tinyfish_api_key: str
    tinyfish_headless: bool = True
    
    # Database
    redis_url: str = "redis://localhost:6379/0"
    postgres_url: str | None = None
    
    # Alerts
    discord_webhook: str | None = None
    slack_webhook: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    
    # Agent Configuration
    sentiment_threshold: float = 0.7
    scan_interval: int = 300
    default_tickers: str = "AAPL,TSLA,NVDA,BTC,ETH"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Rate Limiting
    max_requests_per_minute: int = 60
    openai_rpm_limit: int = 3500
    
    # Feature Flags
    enable_caching: bool = True
    enable_vector_storage: bool = True
    enable_alerts: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    @property
    def tickers_list(self) -> list[str]:
        """Get default tickers as a list."""
        return [t.strip() for t in self.default_tickers.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
