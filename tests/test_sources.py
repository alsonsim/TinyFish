"""Tests for data sources."""

import pytest
from src.sources.news import CNBCSource, BloombergSource
from src.agent.executor import TinyFishExecutor


@pytest.fixture
def mock_executor():
    """Create a mock executor."""
    executor = TinyFishExecutor(api_key="test-key")
    executor.fetch_page = pytest.AsyncMock(
        return_value="<html><body>Test content</body></html>"
    )
    return executor


@pytest.mark.asyncio
async def test_cnbc_source(mock_executor):
    """Test CNBC source scraping."""
    source = CNBCSource(executor=mock_executor)
    
    data = await source.fetch_data("AAPL")
    
    # Should return data (even if mocked/empty)
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_bloomberg_source(mock_executor):
    """Test Bloomberg source scraping."""
    source = BloombergSource(executor=mock_executor)
    
    data = await source.fetch_data("TSLA")
    
    assert isinstance(data, list)
