"""Pydantic data models for the financial agent."""

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
