"""Complete file creation script - Part 3: Data models and storage."""

import os

files = {
    # src/data/__init__.py
    "src/data/__init__.py": '''"""Data models, storage, and caching."""

from .models import SentimentScore, TradingSignal, CollectionPlan
from .storage import VectorStore
from .cache import CacheManager

__all__ = [
    "SentimentScore",
    "TradingSignal",
    "CollectionPlan",
    "VectorStore",
    "CacheManager",
]
''',

    # src/data/models.py
    "src/data/models.py": '''"""Pydantic data models for the financial agent."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class SentimentScore(BaseModel):
    """Sentiment analysis score for a ticker."""
    
    ticker: str = Field(..., description="Stock ticker symbol")
    bull_score: float = Field(..., ge=0.0, le=1.0, description="Bullish sentiment score")
    bear_score: float = Field(..., ge=0.0, le=1.0, description="Bearish sentiment score")
    sentiment: Literal["BULL", "BEAR", "NEUTRAL"] = Field(..., description="Overall sentiment classification")
    reasons: list[str] = Field(default_factory=list, description="Key reasons for the sentiment")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "bull_score": 0.75,
                "bear_score": 0.25,
                "sentiment": "BULL",
                "reasons": [
                    "Strong earnings report",
                    "Positive analyst ratings",
                    "Product launch hype"
                ],
            }
        }


class TradingSignal(BaseModel):
    """Trading signal generated from sentiment analysis."""
    
    ticker: str = Field(..., description="Stock ticker symbol(s)")
    action: Literal["BUY", "SELL", "HOLD"] = Field(..., description="Recommended action")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level in the signal")
    reasons: list[str] = Field(..., description="Reasons for the signal")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Signal generation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "TSLA",
                "action": "BUY",
                "confidence": 0.82,
                "reasons": [
                    "Strong bullish sentiment (0.85)",
                    "Positive news coverage",
                    "High social media engagement"
                ],
            }
        }


class CollectionPlan(BaseModel):
    """Plan for data collection across sources."""
    
    tickers: list[str] = Field(..., description="Tickers to collect data for")
    priority_sources: list[str] = Field(..., description="Sources in priority order")
    reasoning: str = Field(..., description="LLM reasoning for the plan")
    parallel_sources: int = Field(default=2, ge=1, le=5, description="Number of sources to query in parallel")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tickers": ["AAPL", "TSLA"],
                "priority_sources": ["news", "social", "forums"],
                "reasoning": "News and social provide real-time sentiment",
                "parallel_sources": 3,
            }
        }


class SourceData(BaseModel):
    """Raw data from a source."""
    
    source: str = Field(..., description="Source name (e.g., 'cnbc', 'reddit')")
    ticker: str = Field(..., description="Related ticker symbol")
    title: str | None = Field(None, description="Article/post title")
    text: str = Field(..., description="Main content text")
    url: str = Field(..., description="Source URL")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Collection timestamp")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class AgentState(BaseModel):
    """State of the financial agent."""
    
    status: Literal["idle", "collecting", "analyzing", "signaling"] = "idle"
    current_tickers: list[str] = Field(default_factory=list)
    last_run: datetime | None = None
    errors: list[str] = Field(default_factory=list)
''',

    # src/data/storage.py
    "src/data/storage.py": '''"""Vector storage for historical sentiment data."""

import structlog
from typing import Any
import json

from src.data.models import SentimentScore, TradingSignal

logger = structlog.get_logger(__name__)


class VectorStore:
    """
    Manages vector storage for sentiment history and signals.
    
    Uses:
    - Redis for caching and recent data
    - Postgres with pgvector for long-term vector storage
    
    Example:
        >>> store = VectorStore(redis_url="redis://localhost", postgres_url="postgresql://...")
        >>> await store.store_sentiments([sentiment_score])
        >>> historical = await store.query_similar(ticker="AAPL", limit=10)
    """
    
    def __init__(
        self,
        redis_url: str,
        postgres_url: str | None = None,
    ) -> None:
        """
        Initialize vector store.
        
        Args:
            redis_url: Redis connection URL
            postgres_url: PostgreSQL connection URL (optional)
        """
        self.redis_url = redis_url
        self.postgres_url = postgres_url
        self.logger = logger.bind(component="vector_store")
        
        # TODO: Initialize actual connections
        # import redis.asyncio as redis
        # self.redis = redis.from_url(redis_url)
        
        # if postgres_url:
        #     from sqlalchemy.ext.asyncio import create_async_engine
        #     self.engine = create_async_engine(postgres_url)
        
        self.logger.info("vector_store_initialized")
    
    async def store_sentiments(
        self,
        scores: list[SentimentScore],
    ) -> None:
        """
        Store sentiment scores.
        
        Args:
            scores: List of sentiment scores to store
        """
        self.logger.info("storing_sentiments", count=len(scores))
        
        # TODO: Implement actual storage
        # for score in scores:
        #     key = f"sentiment:{score.ticker}:{score.timestamp.isoformat()}"
        #     await self.redis.setex(
        #         key,
        #         3600 * 24,  # 24 hour TTL
        #         score.model_dump_json(),
        #     )
        
        self.logger.debug("sentiments_stored")
    
    async def store_signal(self, signal: TradingSignal) -> None:
        """
        Store trading signal.
        
        Args:
            signal: Trading signal to store
        """
        self.logger.info("storing_signal", ticker=signal.ticker, action=signal.action)
        
        # TODO: Implement actual storage
        # key = f"signal:{signal.ticker}:{signal.timestamp.isoformat()}"
        # await self.redis.setex(
        #     key,
        #     3600 * 24 * 7,  # 7 day TTL
        #     signal.model_dump_json(),
        #  )
    
    async def query_similar(
        self,
        ticker: str,
        limit: int = 10,
    ) -> list[SentimentScore]:
        """
        Query for similar historical sentiment.
        
        Args:
            ticker: Ticker symbol to query
            limit: Maximum number of results
        
        Returns:
            List of historical sentiment scores
        """
        self.logger.info("querying_similar", ticker=ticker, limit=limit)
        
        # TODO: Implement vector similarity search
        # Using pgvector or Redis Vector Search
        
        return []
    
    async def get_signal_history(
        self,
        ticker: str,
        days: int = 7,
    ) -> list[TradingSignal]:
        """
        Get historical signals for a ticker.
        
        Args:
            ticker: Ticker symbol
            days: Number of days to look back
        
        Returns:
            List of historical trading signals
        """
        self.logger.info("getting_signal_history", ticker=ticker, days=days)
        
        # TODO: Implement
        return []
    
    async def close(self) -> None:
        """Close all connections."""
        self.logger.info("closing_vector_store")
        # TODO: Close connections
        # await self.redis.close()
        # if self.engine:
        #     await self.engine.dispose()
''',

    # src/data/cache.py
    "src/data/cache.py": '''"""Request and response caching."""

import structlog
import hashlib
import json
from typing import Any

logger = structlog.get_logger(__name__)


class CacheManager:
    """
    Manages caching for API requests and responses.
    
    Uses Redis for fast in-memory caching with TTL.
    
    Example:
        >>> cache = CacheManager(redis_url="redis://localhost")
        >>> await cache.set("key", {"data": "value"}, ttl=300)
        >>> data = await cache.get("key")
    """
    
    def __init__(self, redis_url: str) -> None:
        """
        Initialize cache manager.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.logger = logger.bind(component="cache_manager")
        
        # TODO: Initialize Redis connection
        # import redis.asyncio as redis
        # self.redis = redis.from_url(redis_url)
        
        self.logger.info("cache_manager_initialized")
    
    async def get(self, key: str) -> Any | None:
        """
        Get cached data by key.
        
        Args:
            key: Cache key
        
        Returns:
            Cached data or None if not found
        """
        try:
            # TODO: Implement actual Redis get
            # data = await self.redis.get(key)
            # if data:
            #     return json.loads(data)
            return None
            
        except Exception as e:
            self.logger.error("cache_get_failed", key=key, error=str(e))
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
    ) -> None:
        """
        Set cached data with TTL.
        
        Args:
            key: Cache key
            value: Data to cache
            ttl: Time to live in seconds
        """
        try:
            # TODO: Implement actual Redis set
            # await self.redis.setex(
            #     key,
            #     ttl,
            #     json.dumps(value),
            # )
            pass
            
        except Exception as e:
            self.logger.error("cache_set_failed", key=key, error=str(e))
    
    async def get_cached_data(
        self,
        source: str,
        ticker: str,
    ) -> list[dict[str, Any]] | None:
        """
        Get cached source data for ticker.
        
        Args:
            source: Source name
            ticker: Ticker symbol
        
        Returns:
            Cached data or None
        """
        cache_key = self._generate_key(source, ticker)
        return await self.get(cache_key)
    
    async def cache_source_data(
        self,
        source: str,
        ticker: str,
        data: list[dict[str, Any]],
        ttl: int = 300,
    ) -> None:
        """
        Cache source data.
        
        Args:
            source: Source name
            ticker: Ticker symbol
            data: Data to cache
            ttl: Cache TTL in seconds (default 5 min)
        """
        cache_key = self._generate_key(source, ticker)
        await self.set(cache_key, data, ttl=ttl)
    
    def _generate_key(self, *parts: str) -> str:
        """Generate cache key from parts."""
        combined = ":".join(parts)
        return f"tinyfish:{combined}"
    
    async def invalidate(self, pattern: str) -> None:
        """
        Invalidate cache keys matching pattern.
        
        Args:
            pattern: Redis key pattern
        """
        try:
            # TODO: Implement pattern-based deletion
            # keys = await self.redis.keys(pattern)
            # if keys:
            #     await self.redis.delete(*keys)
            pass
            
        except Exception as e:
            self.logger.error("cache_invalidate_failed", pattern=pattern, error=str(e))
    
    async def close(self) -> None:
        """Close Redis connection."""
        self.logger.info("closing_cache_manager")
        # TODO: Close connection
        # await self.redis.close()
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
    print("Creating data models and storage files...")
    print()
    create_files()
    print()
    print("Part 3 complete!")
