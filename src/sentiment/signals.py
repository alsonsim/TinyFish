"""Trading signal generation from sentiment scores."""

import structlog
from typing import Literal

from src.data.models import SentimentScore, TradingSignal

logger = structlog.get_logger(__name__)


class SignalGenerator:
    """
    Generates trading signals from sentiment analysis.
    
    Example:
        >>> generator = SignalGenerator()
        >>> signal = await generator.generate([sentiment_score], ["AAPL"])
        >>> print(f"{signal.action} with {signal.confidence} confidence")
    """
    
    def __init__(
        self,
        bull_threshold: float = 0.7,
        bear_threshold: float = 0.7,
    ) -> None:
        """
        Initialize signal generator.
        
        Args:
            bull_threshold: Minimum bull score for BUY signal
            bear_threshold: Minimum bear score for SELL signal
        """
        self.bull_threshold = bull_threshold
        self.bear_threshold = bear_threshold
        self.logger = logger.bind(component="signal_generator")
    
    async def generate(
        self,
        sentiment_scores: list[SentimentScore],
        tickers: list[str],
    ) -> TradingSignal:
        """
        Generate trading signal from sentiment scores.
        
        Args:
            sentiment_scores: List of sentiment scores
            tickers: Ticker symbols being analyzed
        
        Returns:
            Trading signal with action and confidence
        """
        self.logger.info("generating_signal", ticker_count=len(tickers))
        
        if not sentiment_scores:
            return self._hold_signal(tickers, "No sentiment data available")
        
        # Aggregate scores
        avg_bull = sum(s.bull_score for s in sentiment_scores) / len(sentiment_scores)
        avg_bear = sum(s.bear_score for s in sentiment_scores) / len(sentiment_scores)
        
        # Collect all reasons
        all_reasons = []
        bullish_points = []
        bearish_points = []
        for score in sentiment_scores:
            all_reasons.extend(score.reasons)
            bullish_points.extend(score.bullish_points)
            bearish_points.extend(score.bearish_points)
        
        # Determine action
        action: Literal["BUY", "SELL", "HOLD"]
        confidence: float
        
        if avg_bull > self.bull_threshold and avg_bull > avg_bear:
            action = "BUY"
            confidence = avg_bull
            primary_reasons = [
                f"Bullish news outweighed bearish news ({avg_bull:.2f} vs {avg_bear:.2f})",
                *(bullish_points[:2] or all_reasons[:2]),
            ]
        
        elif avg_bear > self.bear_threshold and avg_bear > avg_bull:
            action = "SELL"
            confidence = avg_bear
            primary_reasons = [
                f"Bearish news outweighed bullish news ({avg_bear:.2f} vs {avg_bull:.2f})",
                *(bearish_points[:2] or all_reasons[:2]),
            ]
        
        else:
            action = "HOLD"
            confidence = 1.0 - abs(avg_bull - avg_bear)  # Confidence in neutral stance
            primary_reasons = [
                f"Mixed sentiment (Bull: {avg_bull:.2f}, Bear: {avg_bear:.2f})",
                *(all_reasons[:1] or ["Bullish and bearish headlines are still balanced."]),
            ]
        
        signal = TradingSignal(
            ticker=", ".join(tickers),
            action=action,
            confidence=confidence,
            reasons=primary_reasons,
        )
        
        self.logger.info(
            "signal_generated",
            action=action,
            confidence=confidence,
        )
        
        return signal
    
    def _hold_signal(self, tickers: list[str], reason: str) -> TradingSignal:
        """Generate a HOLD signal with given reason."""
        return TradingSignal(
            ticker=", ".join(tickers),
            action="HOLD",
            confidence=0.5,
            reasons=[reason],
        )
