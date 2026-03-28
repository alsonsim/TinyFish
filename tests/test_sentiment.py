"""Tests for sentiment analysis."""

import pytest

from src.sentiment.analyzer import SentimentAnalyzer
from src.sentiment.signals import SignalGenerator
from src.data.models import SentimentScore


@pytest.mark.asyncio
async def test_sentiment_analyzer_heuristic_flow():
    """Test heuristic sentiment analysis from stance-tagged news."""
    analyzer = SentimentAnalyzer(openai_api_key=None)

    score = await analyzer.analyze_ticker(
        "AAPL",
        [
            {
                "source": "yahoo_finance_sg",
                "title": "Apple rallies on stronger iPhone demand",
                "text": "Demand outlook improved after the latest update.",
                "stance": "bullish",
                "rationale": "Demand momentum improved",
            },
            {
                "source": "bloomberg_asia",
                "title": "Apple faces supply chain pressure",
                "text": "Margins could be pressured by supplier constraints.",
                "stance": "bearish",
                "rationale": "Supply chain pressure may weigh on margins",
            },
        ],
    )

    assert score.ticker == "AAPL"
    assert 0 <= score.bull_score <= 1
    assert 0 <= score.bear_score <= 1
    assert score.summary


def test_signal_generator():
    """Test signal generation logic."""
    generator = SignalGenerator(bull_threshold=0.7, bear_threshold=0.7)

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
            bullish_points=["Yahoo Finance Singapore: demand outlook improved"],
            bearish_points=[],
            summary="Bullish headlines dominate.",
        )
    ]

    signal = await generator.generate(scores, ["AAPL"])

    assert signal.action == "BUY"
    assert signal.confidence > 0.7
