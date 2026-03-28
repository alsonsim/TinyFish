"""Configuration management using pydantic-settings when available."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    HAS_PYDANTIC_SETTINGS = True
except ImportError:  # pragma: no cover - exercised in dependency-light setups
    HAS_PYDANTIC_SETTINGS = False
    BaseSettings = BaseModel  # type: ignore[misc, assignment]

    def SettingsConfigDict(**kwargs: object) -> dict[str, object]:
        return dict(kwargs)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4"

    tinyfish_api_key: str | None = None
    tinyfish_headless: bool = True

    redis_url: str = "redis://localhost:6379/0"
    postgres_url: str | None = None

    discord_webhook: str | None = None
    slack_webhook: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    sentiment_threshold: float = 0.7
    scan_interval: int = 300
    default_tickers: str = "AAPL,TSLA,NVDA,BTC,ETH"

    log_level: str = "INFO"
    log_format: str = "json"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    max_requests_per_minute: int = 60
    openai_rpm_limit: int = 3500

    enable_caching: bool = True
    enable_vector_storage: bool = True
    enable_alerts: bool = True
    offline_mode: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def tickers_list(self) -> list[str]:
        """Get default tickers as a list."""
        return [t.strip().upper() for t in self.default_tickers.split(",") if t.strip()]


def _parse_env_file(path: str = ".env") -> dict[str, str]:
    values: dict[str, str] = {}
    if not os.path.exists(path):
        return values

    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    if not HAS_PYDANTIC_SETTINGS:
        env_values = _parse_env_file()
        for key, value in os.environ.items():
            env_values[key] = value

        bool_fields = {
            "tinyfish_headless",
            "enable_caching",
            "enable_vector_storage",
            "enable_alerts",
            "offline_mode",
        }
        int_fields = {"scan_interval", "api_port", "max_requests_per_minute", "openai_rpm_limit"}
        float_fields = {"sentiment_threshold"}

        parsed: dict[str, object] = {}
        for field_name in Settings.model_fields:
            env_name = field_name.upper()
            raw_value = env_values.get(env_name)
            if raw_value is None:
                continue
            if field_name in bool_fields:
                parsed[field_name] = raw_value.strip().lower() in {"1", "true", "yes", "on"}
            elif field_name in int_fields:
                parsed[field_name] = int(raw_value)
            elif field_name in float_fields:
                parsed[field_name] = float(raw_value)
            else:
                parsed[field_name] = raw_value
        return Settings(**parsed)

    return Settings()
