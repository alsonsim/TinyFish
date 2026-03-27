"""Tests for sentiment analysis."""

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
