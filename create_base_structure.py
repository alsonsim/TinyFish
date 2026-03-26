"""Create minimal TinyFish Financial Agent project structure."""

import os

# Directory structure
dirs = [
    'src/agent',
    'src/sources',
    'src/sentiment',
    'src/data',
    'src/trading',
    'src/utils',
    'tests',
    'scripts'
]

# Minimal files with basic structure
files = {
    # Root files
    'README.md': '''# TinyFish Financial Agent

AI-powered financial sentiment analysis using TinyFish + OpenAI.

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env
python main.py
```
''',
    
    'requirements.txt': '''openai>=1.0.0
tinyfish>=0.1.0
pydantic>=2.0.0
python-dotenv>=1.0.0
structlog>=24.0.0
httpx>=0.25.0
pytest>=7.0.0
pytest-asyncio>=0.23.0
''',
    
    '.env.example': '''OPENAI_API_KEY=
TINYFISH_API_KEY=
REDIS_URL=redis://localhost:6379/0
''',
    
    '.gitignore': '''__pycache__/
*.py[cod]
.env
venv/
.pytest_cache/
''',
    
    'main.py': '''"""Main entry point."""
import asyncio
from src.agent.core import FinancialAgent

async def main():
    agent = FinancialAgent()
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
''',
    
    # Source files - minimal structure
    'src/__init__.py': '',
    
    'src/agent/__init__.py': '',
    'src/agent/core.py': '''"""Main agent orchestration."""

class FinancialAgent:
    def __init__(self):
        pass
    
    async def run(self):
        pass
''',
    
    'src/agent/planner.py': '''"""LLM-based planning."""

class AgentPlanner:
    pass
''',
    
    'src/agent/executor.py': '''"""TinyFish browser executor."""

class TinyFishExecutor:
    pass
''',
    
    'src/sources/__init__.py': '',
    'src/sources/news.py': '''"""News sources."""

class CNBCSource:
    pass

class BloombergSource:
    pass
''',
    
    'src/sources/forums.py': '''"""Forum sources."""

class RedditSource:
    pass

class StockTwitsSource:
    pass
''',
    
    'src/sources/social.py': '''"""Social media sources."""

class TwitterSource:
    pass
''',
    
    'src/sources/crypto.py': '''"""Crypto sources."""

class CoinMarketCapSource:
    pass
''',
    
    'src/sentiment/__init__.py': '',
    'src/sentiment/analyzer.py': '''"""Sentiment analysis."""

class SentimentAnalyzer:
    pass
''',
    
    'src/sentiment/signals.py': '''"""Trading signal generation."""

class SignalGenerator:
    pass
''',
    
    'src/sentiment/scorer.py': '''"""Sentiment scoring."""

class SentimentScorer:
    pass
''',
    
    'src/data/__init__.py': '',
    'src/data/models.py': '''"""Pydantic data models."""
from pydantic import BaseModel
from typing import Literal

class SentimentScore(BaseModel):
    ticker: str
    bull_score: float
    bear_score: float
    sentiment: Literal["BULL", "BEAR", "NEUTRAL"]

class TradingSignal(BaseModel):
    ticker: str
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float
    reasons: list[str]
''',
    
    'src/data/storage.py': '''"""Data storage."""

class VectorStore:
    pass
''',
    
    'src/data/cache.py': '''"""Caching."""

class CacheManager:
    pass
''',
    
    'src/trading/__init__.py': '',
    'src/trading/signals.py': '''"""Signal formatting."""

class SignalFormatter:
    pass
''',
    
    'src/trading/alerts.py': '''"""Alert system."""

class AlertManager:
    pass
''',
    
    'src/utils/__init__.py': '',
    'src/utils/config.py': '''"""Configuration."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    tinyfish_api_key: str
    
    class Config:
        env_file = ".env"
''',
    
    'src/utils/logger.py': '''"""Logging setup."""
import structlog

def setup_logging():
    structlog.configure()
''',
    
    'tests/__init__.py': '',
    'tests/test_agent.py': '''"""Agent tests."""
import pytest

def test_placeholder():
    assert True
''',
    
    'docker-compose.yml': '''version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
''',
}

def create_structure():
    print("Creating TinyFish Financial Agent base structure...\n")
    
    # Create directories
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"📁 {dir_path}/")
    
    print()
    
    # Create files
    for filepath, content in files.items():
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📄 {filepath}")
    
    print("\n✅ Base structure created!")
    print("\nNext steps:")
    print("1. pip install -r requirements.txt")
    print("2. cp .env.example .env")
    print("3. Add your API keys to .env")
    print("4. Start implementing in src/")

if __name__ == "__main__":
    create_structure()
