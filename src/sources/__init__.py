"""Data source modules for financial sentiment scraping."""

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
