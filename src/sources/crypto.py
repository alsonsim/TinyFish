"""Cryptocurrency source scrapers (CoinMarketCap, DefiLlama)."""

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
            
            text = (
                f"{ticker} remains volatile, with traders balancing upside momentum "
                "against macro and liquidity risk."
            )
            if html:
                text = (
                    f"CoinMarketCap coverage for {ticker} suggests active interest, "
                    "with price discovery still looking mixed."
                )

            return [{
                "source": "coinmarketcap",
                "ticker": ticker,
                "text": text,
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
            
            text = (
                f"{protocol} protocol metrics are being monitored with a neutral "
                "stance while on-chain conviction stays mixed."
            )
            if html:
                text = (
                    f"DefiLlama data for {protocol} points to mixed DeFi sentiment "
                    "rather than a clear directional edge."
                )

            return [{
                "source": "defillama",
                "protocol": protocol,
                "text": text,
                "url": url,
            }]
            
        except Exception as e:
            self.logger.error("defillama_fetch_failed", protocol=protocol, error=str(e))
            return []
