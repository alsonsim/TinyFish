"""Shared type definitions."""

from typing import Literal, TypeAlias

# Ticker symbol type
TickerSymbol: TypeAlias = str

# Source types
SourceType: TypeAlias = Literal["news", "forums", "social", "crypto"]

# Sentiment types
SentimentType: TypeAlias = Literal["BULL", "BEAR", "NEUTRAL"]

# Action types
ActionType: TypeAlias = Literal["BUY", "SELL", "HOLD"]
