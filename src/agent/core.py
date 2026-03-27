"""Main agent orchestration for TinyFish Financial Agent."""

import asyncio
from typing import Any

import structlog

from src.agent.executor import TinyFishExecutor
from src.agent.planner import AgentPlanner
from src.data.models import SentimentScore, TradingSignal
from src.sentiment.analyzer import SentimentAnalyzer
from src.sentiment.signals import SignalGenerator
from src.sources.news import CNBCSource, BloombergSource
from src.sources.forums import RedditSource, StockTwitsSource
from src.sources.social import TwitterSource
from src.sources.crypto import CoinMarketCapSource

logger = structlog.get_logger(__name__)


class FinancialAgent:
    """
    Central orchestrator that coordinates data collection, sentiment
    analysis, and trading signal generation.

    Example:
        >>> agent = FinancialAgent(openai_api_key="sk-...", tinyfish_key="tf-...")
        >>> signal = await agent.monitor_sentiment(["AAPL", "TSLA"])
        >>> print(signal.action, signal.confidence)
    """

    def __init__(
        self,
        openai_api_key: str,
        tinyfish_key: str,
        settings: Any = None,
    ) -> None:
        self.settings = settings
        self.logger = logger.bind(component="financial_agent")

        # Core components
        self.executor = TinyFishExecutor(api_key=tinyfish_key)
        self.planner = AgentPlanner(openai_api_key=openai_api_key)
        self.analyzer = SentimentAnalyzer(openai_api_key=openai_api_key)

        threshold = getattr(settings, "sentiment_threshold", 0.7) if settings else 0.7
        self.signal_generator = SignalGenerator(
            bull_threshold=threshold,
            bear_threshold=threshold,
        )

        # Data sources
        self.sources = [
            CNBCSource(executor=self.executor),
            BloombergSource(executor=self.executor),
            RedditSource(executor=self.executor),
            StockTwitsSource(executor=self.executor),
            TwitterSource(executor=self.executor),
            CoinMarketCapSource(executor=self.executor),
        ]

        self.logger.info("financial_agent_initialized")

    async def monitor_sentiment(self, tickers: list[str]) -> TradingSignal:
        """
        Run the full pipeline: plan -> collect -> analyze -> signal.

        Args:
            tickers: Ticker symbols to monitor

        Returns:
            Trading signal with action and confidence
        """
        self.logger.info("monitoring_sentiment", tickers=tickers)

        # 1. Plan collection strategy
        plan = await self.planner.create_plan(tickers)
        self.logger.info("plan_ready", sources=plan.priority_sources)

        # 2. Collect data from sources
        data = await self._collect_data(tickers)

        # 3. Analyze sentiment
        scores = await self._analyze_sentiment(tickers, data)

        # 4. Generate trading signal
        signal = await self.signal_generator.generate(scores, tickers)

        self.logger.info(
            "monitoring_complete",
            action=signal.action,
            confidence=signal.confidence,
        )
        return signal

    async def _collect_data(self, tickers: list[str]) -> list[dict[str, Any]]:
        """Collect data from all sources in parallel."""
        self.logger.info("collecting_data", tickers=tickers)

        all_data: list[dict[str, Any]] = []

        tasks = [
            source.fetch_data(ticker)
            for ticker in tickers
            for source in self.sources
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_data.extend(result)
            elif isinstance(result, Exception):
                self.logger.warning("source_failed", error=str(result))

        self.logger.info("data_collected", item_count=len(all_data))
        return all_data

    async def _analyze_sentiment(
        self,
        tickers: list[str],
        data: list[dict[str, Any]],
    ) -> list[SentimentScore]:
        """Analyze sentiment for each ticker from collected data."""
        self.logger.info("analyzing_sentiment", tickers=tickers)

        # Group data by ticker
        by_ticker: dict[str, list[dict[str, Any]]] = {t: [] for t in tickers}
        for item in data:
            ticker = item.get("ticker", "")
            if ticker in by_ticker:
                by_ticker[ticker].append(item)

        # Analyze each ticker
        items = [(ticker, items) for ticker, items in by_ticker.items()]
        scores = await self.analyzer.batch_analyze(items)

        self.logger.info("sentiment_analyzed", score_count=len(scores))
        return scores

    async def cleanup(self) -> None:
        """Release all resources."""
        self.logger.info("cleaning_up")
        await self.executor.close()
