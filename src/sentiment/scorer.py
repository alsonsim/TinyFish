"""Sentiment scoring utilities."""

import structlog
from typing import Literal

logger = structlog.get_logger(__name__)


class SentimentScorer:
    """
    Utility class for sentiment score calculations and aggregations.
    
    Example:
        >>> scorer = SentimentScorer()
        >>> normalized = scorer.normalize_score(0.85)
        >>> sentiment = scorer.classify_sentiment(0.8, 0.3)
    """
    
    def __init__(self) -> None:
        self.logger = logger.bind(component="sentiment_scorer")
    
    def normalize_score(self, score: float) -> float:
        """
        Normalize a sentiment score to 0.0-1.0 range.
        
        Args:
            score: Raw sentiment score
        
        Returns:
            Normalized score between 0.0 and 1.0
        """
        return max(0.0, min(1.0, score))
    
    def classify_sentiment(
        self,
        bull_score: float,
        bear_score: float,
        threshold: float = 0.2,
    ) -> Literal["BULL", "BEAR", "NEUTRAL"]:
        """
        Classify overall sentiment based on bull/bear scores.
        
        Args:
            bull_score: Bullish sentiment score (0.0-1.0)
            bear_score: Bearish sentiment score (0.0-1.0)
            threshold: Minimum difference to classify as BULL/BEAR
        
        Returns:
            Sentiment classification
        """
        diff = bull_score - bear_score
        
        if diff > threshold:
            return "BULL"
        elif diff < -threshold:
            return "BEAR"
        else:
            return "NEUTRAL"
    
    def aggregate_scores(
        self,
        scores: list[tuple[float, float]],
    ) -> tuple[float, float]:
        """
        Aggregate multiple (bull, bear) score pairs.
        
        Args:
            scores: List of (bull_score, bear_score) tuples
        
        Returns:
            Aggregated (bull_score, bear_score) tuple
        """
        if not scores:
            return (0.5, 0.5)
        
        avg_bull = sum(s[0] for s in scores) / len(scores)
        avg_bear = sum(s[1] for s in scores) / len(scores)
        
        return (avg_bull, avg_bear)
    
    def weighted_aggregate(
        self,
        scores: list[tuple[float, float, float]],
    ) -> tuple[float, float]:
        """
        Aggregate scores with weights.
        
        Args:
            scores: List of (bull_score, bear_score, weight) tuples
        
        Returns:
            Weighted aggregated (bull_score, bear_score) tuple
        """
        if not scores:
            return (0.5, 0.5)
        
        total_weight = sum(s[2] for s in scores)
        
        if total_weight == 0:
            return self.aggregate_scores([(s[0], s[1]) for s in scores])
        
        weighted_bull = sum(s[0] * s[2] for s in scores) / total_weight
        weighted_bear = sum(s[1] * s[2] for s in scores) / total_weight
        
        return (weighted_bull, weighted_bear)
