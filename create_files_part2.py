"""Complete file creation script for TinyFish Financial Agent - Part 2: Sentiment & Data modules."""

import os

files = {
    # src/sentiment/__init__.py
    "src/sentiment/__init__.py": '''"""Sentiment analysis modules using OpenAI GPT-4."""

from .analyzer import SentimentAnalyzer
from .signals import SignalGenerator
from .scorer import SentimentScorer

__all__ = ["SentimentAnalyzer", "SignalGenerator", "SentimentScorer"]
''',

    # src/sentiment/analyzer.py
    "src/sentiment/analyzer.py": '''"""OpenAI GPT-4 sentiment extraction and analysis."""

from typing import Any
import structlog
from openai import AsyncOpenAI

from src.data.models import SentimentScore

logger = structlog.get_logger(__name__)


class SentimentAnalyzer:
    """
    Uses OpenAI GPT-4 to analyze financial sentiment from text.
    
    Example:
        >>> analyzer = SentimentAnalyzer(openai_api_key="sk-...")
        >>> score = await analyzer.analyze_ticker("AAPL", [{"text": "Apple stock soars!"}])
        >>> print(f"Sentiment: {score.sentiment}, Bull: {score.bull_score}")
    """
    
    def __init__(
        self,
        openai_api_key: str,
        model: str = "gpt-4-turbo-preview",
    ) -> None:
        """
        Initialize the sentiment analyzer.
        
        Args:
            openai_api_key: OpenAI API key
            model: GPT model to use
        """
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.model = model
        self.logger = logger.bind(component="sentiment_analyzer")
    
    async def analyze_ticker(
        self,
        ticker: str,
        data_items: list[dict[str, Any]],
    ) -> SentimentScore:
        """
        Analyze sentiment for a specific ticker across data items.
        
        Args:
            ticker: Stock ticker symbol
            data_items: List of text data items to analyze
        
        Returns:
            Aggregated sentiment score
        """
        self.logger.info("analyzing_ticker", ticker=ticker, item_count=len(data_items))
        
        if not data_items:
            return self._neutral_score(ticker)
        
        # Combine all texts
        combined_text = "\\n\\n".join(
            item.get("text", "") or item.get("title", "")
            for item in data_items
        )[:8000]  # Limit to avoid token limits
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(ticker, combined_text)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial sentiment analysis expert. Analyze market sentiment objectively.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            
            analysis = response.choices[0].message.content
            self.logger.debug("llm_analysis", analysis=analysis)
            
            # Parse sentiment from response
            score = self._parse_sentiment(ticker, analysis)
            
            return score
            
        except Exception as e:
            self.logger.error("analysis_failed", ticker=ticker, error=str(e))
            return self._neutral_score(ticker)
    
    def _build_analysis_prompt(self, ticker: str, text: str) -> str:
        """Build the sentiment analysis prompt."""
        return f"""
        Analyze the overall market sentiment for {ticker} based on the following content:
        
        {text}
        
        Provide:
        1. Bull score (0.0 - 1.0): How bullish is the sentiment?
        2. Bear score (0.0 - 1.0): How bearish is the sentiment?
        3. Overall sentiment: BULL, BEAR, or NEUTRAL
        4. Key reasons (2-3 bullet points)
        
        Format your response as:
        Bull Score: X.XX
        Bear Score: X.XX
        Sentiment: [BULL/BEAR/NEUTRAL]
        Reasons:
        - Reason 1
        - Reason 2
        """
    
    def _parse_sentiment(self, ticker: str, analysis: str | None) -> SentimentScore:
        """Parse LLM response into structured sentiment score."""
        if not analysis:
            return self._neutral_score(ticker)
        
        try:
            # Extract scores using simple parsing
            lines = analysis.split("\\n")
            
            bull_score = 0.5
            bear_score = 0.5
            sentiment = "NEUTRAL"
            reasons = []
            
            for line in lines:
                line = line.strip()
                
                if line.startswith("Bull Score:"):
                    try:
                        bull_score = float(line.split(":")[1].strip())
                    except:
                        pass
                
                elif line.startswith("Bear Score:"):
                    try:
                        bear_score = float(line.split(":")[1].strip())
                    except:
                        pass
                
                elif line.startswith("Sentiment:"):
                    sentiment_text = line.split(":")[1].strip().upper()
                    if sentiment_text in ["BULL", "BEAR", "NEUTRAL"]:
                        sentiment = sentiment_text
                
                elif line.startswith("-"):
                    reasons.append(line[1:].strip())
            
            return SentimentScore(
                ticker=ticker,
                bull_score=bull_score,
                bear_score=bear_score,
                sentiment=sentiment,
                reasons=reasons,
            )
            
        except Exception as e:
            self.logger.error("sentiment_parsing_failed", error=str(e))
            return self._neutral_score(ticker)
    
    def _neutral_score(self, ticker: str) -> SentimentScore:
        """Return a neutral sentiment score."""
        return SentimentScore(
            ticker=ticker,
            bull_score=0.5,
            bear_score=0.5,
            sentiment="NEUTRAL",
            reasons=["Insufficient data for analysis"],
        )
    
    async def batch_analyze(
        self,
        items: list[tuple[str, list[dict[str, Any]]]],
    ) -> list[SentimentScore]:
        """
        Analyze multiple tickers in batch.
        
        Args:
            items: List of (ticker, data_items) tuples
        
        Returns:
            List of sentiment scores
        """
        import asyncio
        
        tasks = [
            self.analyze_ticker(ticker, data)
            for ticker, data in items
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        scores = []
        for result in results:
            if isinstance(result, SentimentScore):
                scores.append(result)
            else:
                self.logger.warning("batch_item_failed", error=str(result))
        
        return scores
''',

    # src/sentiment/signals.py
    "src/sentiment/signals.py": '''"""Trading signal generation from sentiment scores."""

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
        for score in sentiment_scores:
            all_reasons.extend(score.reasons)
        
        # Determine action
        action: Literal["BUY", "SELL", "HOLD"]
        confidence: float
        
        if avg_bull > self.bull_threshold and avg_bull > avg_bear:
            action = "BUY"
            confidence = avg_bull
            primary_reasons = [
                f"Strong bullish sentiment ({avg_bull:.2f})",
                *all_reasons[:2],
            ]
        
        elif avg_bear > self.bear_threshold and avg_bear > avg_bull:
            action = "SELL"
            confidence = avg_bear
            primary_reasons = [
                f"Strong bearish sentiment ({avg_bear:.2f})",
                *all_reasons[:2],
            ]
        
        else:
            action = "HOLD"
            confidence = 1.0 - abs(avg_bull - avg_bear)  # Confidence in neutral stance
            primary_reasons = [
                f"Mixed sentiment (Bull: {avg_bull:.2f}, Bear: {avg_bear:.2f})",
                "Waiting for clearer signals",
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
''',

    # src/sentiment/scorer.py
    "src/sentiment/scorer.py": '''"""Sentiment scoring utilities."""

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
    print("Creating sentiment and data module files...")
    print()
    create_files()
    print()
    print("Part 2 complete!")
