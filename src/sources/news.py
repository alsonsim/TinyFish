"""News source scrapers backed by TinyFish automation."""

from __future__ import annotations

import json
import re
from html import unescape
from typing import Any

import structlog

from src.agent.executor import TinyFishExecutor

logger = structlog.get_logger(__name__)


class _TinyFishNewsSource:
    """Common TinyFish-backed extraction flow for market-news sources."""

    source_name = "news"
    base_url = ""
    country_code: str | None = None
    timeout_seconds = 120

    def __init__(self, executor: TinyFishExecutor) -> None:
        self.executor = executor
        self.logger = logger.bind(source=self.source_name)

    async def fetch_data(self, ticker: str) -> list[dict[str, Any]]:
        self.logger.info("fetching_source_data", ticker=ticker)
        try:
            payload = await self.executor.run_extraction(
                url=self.build_url(ticker),
                goal=self._build_goal(ticker),
                country_code=self.country_code,
                timeout_seconds=self.timeout_seconds,
            )
            items = self._normalize_items(ticker, payload)
            if items:
                self.logger.info("source_fetch_complete", ticker=ticker, count=len(items))
                return items
        except Exception as exc:
            self.logger.error("source_fetch_failed", ticker=ticker, error=str(exc))

        direct_items = await self._fallback_fetch_data(ticker)
        if direct_items:
            self.logger.info("source_fetch_complete_direct", ticker=ticker, count=len(direct_items))
            return direct_items

        return [self._fallback_item(ticker)]

    async def _fallback_fetch_data(self, ticker: str) -> list[dict[str, Any]]:
        return []

    def build_url(self, ticker: str) -> str:
        return self.base_url

    def _build_goal(self, ticker: str) -> str:
        return (
            f"Extract up to 4 visible news items on this page that are clearly about {ticker}. "
            "Return strict JSON only using this schema: "
            '{"items":[{"headline":"", "summary":"", "url":"", '
            '"stance":"bullish|bearish|neutral", "rationale":""}]}. '
            "Do not browse to unrelated pages. If the page has no relevant items, return {\"items\": []}."
        )

    @property
    def display_name(self) -> str:
        return self.source_name.replace("_", " ").title()

    def _normalize_items(self, ticker: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        items = self._extract_candidate_items(payload)
        normalized: list[dict[str, Any]] = []

        for item in items:
            title = str(item.get("headline") or item.get("title") or "").strip()
            summary = str(item.get("summary") or item.get("text") or item.get("description") or "").strip()
            url = str(item.get("url") or item.get("link") or self.build_url(ticker)).strip()
            stance = str(item.get("stance") or item.get("sentiment") or "neutral").strip().lower()
            rationale = str(item.get("rationale") or item.get("why") or "").strip()

            if not title and not summary:
                continue
            if stance not in {"bullish", "bearish", "neutral"}:
                stance = self._classify_stance(f"{title} {summary}")
                rationale = rationale or "Derived from headline and summary wording."

            normalized.append(
                {
                    "source": self.source_name,
                    "ticker": ticker,
                    "title": title or f"{ticker} market update",
                    "text": summary or rationale or "No summary returned by the source",
                    "url": url,
                    "stance": stance,
                    "rationale": rationale,
                    "metadata": {
                        "publisher": self.display_name,
                    },
                }
            )

        return normalized[:4]

    def _extract_candidate_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("items", "news", "results", "articles"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

        if isinstance(payload.get("data"), dict):
            nested = self._extract_candidate_items(payload["data"])
            if nested:
                return nested

        text = payload.get("text") or payload.get("raw")
        if isinstance(text, str):
            try:
                decoded = json.loads(text)
            except json.JSONDecodeError:
                return []
            if isinstance(decoded, dict):
                return self._extract_candidate_items(decoded)
            if isinstance(decoded, list):
                return [item for item in decoded if isinstance(item, dict)]

        return []

    def _classify_stance(self, text: str) -> str:
        lowered = text.lower()
        bullish_terms = ["beat", "surge", "growth", "gain", "strong", "upgrade", "record", "boost"]
        bearish_terms = ["drop", "slip", "fall", "miss", "weak", "cut", "risk", "lawsuit", "tepid"]
        bullish_hits = sum(term in lowered for term in bullish_terms)
        bearish_hits = sum(term in lowered for term in bearish_terms)
        if bullish_hits > bearish_hits:
            return "bullish"
        if bearish_hits > bullish_hits:
            return "bearish"
        return "neutral"

    def _fallback_item(self, ticker: str) -> dict[str, Any]:
        return {
            "source": self.source_name,
            "ticker": ticker,
            "title": f"{ticker} coverage unavailable on {self.display_name}",
            "text": (
                f"TinyFish did not return a structured news set from {self.display_name}, "
                "so the dashboard is holding a neutral placeholder instead."
            ),
            "url": self.build_url(ticker),
            "stance": "neutral",
            "rationale": "No structured response was returned for this source.",
            "metadata": {
                "publisher": self.display_name,
            },
        }


class YahooFinanceSingaporeSource(_TinyFishNewsSource):
    source_name = "yahoo_finance_sg"
    base_url = "https://sg.finance.yahoo.com/"
    country_code = None

    @property
    def display_name(self) -> str:
        return "Yahoo Finance Singapore"

    def build_url(self, ticker: str) -> str:
        return f"https://sg.finance.yahoo.com/quote/{ticker}"

    async def _fallback_fetch_data(self, ticker: str) -> list[dict[str, Any]]:
        html = await self.executor.fetch_page(self.build_url(ticker))
        if not html:
            return []

        anchor_pattern = re.compile(
            r'<a(?P<attrs>[^>]+)href="(?P<href>https://sg\.finance\.yahoo\.com/news/[^"]+)"(?P<tail>[^>]*)>',
            re.S,
        )
        attr_pattern = re.compile(r'(?:aria-label|title)="([^"]+)"')
        seen: set[str] = set()
        items: list[dict[str, Any]] = []

        for attrs, href, tail in anchor_pattern.findall(html):
            if href in seen:
                continue
            seen.add(href)
            attr_text = f"{attrs} {tail}"
            match = attr_pattern.search(attr_text)
            if not match:
                continue
            title = unescape(match.group(1)).strip()
            if not title:
                continue
            stance = self._classify_stance(title)
            items.append(
                {
                    "source": self.source_name,
                    "ticker": ticker,
                    "title": title,
                    "text": title,
                    "url": href,
                    "stance": stance,
                    "rationale": "Derived from Yahoo Finance Singapore quote-page headline wording.",
                    "metadata": {"publisher": self.display_name},
                }
            )
            if len(items) >= 4:
                break
        return items


class BloombergAsiaSource(_TinyFishNewsSource):
    source_name = "bloomberg_asia"
    base_url = "https://www.bloomberg.com/asia"
    country_code = None

    @property
    def display_name(self) -> str:
        return "Bloomberg Asia"

    def build_url(self, ticker: str) -> str:
        return f"https://www.bloomberg.com/search?query={ticker}"


CNBCSource = YahooFinanceSingaporeSource
BloombergSource = BloombergAsiaSource
