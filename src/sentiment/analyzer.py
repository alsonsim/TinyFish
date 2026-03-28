"""OpenAI-backed sentiment extraction with heuristic fallback."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import structlog

from src.data.models import SentimentScore
from src.sentiment.scorer import SentimentScorer

logger = structlog.get_logger(__name__)


class SentimentAnalyzer:
    """Analyze ticker sentiment from collected news evidence."""

    def __init__(
        self,
        openai_api_key: str | None,
        model: str = "gpt-5.4",
    ) -> None:
        self.api_key = openai_api_key
        self.model = model
        self.enabled = bool(openai_api_key)
        self.scorer = SentimentScorer()
        self.logger = logger.bind(component="sentiment_analyzer")

    async def analyze_ticker(
        self,
        ticker: str,
        data_items: list[dict[str, Any]],
    ) -> SentimentScore:
        """Analyze one ticker from the collected Yahoo/Bloomberg evidence."""
        self.logger.info("analyzing_ticker", ticker=ticker, item_count=len(data_items))

        if not data_items:
            return self._neutral_score(ticker)

        if self.enabled:
            try:
                return await asyncio.to_thread(self._analyze_with_openai, ticker, data_items)
            except Exception as exc:
                self.logger.error("analysis_failed", ticker=ticker, error=str(exc))

        return self._analyze_with_heuristics(ticker, data_items)

    def _analyze_with_openai(
        self,
        ticker: str,
        data_items: list[dict[str, Any]],
    ) -> SentimentScore:
        evidence = [
            {
                "source": item.get("source"),
                "title": item.get("title"),
                "summary": item.get("text"),
                "stance": item.get("stance", "neutral"),
                "rationale": item.get("rationale", ""),
                "url": item.get("url", ""),
            }
            for item in data_items[:8]
        ]

        system_prompt = (
            "You are a financial news sentiment analyst. "
            "Given recent market news, decide whether the overall setup for the ticker is "
            "bullish, bearish, or neutral. Return strict JSON only."
        )
        user_prompt = (
            f"Ticker: {ticker}\n"
            "News evidence:\n"
            f"{json.dumps(evidence, ensure_ascii=True)}\n\n"
            "Return JSON with this exact shape:\n"
            "{"
            '"bull_score": 0.0,'
            '"bear_score": 0.0,'
            '"sentiment": "BULL|BEAR|NEUTRAL",'
            '"reasons": ["short overall reasons"],'
            '"bullish_points": ["specific bullish evidence"],'
            '"bearish_points": ["specific bearish evidence"],'
            '"summary": "one short synthesis sentence"'
            "}\n"
            "Scores must be between 0 and 1."
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }

        response = self._post_json(
            "https://api.openai.com/v1/chat/completions",
            payload,
            {
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        content = response["choices"][0]["message"]["content"]
        parsed = self._parse_json_response(content)

        bull_score = self.scorer.normalize_score(float(parsed.get("bull_score", 0.5)))
        bear_score = self.scorer.normalize_score(float(parsed.get("bear_score", 0.5)))
        sentiment = str(parsed.get("sentiment", "NEUTRAL")).upper()
        if sentiment not in {"BULL", "BEAR", "NEUTRAL"}:
            sentiment = self.scorer.classify_sentiment(bull_score, bear_score, threshold=0.1)

        reasons = [str(item).strip() for item in parsed.get("reasons", []) if str(item).strip()]
        bullish_points = [
            str(item).strip() for item in parsed.get("bullish_points", []) if str(item).strip()
        ]
        bearish_points = [
            str(item).strip() for item in parsed.get("bearish_points", []) if str(item).strip()
        ]
        summary = str(parsed.get("summary", "")).strip()

        if not reasons:
            reasons = self._build_default_reasons(bullish_points, bearish_points)
        if not summary:
            summary = "OpenAI returned a score without a summary."

        return SentimentScore(
            ticker=ticker,
            bull_score=bull_score,
            bear_score=bear_score,
            sentiment=sentiment,
            reasons=reasons[:3],
            bullish_points=bullish_points[:4],
            bearish_points=bearish_points[:4],
            summary=summary,
        )

    def _parse_json_response(self, content: str) -> dict[str, Any]:
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if "\n" in text:
                text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
        return json.loads(text.strip())

    def _analyze_with_heuristics(
        self,
        ticker: str,
        data_items: list[dict[str, Any]],
    ) -> SentimentScore:
        bullish_news = [item for item in data_items if item.get("stance") == "bullish"]
        bearish_news = [item for item in data_items if item.get("stance") == "bearish"]
        neutral_news = [item for item in data_items if item.get("stance") == "neutral"]

        total = max(1, len(data_items))
        bull_score = self.scorer.normalize_score(
            0.5 + ((len(bullish_news) - len(bearish_news)) / total) * 0.35
        )
        bear_score = self.scorer.normalize_score(
            0.5 + ((len(bearish_news) - len(bullish_news)) / total) * 0.35
        )
        sentiment = self.scorer.classify_sentiment(bull_score, bear_score, threshold=0.1)

        bullish_points = [
            self._format_item_point(item)
            for item in bullish_news[:4]
        ]
        bearish_points = [
            self._format_item_point(item)
            for item in bearish_news[:4]
        ]

        reasons = self._build_default_reasons(bullish_points, bearish_points)
        summary = (
            f"{ticker} has {len(bullish_news)} bullish, {len(bearish_news)} bearish, "
            f"and {len(neutral_news)} neutral news items across the selected sources."
        )

        return SentimentScore(
            ticker=ticker,
            bull_score=bull_score,
            bear_score=bear_score,
            sentiment=sentiment,
            reasons=reasons,
            bullish_points=bullish_points,
            bearish_points=bearish_points,
            summary=summary,
        )

    def _build_default_reasons(
        self,
        bullish_points: list[str],
        bearish_points: list[str],
    ) -> list[str]:
        reasons: list[str] = []
        if bullish_points:
            reasons.append(bullish_points[0])
        if bearish_points:
            reasons.append(bearish_points[0])
        if not reasons:
            reasons.append("Recent coverage is balanced and does not point to a strong edge.")
        return reasons[:3]

    def _format_item_point(self, item: dict[str, Any]) -> str:
        source = str(item.get("source", "source")).replace("_", " ")
        title = str(item.get("title", "")).strip()
        rationale = str(item.get("rationale", "")).strip()
        if rationale:
            return f"{source.title()}: {title} ({rationale})"
        return f"{source.title()}: {title}"

    def _neutral_score(self, ticker: str) -> SentimentScore:
        return SentimentScore(
            ticker=ticker,
            bull_score=0.5,
            bear_score=0.5,
            sentiment="NEUTRAL",
            reasons=["Insufficient data for analysis"],
            bullish_points=[],
            bearish_points=[],
            summary="No news items were available for the requested ticker.",
        )

    async def batch_analyze(
        self,
        items: list[tuple[str, list[dict[str, Any]]]],
    ) -> list[SentimentScore]:
        tasks = [
            self.analyze_ticker(ticker, data)
            for ticker, data in items
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        scores: list[SentimentScore] = []
        for (ticker, _), result in zip(items, results):
            if isinstance(result, SentimentScore):
                scores.append(result)
            else:
                self.logger.warning("batch_item_failed", ticker=ticker, error=str(result))
                scores.append(self._neutral_score(ticker))

        return scores

    def _post_json(
        self,
        url: str,
        payload: dict[str, Any],
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)

        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:  # pragma: no cover - network/runtime
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI HTTP {exc.code}: {detail}") from exc
        except URLError as exc:  # pragma: no cover - network/runtime
            raise RuntimeError(f"OpenAI network error: {exc.reason}") from exc
