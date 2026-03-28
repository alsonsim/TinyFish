"""Tests for data sources."""

import pytest
from unittest.mock import AsyncMock

from src.sources.news import CNBCSource, BloombergSource
from src.agent.executor import TinyFishExecutor


@pytest.fixture
def mock_executor():
    """Create a mock executor."""
    executor = TinyFishExecutor(api_key="test-key")
    executor.run_extraction = AsyncMock(
        return_value={
            "items": [
                {
                    "headline": "AAPL climbs after upbeat guidance",
                    "summary": "Investors reacted positively to guidance.",
                    "url": "https://example.com/aapl",
                    "stance": "bullish",
                    "rationale": "Guidance improved",
                }
            ]
        }
    )
    return executor


@pytest.mark.asyncio
async def test_cnbc_source(mock_executor):
    """Test Yahoo alias source scraping."""
    source = CNBCSource(executor=mock_executor)

    data = await source.fetch_data("AAPL")

    assert isinstance(data, list)
    assert data[0]["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_bloomberg_source(mock_executor):
    """Test Bloomberg Asia scraping."""
    source = BloombergSource(executor=mock_executor)

    data = await source.fetch_data("TSLA")

    assert isinstance(data, list)
    assert data[0]["ticker"] == "TSLA"
