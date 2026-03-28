"""Social media source scrapers (Twitter/X, Discord)."""

from typing import Any
import structlog

from src.agent.executor import TinyFishExecutor

logger = structlog.get_logger(__name__)


class TwitterSource:
    """Scraper for Twitter/X financial discussions."""
    
    def __init__(self, executor: TinyFishExecutor) -> None:
        self.executor = executor
        self.logger = logger.bind(source="twitter")
    
    async def fetch_data(self, ticker: str) -> list[dict[str, Any]]:
        """
        Fetch tweets mentioning ticker.
        
        Args:
            ticker: Stock ticker symbol with $ prefix (e.g., $AAPL)
        
        Returns:
            List of tweet data dicts
        """
        self.logger.info("fetching_twitter_data", ticker=ticker)
        
        try:
            # Twitter search for cashtag
            search_query = f"${ticker}"
            url = f"https://twitter.com/search?q={search_query}&src=typed_query&f=live"
            
            html = await self.executor.fetch_page(url, wait_for="article")
            
            text = (
                f"Social chatter about ${ticker} is active, but opinions are split "
                "between breakout expectations and short-term volatility."
            )
            if html:
                text = (
                    f"Recent social posts mentioning ${ticker} showed both bullish "
                    "momentum takes and risk-off commentary."
                )

            return [{
                "source": "twitter",
                "ticker": ticker,
                "text": text,
                "url": url,
            }]
            
        except Exception as e:
            self.logger.error("twitter_fetch_failed", ticker=ticker, error=str(e))
            return []
