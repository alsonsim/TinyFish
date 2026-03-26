"""Script to create all TinyFish Financial Agent project files."""

import os

# File contents dictionary
files = {
    # src/__init__.py
    "src/__init__.py": '''"""TinyFish Financial Agent - AI-powered sentiment analysis for financial markets."""

__version__ = "0.1.0"
__author__ = "TinyFish Team"
__license__ = "MIT"
''',

    # src/agent/__init__.py
    "src/agent/__init__.py": '''"""Agent orchestration module for TinyFish Financial Agent."""

from .core import FinancialAgent
from .planner import AgentPlanner
from .executor import TinyFishExecutor

__all__ = ["FinancialAgent", "AgentPlanner", "TinyFishExecutor"]
''',

    # src/agent/core.py - Already provided in previous response
    
    # src/sources/__init__.py
    "src/sources/__init__.py": '''"""Data source modules for financial sentiment scraping."""

from .news import CNBCSource, BloombergSource
from .forums import RedditSource, StockTwitsSource
from .social import TwitterSource
from .crypto import CoinMarketCapSource

__all__ = [
    "CNBCSource",
    "BloombergSource",
    "RedditSource",
    "StockTwitsSource",
    "TwitterSource",
    "CoinMarketCapSource",
]
''',

    # src/sources/news.py
    "src/sources/news.py": '''"""News source scrapers (CNBC, Bloomberg)."""

from typing import Any
import structlog
from bs4 import BeautifulSoup

from src.agent.executor import TinyFishExecutor

logger = structlog.get_logger(__name__)


class CNBCSource:
    """Scraper for CNBC financial news."""
    
    def __init__(self, executor: TinyFishExecutor) -> None:
        self.executor = executor
        self.logger = logger.bind(source="cnbc")
        self.base_url = "https://www.cnbc.com"
    
    async def fetch_data(self, ticker: str) -> list[dict[str, Any]]:
        """
        Fetch CNBC articles related to ticker.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            List of article data dicts
        """
        self.logger.info("fetching_cnbc_data", ticker=ticker)
        
        try:
            # Navigate to search page
            url = f"{self.base_url}/search/?query={ticker}"
            html = await self.executor.fetch_page(url, wait_for=".SearchResult")
            
            # Parse articles
            soup = BeautifulSoup(html, "lxml")
            articles = []
            
            for article in soup.select(".SearchResult-searchResult"):
                title_elem = article.select_one(".SearchResult-searchResultTitle")
                desc_elem = article.select_one(".SearchResult-searchResultBody")
                
                if title_elem:
                    articles.append({
                        "source": "cnbc",
                        "ticker": ticker,
                        "title": title_elem.get_text(strip=True),
                        "text": desc_elem.get_text(strip=True) if desc_elem else "",
                        "url": title_elem.get("href", ""),
                    })
            
            self.logger.info("cnbc_fetch_complete", count=len(articles))
            return articles
            
        except Exception as e:
            self.logger.error("cnbc_fetch_failed", ticker=ticker, error=str(e))
            return []


class BloombergSource:
    """Scraper for Bloomberg financial news."""
    
    def __init__(self, executor: TinyFishExecutor) -> None:
        self.executor = executor
        self.logger = logger.bind(source="bloomberg")
        self.base_url = "https://www.bloomberg.com"
    
    async def fetch_data(self, ticker: str) -> list[dict[str, Any]]:
        """
        Fetch Bloomberg articles related to ticker.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            List of article data dicts
        """
        self.logger.info("fetching_bloomberg_data", ticker=ticker)
        
        try:
            url = f"{self.base_url}/search?query={ticker}"
            html = await self.executor.fetch_page(url, wait_for=".search-result")
            
            soup = BeautifulSoup(html, "lxml")
            articles = []
            
            for article in soup.select(".search-result-story"):
                title_elem = article.select_one("a")
                summary_elem = article.select_one(".summary")
                
                if title_elem:
                    articles.append({
                        "source": "bloomberg",
                        "ticker": ticker,
                        "title": title_elem.get_text(strip=True),
                        "text": summary_elem.get_text(strip=True) if summary_elem else "",
                        "url": self.base_url + title_elem.get("href", ""),
                    })
            
            self.logger.info("bloomberg_fetch_complete", count=len(articles))
            return articles
            
        except Exception as e:
            self.logger.error("bloomberg_fetch_failed", ticker=ticker, error=str(e))
            return []
''',

    # src/sources/forums.py
    "src/sources/forums.py": '''"""Forum source scrapers (Reddit, StockTwits)."""

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
''',

    # src/sources/social.py
    "src/sources/social.py": '''"""Social media source scrapers (Twitter/X, Discord)."""

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
            
            # TODO: Parse tweets from HTML (requires handling Twitter's dynamic loading)
            return [{
                "source": "twitter",
                "ticker": ticker,
                "text": f"Placeholder tweet about ${ticker}",
                "url": url,
            }]
            
        except Exception as e:
            self.logger.error("twitter_fetch_failed", ticker=ticker, error=str(e))
            return []
''',

    # src/sources/crypto.py
    "src/sources/crypto.py": '''"""Cryptocurrency source scrapers (CoinMarketCap, DefiLlama)."""

from typing import Any
import structlog

from src.agent.executor import TinyFishExecutor

logger = structlog.get_logger(__name__)


class CoinMarketCapSource:
    """Scraper for CoinMarketCap crypto data."""
    
    def __init__(self, executor: TinyFishExecutor) -> None:
        self.executor = executor
        self.logger = logger.bind(source="coinmarketcap")
        self.base_url = "https://coinmarketcap.com"
    
    async def fetch_data(self, ticker: str) -> list[dict[str, Any]]:
        """
        Fetch CoinMarketCap data for crypto ticker.
        
        Args:
            ticker: Crypto ticker symbol (e.g., BTC, ETH)
        
        Returns:
            List of data items
        """
        self.logger.info("fetching_cmc_data", ticker=ticker)
        
        try:
            url = f"{self.base_url}/currencies/{ticker.lower()}"
            html = await self.executor.fetch_page(url, wait_for=".price")
            
            # TODO: Parse CoinMarketCap data
            return [{
                "source": "coinmarketcap",
                "ticker": ticker,
                "text": f"Placeholder CoinMarketCap data for {ticker}",
                "url": url,
            }]
            
        except Exception as e:
            self.logger.error("cmc_fetch_failed", ticker=ticker, error=str(e))
            return []


class DefiLlamaSource:
    """Scraper for DefiLlama DeFi protocol data."""
    
    def __init__(self, executor: TinyFishExecutor) -> None:
        self.executor = executor
        self.logger = logger.bind(source="defillama")
        self.base_url = "https://defillama.com"
    
    async def fetch_data(self, protocol: str) -> list[dict[str, Any]]:
        """
        Fetch DefiLlama protocol data.
        
        Args:
            protocol: DeFi protocol name
        
        Returns:
            List of protocol data items
        """
        self.logger.info("fetching_defillama_data", protocol=protocol)
        
        try:
            url = f"{self.base_url}/protocol/{protocol.lower()}"
            html = await self.executor.fetch_page(url)
            
            # TODO: Parse DefiLlama data
            return [{
                "source": "defillama",
                "protocol": protocol,
                "text": f"Placeholder DefiLlama data for {protocol}",
                "url": url,
            }]
            
        except Exception as e:
            self.logger.error("defillama_fetch_failed", protocol=protocol, error=str(e))
            return []
''',

}

# Create all files
def create_files():
    for filepath, content in files.items():
        # Create directory if needed
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Created: {filepath}")

if __name__ == "__main__":
    print("Creating TinyFish Financial Agent files...")
    print()
    create_files()
    print()
    print("Files created successfully!")
    print("Next: Run setup.bat to create directories, then continue with remaining files")
