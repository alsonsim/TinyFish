"""Forum source scrapers (Reddit, StockTwits)."""

from typing import Any
import structlog

from src.agent.executor import TinyFishExecutor

logger = structlog.get_logger(__name__)


class RedditSource:
    """Scraper for Reddit financial discussions."""
    
    def __init__(
        self,
        executor: TinyFishExecutor,
        subreddits: list[str] | None = None,
    ) -> None:
        self.executor = executor
        self.subreddits = subreddits or ["wallstreetbets", "stocks", "investing"]
        self.logger = logger.bind(source="reddit")
    
    async def fetch_data(self, ticker: str) -> list[dict[str, Any]]:
        """
        Fetch Reddit posts mentioning ticker.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            List of post data dicts
        """
        self.logger.info("fetching_reddit_data", ticker=ticker)
        
        posts = []
        
        for subreddit in self.subreddits:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/search?q={ticker}&restrict_sr=1&sort=new"
                html = await self.executor.fetch_page(url)
                
                # TODO: Parse Reddit posts from HTML
                # For now, placeholder
                posts.append({
                    "source": "reddit",
                    "subreddit": subreddit,
                    "ticker": ticker,
                    "title": f"Placeholder Reddit post about {ticker}",
                    "text": "Placeholder content",
                    "url": url,
                })
                
            except Exception as e:
                self.logger.error(
                    "reddit_fetch_failed",
                    subreddit=subreddit,
                    error=str(e),
                )
        
        return posts


class StockTwitsSource:
    """Scraper for StockTwits social sentiment."""
    
    def __init__(self, executor: TinyFishExecutor) -> None:
        self.executor = executor
        self.logger = logger.bind(source="stocktwits")
        self.base_url = "https://stocktwits.com"
    
    async def fetch_data(self, ticker: str) -> list[dict[str, Any]]:
        """
        Fetch StockTwits messages for ticker.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            List of message data dicts
        """
        self.logger.info("fetching_stocktwits_data", ticker=ticker)
        
        try:
            url = f"{self.base_url}/symbol/{ticker}"
            html = await self.executor.fetch_page(url, wait_for=".stream")
            
            # TODO: Parse StockTwits messages
            return [{
                "source": "stocktwits",
                "ticker": ticker,
                "text": f"Placeholder StockTwits message about {ticker}",
                "url": url,
            }]
            
        except Exception as e:
            self.logger.error("stocktwits_fetch_failed", ticker=ticker, error=str(e))
            return []
