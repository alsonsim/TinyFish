"""LLM-based data collection planning."""

from typing import Any

import structlog
from openai import AsyncOpenAI

from src.data.models import CollectionPlan

logger = structlog.get_logger(__name__)


class AgentPlanner:
    """
    Uses GPT-4 to plan which sources to query and in what order.

    Example:
        >>> planner = AgentPlanner(openai_api_key="sk-...")
        >>> plan = await planner.create_plan(["AAPL", "BTC"])
    """

    def __init__(
        self,
        openai_api_key: str,
        model: str = "gpt-4-turbo-preview",
    ) -> None:
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.model = model
        self.logger = logger.bind(component="agent_planner")

    async def create_plan(self, tickers: list[str]) -> CollectionPlan:
        """
        Create a data collection plan for the given tickers.

        Args:
            tickers: Ticker symbols to plan collection for

        Returns:
            Collection plan with prioritized sources
        """
        self.logger.info("creating_plan", tickers=tickers)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a financial data collection planner. "
                            "Given ticker symbols, determine the best sources "
                            "to query and in what order."
                        ),
                    },
                    {
                        "role": "user",
                        "content": self._build_prompt(tickers),
                    },
                ],
                temperature=0.3,
            )

            reasoning = response.choices[0].message.content or ""
            plan = self._parse_plan(tickers, reasoning)

            self.logger.info(
                "plan_created",
                sources=plan.priority_sources,
                parallel=plan.parallel_sources,
            )
            return plan

        except Exception as e:
            self.logger.error("planning_failed", error=str(e))
            return self._default_plan(tickers)

    def _build_prompt(self, tickers: list[str]) -> str:
        """Build the planning prompt."""
        has_crypto = any(t in ("BTC", "ETH", "SOL", "DOGE") for t in tickers)
        has_stocks = any(t not in ("BTC", "ETH", "SOL", "DOGE") for t in tickers)

        return f"""
        Plan data collection for these tickers: {', '.join(tickers)}

        Available sources: news (CNBC, Bloomberg), forums (Reddit, StockTwits),
        social (Twitter), crypto (CoinMarketCap, DefiLlama)

        {'Include crypto sources.' if has_crypto else ''}
        {'Include stock news sources.' if has_stocks else ''}

        Respond with:
        Priority Sources: source1, source2, source3
        Parallel Count: N
        Reasoning: your reasoning here
        """

    def _parse_plan(self, tickers: list[str], reasoning: str) -> CollectionPlan:
        """Parse LLM response into a CollectionPlan."""
        sources = ["news", "forums", "social"]
        parallel = 2

        for line in reasoning.split("\n"):
            line = line.strip()
            if line.startswith("Priority Sources:"):
                sources = [s.strip() for s in line.split(":")[1].split(",")]
            elif line.startswith("Parallel Count:"):
                try:
                    parallel = int(line.split(":")[1].strip())
                except ValueError:
                    pass

        return CollectionPlan(
            tickers=tickers,
            priority_sources=sources,
            reasoning=reasoning,
            parallel_sources=max(1, min(5, parallel)),
        )

    def _default_plan(self, tickers: list[str]) -> CollectionPlan:
        """Return a default plan when LLM planning fails."""
        return CollectionPlan(
            tickers=tickers,
            priority_sources=["news", "forums", "social"],
            reasoning="Default plan (LLM planning unavailable)",
            parallel_sources=2,
        )
