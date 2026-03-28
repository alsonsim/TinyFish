"""LLM-based data collection planning."""

from typing import Any

import structlog

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - optional dependency
    AsyncOpenAI = None  # type: ignore[assignment]

from src.data.models import CollectionPlan

logger = structlog.get_logger(__name__)


class _UnavailableCompletions:
    async def create(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("OpenAI client is unavailable")


class _UnavailableChat:
    def __init__(self) -> None:
        self.completions = _UnavailableCompletions()


class _UnavailableClient:
    def __init__(self) -> None:
        self.chat = _UnavailableChat()


class AgentPlanner:
    """
    Uses GPT-4 to plan which sources to query and in what order.

    Example:
        >>> planner = AgentPlanner(openai_api_key="sk-...")
        >>> plan = await planner.create_plan(["AAPL", "BTC"])
    """

    def __init__(
        self,
        openai_api_key: str | None,
        model: str = "gpt-4-turbo-preview",
    ) -> None:
        self.client = (
            AsyncOpenAI(api_key=openai_api_key)
            if AsyncOpenAI and openai_api_key
            else _UnavailableClient()
        )
        self.model = model
        self.enabled = AsyncOpenAI is not None and bool(openai_api_key)
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

        if not self.enabled:
            return self._default_plan(tickers)

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
        return f"""
        Plan data collection for these tickers: {', '.join(tickers)}

        Available sources: news (Yahoo Finance Singapore, Bloomberg Asia)

        Respond with:
        Priority Sources: source1
        Parallel Count: N
        Reasoning: your reasoning here
        """

    def _parse_plan(self, tickers: list[str], reasoning: str) -> CollectionPlan:
        """Parse LLM response into a CollectionPlan."""
        sources = ["news"]
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
            priority_sources=["news"],
            reasoning="Default plan (LLM planning unavailable or disabled)",
            parallel_sources=2,
        )
