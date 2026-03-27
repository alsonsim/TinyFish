"""Tests for agent orchestration."""

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
