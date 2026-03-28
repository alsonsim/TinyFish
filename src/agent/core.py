"""Main agent orchestration for TinyFish Financial Agent."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from src.agent.executor import TinyFishExecutor
from src.agent.planner import AgentPlanner
from src.data.models import SentimentScore, TradingSignal
from src.sentiment.analyzer import SentimentAnalyzer
from src.sentiment.signals import SignalGenerator
from src.sources.news import BloombergAsiaSource, YahooFinanceSingaporeSource

logger = structlog.get_logger(__name__)


class FinancialAgent:
    """Coordinate TinyFish collection, OpenAI analysis, and signal generation."""

    def __init__(
        self,
        openai_api_key: str | None,
        tinyfish_key: str | None,
        settings: Any = None,
    ) -> None:
        self.settings = settings
        self.logger = logger.bind(component="financial_agent")

        self.executor = TinyFishExecutor(
            api_key=tinyfish_key,
            headless=getattr(settings, "tinyfish_headless", True),
        )
        self.planner = AgentPlanner(
            openai_api_key=openai_api_key,
            model=getattr(settings, "openai_model", "gpt-5.4"),
        )
        self.analyzer = SentimentAnalyzer(
            openai_api_key=openai_api_key,
            model=getattr(settings, "openai_model", "gpt-5.4"),
        )

        threshold = getattr(settings, "sentiment_threshold", 0.7) if settings else 0.7
        self.signal_generator = SignalGenerator(
            bull_threshold=threshold,
            bear_threshold=threshold,
        )

        self.sources = [
            YahooFinanceSingaporeSource(executor=self.executor),
            BloombergAsiaSource(executor=self.executor),
        ]
        self.source_groups = {
            "news": self.sources,
        }

        self.logger.info("financial_agent_initialized")

    async def analyze_market(self, tickers: list[str]) -> dict[str, Any]:
        """Run the full market-analysis pipeline and return detailed artifacts."""
        self.logger.info("monitoring_sentiment", tickers=tickers)

        plan = await self.planner.create_plan(tickers)
        self.logger.info("plan_ready", sources=plan.priority_sources)

        data = await self._collect_data(tickers, plan.priority_sources)
        scores = await self._analyze_sentiment(tickers, data)
        signal = await self.signal_generator.generate(scores, tickers)
        per_ticker = self._build_ticker_breakdown(tickers, data, scores)

        # Auto-store results in history
        try:
            from src.data.history import get_sentiment_history
            history = get_sentiment_history()
            history.store_analysis(signal, scores)
        except Exception as exc:
            self.logger.warning("history_storage_failed", error=str(exc))

        self.logger.info(
            "monitoring_complete",
            action=signal.action,
            confidence=signal.confidence,
        )
        return {
            "plan": plan,
            "signal": signal,
            "scores": scores,
            "data": data,
            "per_ticker": per_ticker,
        }

    async def monitor_sentiment(self, tickers: list[str]) -> TradingSignal:
        """Compatibility wrapper that returns only the final trading signal."""
        result = await self.analyze_market(tickers)
        return result["signal"]

    async def _collect_data(
        self,
        tickers: list[str],
        source_groups: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        self.logger.info("collecting_data", tickers=tickers)

        all_data: list[dict[str, Any]] = []
        selected_sources = self._select_sources(source_groups or [])

        tasks = [
            source.fetch_data(ticker)
            for ticker in tickers
            for source in selected_sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_data.extend(result)
            elif isinstance(result, Exception):
                self.logger.warning("source_failed", error=str(result))

        self.logger.info("data_collected", item_count=len(all_data))
        return all_data

    def _select_sources(self, source_groups: list[str]) -> list[Any]:
        selected: list[Any] = []
        for group in source_groups:
            selected.extend(self.source_groups.get(group, []))
        return selected or list(self.sources)

    async def _analyze_sentiment(
        self,
        tickers: list[str],
        data: list[dict[str, Any]],
    ) -> list[SentimentScore]:
        self.logger.info("analyzing_sentiment", tickers=tickers)

        by_ticker: dict[str, list[dict[str, Any]]] = {ticker: [] for ticker in tickers}
        for item in data:
            ticker = item.get("ticker", "")
            if ticker in by_ticker:
                by_ticker[ticker].append(item)

        items = [(ticker, ticker_items) for ticker, ticker_items in by_ticker.items()]
        scores = await self.analyzer.batch_analyze(items)

        self.logger.info("sentiment_analyzed", score_count=len(scores))
        return scores

    def _build_ticker_breakdown(
        self,
        tickers: list[str],
        data: list[dict[str, Any]],
        scores: list[SentimentScore],
    ) -> dict[str, Any]:
        score_map = {score.ticker: score for score in scores}
        output: dict[str, Any] = {}

        for ticker in tickers:
            items = [item for item in data if item.get("ticker") == ticker]
            bullish_news = [item for item in items if item.get("stance") == "bullish"]
            bearish_news = [item for item in items if item.get("stance") == "bearish"]
            neutral_news = [item for item in items if item.get("stance") == "neutral"]
            score = score_map.get(ticker)

            output[ticker] = {
                "score": score.model_dump() if score else None,
                "bullish_news": bullish_news,
                "bearish_news": bearish_news,
                "neutral_news": neutral_news,
                "all_news": items,
            }

        return output

    async def cleanup(self) -> None:
        self.logger.info("cleaning_up")
        await self.executor.close()
