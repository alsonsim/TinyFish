"""News source scrapers (CNBC, Bloomberg)."""

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
