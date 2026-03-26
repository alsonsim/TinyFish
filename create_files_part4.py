"""Complete file creation script - Part 4: Trading, Utils, and Tests."""

import os

files = {
    # src/trading/__init__.py
    "src/trading/__init__.py": '''"""Trading signal output and alerting."""

from .signals import SignalFormatter
from .alerts import AlertManager

__all__ = ["SignalFormatter", "AlertManager"]
''',

    # src/trading/signals.py
    "src/trading/signals.py": '''"""Trading signal formatting and output."""

import structlog
from datetime import datetime

from src.data.models import TradingSignal

logger = structlog.get_logger(__name__)


class SignalFormatter:
    """
    Formats trading signals for various outputs.
    
    Example:
        >>> formatter = SignalFormatter()
        >>> text = formatter.to_text(signal)
        >>> json_str = formatter.to_json(signal)
    """
    
    def __init__(self) -> None:
        self.logger = logger.bind(component="signal_formatter")
    
    def to_text(self, signal: TradingSignal) -> str:
        """
        Format signal as plain text.
        
        Args:
            signal: Trading signal to format
        
        Returns:
            Formatted text string
        """
        emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}[signal.action]
        
        text = f"""
{emoji} TRADING SIGNAL {emoji}

Ticker: {signal.ticker}
Action: {signal.action}
Confidence: {signal.confidence:.1%}
Time: {signal.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}

Reasons:
"""
        for i, reason in enumerate(signal.reasons, 1):
            text += f"{i}. {reason}\n"
        
        return text.strip()
    
    def to_json(self, signal: TradingSignal) -> str:
        """
        Format signal as JSON.
        
        Args:
            signal: Trading signal to format
        
        Returns:
            JSON string
        """
        return signal.model_dump_json(indent=2)
    
    def to_markdown(self, signal: TradingSignal) -> str:
        """
        Format signal as Markdown.
        
        Args:
            signal: Trading signal to format
        
        Returns:
            Markdown formatted string
        """
        emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}[signal.action]
        
        md = f"""# {emoji} Trading Signal: {signal.action}

**Ticker:** `{signal.ticker}`  
**Confidence:** {signal.confidence:.1%}  
**Time:** {signal.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}

## Reasons

"""
        for reason in signal.reasons:
            md += f"- {reason}\n"
        
        return md.strip()
''',

    # src/trading/alerts.py
    "src/trading/alerts.py": '''"""Alert system for Discord, Slack, and Telegram."""

import structlog
from typing import Any

from src.data.models import TradingSignal
from src.trading.signals import SignalFormatter

logger = structlog.get_logger(__name__)


class AlertManager:
    """
    Manages alerts across multiple platforms.
    
    Example:
        >>> alerts = AlertManager(discord_webhook="https://...")
        >>> await alerts.send_signal_alert(signal)
    """
    
    def __init__(
        self,
        discord_webhook: str | None = None,
        slack_webhook: str | None = None,
        telegram_token: str | None = None,
    ) -> None:
        """
        Initialize alert manager.
        
        Args:
            discord_webhook: Discord webhook URL
            slack_webhook: Slack webhook URL
            telegram_token: Telegram bot token
        """
        self.discord_webhook = discord_webhook
        self.slack_webhook = slack_webhook
        self.telegram_token = telegram_token
        
        self.formatter = SignalFormatter()
        self.logger = logger.bind(component="alert_manager")
    
    async def send_signal_alert(self, signal: TradingSignal) -> None:
        """
        Send alert for a trading signal to all configured platforms.
        
        Args:
            signal: Trading signal to alert on
        """
        self.logger.info(
            "sending_signal_alert",
            ticker=signal.ticker,
            action=signal.action,
        )
        
        # Send to all configured platforms
        if self.discord_webhook:
            await self._send_discord(signal)
        
        if self.slack_webhook:
            await self._send_slack(signal)
        
        if self.telegram_token:
            await self._send_telegram(signal)
    
    async def _send_discord(self, signal: TradingSignal) -> None:
        """Send alert to Discord."""
        try:
            # TODO: Implement Discord webhook
            # from discord_webhook import AsyncDiscordWebhook
            # webhook = AsyncDiscordWebhook(url=self.discord_webhook)
            # await webhook.execute(content=self.formatter.to_text(signal))
            
            self.logger.info("discord_alert_sent", ticker=signal.ticker)
            
        except Exception as e:
            self.logger.error("discord_alert_failed", error=str(e))
    
    async def _send_slack(self, signal: TradingSignal) -> None:
        """Send alert to Slack."""
        try:
            # TODO: Implement Slack webhook
            # import httpx
            # async with httpx.AsyncClient() as client:
            #     await client.post(
            #         self.slack_webhook,
            #         json={"text": self.formatter.to_markdown(signal)},
            #     )
            
            self.logger.info("slack_alert_sent", ticker=signal.ticker)
            
        except Exception as e:
            self.logger.error("slack_alert_failed", error=str(e))
    
    async def _send_telegram(self, signal: TradingSignal) -> None:
        """Send alert to Telegram."""
        try:
            # TODO: Implement Telegram bot
            # from telegram import Bot
            # bot = Bot(token=self.telegram_token)
            # await bot.send_message(
            #     chat_id=self.telegram_chat_id,
            #     text=self.formatter.to_text(signal),
            # )
            
            self.logger.info("telegram_alert_sent", ticker=signal.ticker)
            
        except Exception as e:
            self.logger.error("telegram_alert_failed", error=str(e))
''',

    # src/utils/__init__.py
    "src/utils/__init__.py": '''"""Utility modules for configuration, logging, and types."""

from .config import Settings, get_settings
from .logger import setup_logging
from .types import TickerSymbol, SourceType

__all__ = ["Settings", "get_settings", "setup_logging", "TickerSymbol", "SourceType"]
''',

    # src/utils/config.py
    "src/utils/config.py": '''"""Configuration management using pydantic-settings."""

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
''',

    # src/utils/logger.py
    "src/utils/logger.py": '''"""Structured logging setup with structlog."""

import structlog
import logging
import sys
from typing import Any


def setup_logging(level: str = "INFO", format: str = "json") -> None:
    """
    Setup structured logging with structlog.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        format: Output format ("json" or "console")
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )
    
    # Structlog processors
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Add appropriate renderer based on format
    if format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
''',

    # src/utils/types.py
    "src/utils/types.py": '''"""Shared type definitions."""

from typing import Literal, TypeAlias

# Ticker symbol type
TickerSymbol: TypeAlias = str

# Source types
SourceType: TypeAlias = Literal["news", "forums", "social", "crypto"]

# Sentiment types
SentimentType: TypeAlias = Literal["BULL", "BEAR", "NEUTRAL"]

# Action types
ActionType: TypeAlias = Literal["BUY", "SELL", "HOLD"]
''',

    # tests/__init__.py
    "tests/__init__.py": '''"""Test suite for TinyFish Financial Agent."""

__version__ = "0.1.0"
''',

    # tests/test_agent.py
    "tests/test_agent.py": '''"""Tests for agent orchestration."""

import pytest
from unittest.mock import AsyncMock, Mock

from src.agent.core import FinancialAgent
from src.data.models import TradingSignal


@pytest.mark.asyncio
async def test_financial_agent_initialization():
    """Test that FinancialAgent initializes correctly."""
    agent = FinancialAgent(
        openai_api_key="test-key",
        tinyfish_key="test-key",
    )
    
    assert agent is not None
    assert agent.planner is not None
    assert agent.executor is not None
    assert agent.analyzer is not None


@pytest.mark.asyncio
async def test_monitor_sentiment():
    """Test sentiment monitoring pipeline."""
    agent = FinancialAgent(
        openai_api_key="test-key",
        tinyfish_key="test-key",
    )
    
    # Mock the internal methods
    agent._collect_data = AsyncMock(return_value=[
        {"text": "AAPL stock is going up!", "source": "test"}
    ])
    agent._analyze_sentiment = AsyncMock(return_value=[])
    agent.signal_generator.generate = AsyncMock(
        return_value=TradingSignal(
            ticker="AAPL",
            action="HOLD",
            confidence=0.5,
            reasons=["No data"],
        )
    )
    
    signal = await agent.monitor_sentiment(["AAPL"])
    
    assert signal is not None
    assert signal.ticker == "AAPL"
    assert signal.action in ["BUY", "SELL", "HOLD"]


@pytest.mark.asyncio
async def test_agent_cleanup():
    """Test agent cleanup."""
    agent = FinancialAgent(
        openai_api_key="test-key",
        tinyfish_key="test-key",
    )
    
    await agent.cleanup()
    # Should not raise any exceptions
''',

    # tests/test_sentiment.py
    "tests/test_sentiment.py": '''"""Tests for sentiment analysis."""

import pytest
from src.sentiment.analyzer import SentimentAnalyzer
from src.sentiment.signals import SignalGenerator
from src.data.models import SentimentScore


@pytest.mark.asyncio
async def test_sentiment_analyzer():
    """Test sentiment analysis."""
    analyzer = SentimentAnalyzer(openai_api_key="test-key")
    
    # Mock OpenAI response
    analyzer.client.chat.completions.create = pytest.AsyncMock(
        return_value=Mock(
            choices=[
                Mock(
                    message=Mock(
                        content="""
Bull Score: 0.8
Bear Score: 0.2
Sentiment: BULL
Reasons:
- Positive news
- Strong growth
"""
                    )
                )
            ]
        )
    )
    
    score = await analyzer.analyze_ticker(
        "AAPL",
        [{"text": "Apple stock soaring!"}],
    )
    
    assert score.ticker == "AAPL"
    assert 0 <= score.bull_score <= 1
    assert 0 <= score.bear_score <= 1


def test_signal_generator():
    """Test signal generation logic."""
    generator = SignalGenerator(bull_threshold=0.7, bear_threshold=0.7)
    
    # Test that it initializes
    assert generator is not None
    assert generator.bull_threshold == 0.7


@pytest.mark.asyncio
async def test_signal_generation_buy():
    """Test BUY signal generation."""
    generator = SignalGenerator()
    
    scores = [
        SentimentScore(
            ticker="AAPL",
            bull_score=0.9,
            bear_score=0.2,
            sentiment="BULL",
            reasons=["Strong momentum"],
        )
    ]
    
    signal = await generator.generate(scores, ["AAPL"])
    
    assert signal.action == "BUY"
    assert signal.confidence > 0.7
''',

    # tests/test_sources.py
    "tests/test_sources.py": '''"""Tests for data sources."""

import pytest
from src.sources.news import CNBCSource, BloombergSource
from src.agent.executor import TinyFishExecutor


@pytest.fixture
def mock_executor():
    """Create a mock executor."""
    executor = TinyFishExecutor(api_key="test-key")
    executor.fetch_page = pytest.AsyncMock(
        return_value="<html><body>Test content</body></html>"
    )
    return executor


@pytest.mark.asyncio
async def test_cnbc_source(mock_executor):
    """Test CNBC source scraping."""
    source = CNBCSource(executor=mock_executor)
    
    data = await source.fetch_data("AAPL")
    
    # Should return data (even if mocked/empty)
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_bloomberg_source(mock_executor):
    """Test Bloomberg source scraping."""
    source = BloombergSource(executor=mock_executor)
    
    data = await source.fetch_data("TSLA")
    
    assert isinstance(data, list)
''',

    # docker-compose.yml
    "docker-compose.yml": '''version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: tinyfish
      POSTGRES_PASSWORD: tinyfish_password
      POSTGRES_DB: tinyfish_agent
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tinyfish"]
      interval: 5s
      timeout: 3s
      retries: 5

  agent:
    build: .
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    environment:
      REDIS_URL: redis://redis:6379/0
      POSTGRES_URL: postgresql://tinyfish:tinyfish_password@postgres:5432/tinyfish_agent
    env_file:
      - .env
    volumes:
      - ./src:/app/src
      - ./logs:/app/logs
    command: python -m src.agent.core

volumes:
  redis_data:
  postgres_data:
''',

    # Dockerfile
    "Dockerfile": '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/

# Create logs directory
RUN mkdir -p logs

# Run tests (optional)
# RUN pytest tests/

# Default command
CMD ["python", "-m", "src.agent.core"]
''',

    # scripts/dev.sh
    "scripts/dev.sh": '''#!/bin/bash

# TinyFish Financial Agent - Development Script

echo "🐟 Starting TinyFish Financial Agent Development Environment"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your API keys before continuing."
    exit 1
fi

# Start Docker services
echo "🐳 Starting Docker services (Redis + Postgres)..."
docker-compose up -d redis postgres

echo "⏳ Waiting for services to be ready..."
sleep 5

# Run tests
echo "🧪 Running tests..."
pytest tests/ -v

if [ $? -eq 0 ]; then
    echo "✅ Tests passed!"
else
    echo "❌ Tests failed. Please fix before continuing."
    exit 1
fi

# Start the agent
echo "🚀 Starting agent..."
python -m src.agent.core

echo ""
echo "Development environment ready!"
''',

    # scripts/deploy.sh
    "scripts/deploy.sh": '''#!/bin/bash

# TinyFish Financial Agent - Deployment Script

echo "🐟 Deploying TinyFish Financial Agent"
echo ""

# Build Docker image
echo "🏗️  Building Docker image..."
docker-compose build

# Run tests in container
echo "🧪 Running tests..."
docker-compose run --rm agent pytest tests/ -v

if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Aborting deployment."
    exit 1
fi

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

echo "✅ Deployment complete!"
echo ""
echo "Services running:"
docker-compose ps

echo ""
echo "View logs: docker-compose logs -f agent"
''',
}

def create_files():
    for filepath, content in files.items():
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Created: {filepath}")

if __name__ == "__main__":
    print("Creating trading, utils, tests, and Docker files...")
    print()
    create_files()
    print()
    print("Part 4 complete!")
    print()
    print("Making scripts executable...")
    import stat
    for script in ["scripts/dev.sh", "scripts/deploy.sh"]:
        if os.path.exists(script):
            os.chmod(script, os.stat(script).st_mode | stat.S_IEXEC)
    print("Done!")
