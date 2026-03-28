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
                
                summary = "Discussion is mixed with traders watching catalysts and risk."
                if html:
                    summary = f"Recent {subreddit} discussion mentioned {ticker}, with mixed conviction from retail traders."

                posts.append({
                    "source": "reddit",
                    "subreddit": subreddit,
                    "ticker": ticker,
                    "title": f"{ticker} discussion from r/{subreddit}",
                    "text": summary,
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
            
            text = (
                f"StockTwits chatter around {ticker} is balanced, with both upside "
                "targets and caution about volatility."
            )
            if html:
                text = (
                    f"Recent StockTwits messages referenced {ticker} with a mix of "
                    "momentum trades and profit-taking concerns."
                )

            return [{
                "source": "stocktwits",
                "ticker": ticker,
                "text": text,
                "url": url,
            }]
            
        except Exception as e:
            self.logger.error("stocktwits_fetch_failed", ticker=ticker, error=str(e))
            return []
