"""Chatbot for natural language queries about market sentiment."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import structlog

from src.data.history import get_sentiment_history
from src.data.watchlist import get_watchlist

logger = structlog.get_logger(__name__)


class FinancialChatbot:
    """AI chatbot for conversational market sentiment queries."""

    def __init__(self, openai_api_key: str | None, model: str = "gpt-4o-mini") -> None:
        self.api_key = openai_api_key
        self.model = model
        self.enabled = bool(openai_api_key)
        self.logger = logger.bind(component="chatbot")
        self.conversation_history: list[dict[str, str]] = []

    async def process_message(self, message: str) -> dict[str, Any]:
        """Process a chat message and return a response."""
        self.logger.info("processing_message", message=message[:100])

        # Extract tickers from message
        tickers = self._extract_tickers(message)

        # Build context from available data
        context = await self._build_context(tickers, message)

        # Get AI response
        if self.enabled:
            response_text = await asyncio.to_thread(
                self._get_openai_response,
                message,
                context,
            )
        else:
            response_text = self._get_fallback_response(message, tickers, context)

        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": response_text})

        return {
            "response": response_text,
            "tickers": tickers,
            "context_used": bool(context),
        }

    def _extract_tickers(self, message: str) -> list[str]:
        """Extract ticker symbols from message."""
        # Match $TICKER or standalone uppercase words 2-5 chars
        pattern = r'\$([A-Z]{1,5})|(?<!\w)([A-Z]{2,5})(?!\w)'
        matches = re.findall(pattern, message.upper())
        tickers = [m[0] or m[1] for m in matches if m[0] or m[1]]
        return list(dict.fromkeys(tickers))  # Remove duplicates

    async def _build_context(self, tickers: list[str], message: str) -> str:
        """Build context from historical data and watchlist."""
        context_parts = []

        # Add watchlist context
        if "watchlist" in message.lower():
            watchlist = get_watchlist()
            items = watchlist.get_all()
            if items:
                ticker_list = ", ".join([item["ticker"] for item in items])
                context_parts.append(f"User's watchlist: {ticker_list}")

        # Add ticker history context
        history = get_sentiment_history()
        for ticker in tickers[:3]:  # Limit to 3 tickers
            latest = history.get_latest_for_ticker(ticker)
            if latest:
                context_parts.append(
                    f"{ticker}: Latest sentiment is {latest['sentiment']} "
                    f"(bull: {latest['bull_score']:.2f}, bear: {latest['bear_score']:.2f}, "
                    f"action: {latest['action']}, confidence: {latest['confidence']:.2f}). "
                    f"Summary: {latest['summary']}"
                )

        return "\n".join(context_parts)

    def _get_openai_response(self, message: str, context: str) -> str:
        """Get response from OpenAI."""
        system_prompt = (
            "You are a financial market sentiment assistant. "
            "You help users understand market sentiment for stocks based on news analysis. "
            "Be concise, helpful, and focused on actionable insights. "
            "When discussing sentiment, explain the reasoning clearly."
        )

        if context:
            system_prompt += f"\n\nContext:\n{context}"

        messages = [{"role": "system", "content": system_prompt}]

        # Add recent conversation history (last 4 messages)
        messages.extend(self.conversation_history[-4:])

        # Add current message
        messages.append({"role": "user", "content": message})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500,
        }

        try:
            response = self._post_json(
                "https://api.openai.com/v1/chat/completions",
                payload,
                {"Authorization": f"Bearer {self.api_key}"},
            )
            return response["choices"][0]["message"]["content"]
        except Exception as exc:
            self.logger.error("openai_request_failed", error=str(exc))
            return "I'm having trouble connecting to the AI service. Please try again."

    def _get_fallback_response(
        self,
        message: str,
        tickers: list[str],
        context: str,
    ) -> str:
        """Provide a simple fallback response without OpenAI."""
        message_lower = message.lower()

        if "watchlist" in message_lower:
            watchlist = get_watchlist()
            items = watchlist.get_all()
            if items:
                ticker_list = ", ".join([item["ticker"] for item in items])
                return f"Your watchlist contains: {ticker_list}"
            return "Your watchlist is currently empty."

        if tickers:
            ticker = tickers[0]
            history = get_sentiment_history()
            latest = history.get_latest_for_ticker(ticker)

            if latest:
                return (
                    f"{ticker} sentiment: {latest['sentiment']} "
                    f"({latest['action']} signal with {latest['confidence']:.0%} confidence). "
                    f"{latest['summary']}"
                )
            return f"I don't have recent data for {ticker}. Try running an analysis first."

        if "help" in message_lower:
            return (
                "I can help you with:\n"
                "- Check sentiment for specific tickers (e.g., 'What's AAPL sentiment?')\n"
                "- Compare tickers (e.g., 'Compare TSLA and NVDA')\n"
                "- View your watchlist (e.g., 'Show my watchlist')\n"
                "- Get trading signals (e.g., 'Should I buy MSFT?')"
            )

        return (
            "I can help you analyze market sentiment! "
            "Try asking about specific tickers like AAPL, TSLA, or NVDA."
        )

    def _post_json(
        self,
        url: str,
        payload: dict[str, Any],
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a JSON POST request."""
        headers = {"Content-Type": "application/json"}
        if extra_headers:
            headers.update(extra_headers)

        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Network error: {exc.reason}") from exc


_chatbot_instance: FinancialChatbot | None = None


def get_chatbot() -> FinancialChatbot:
    """Get the chatbot singleton."""
    global _chatbot_instance
    if _chatbot_instance is None:
        from src.utils.config import get_settings
        settings = get_settings()
        _chatbot_instance = FinancialChatbot(
            openai_api_key=settings.openai_api_key,
            model=getattr(settings, "openai_model", "gpt-4o-mini"),
        )
    return _chatbot_instance
