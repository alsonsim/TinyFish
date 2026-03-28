"""Trading signal formatting and output."""

from __future__ import annotations

import structlog

from src.data.models import TradingSignal

logger = structlog.get_logger(__name__)


class SignalFormatter:
    """Formats trading signals for terminal, JSON, and Markdown output."""

    def __init__(self) -> None:
        self.logger = logger.bind(component="signal_formatter")

    def to_text(self, signal: TradingSignal) -> str:
        """Format a signal for terminal output."""
        marker = {"BUY": "[+]", "SELL": "[-]", "HOLD": "[=]"}[signal.action]
        lines = [
            f"{marker} TRADING SIGNAL {marker}",
            "",
            f"Ticker: {signal.ticker}",
            f"Action: {signal.action}",
            f"Confidence: {signal.confidence:.1%}",
            f"Time: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "Reasons:",
        ]
        lines.extend(f"{index}. {reason}" for index, reason in enumerate(signal.reasons, 1))
        return "\n".join(lines).strip()

    def to_json(self, signal: TradingSignal) -> str:
        """Format a signal as JSON."""
        return signal.model_dump_json(indent=2)

    def to_markdown(self, signal: TradingSignal) -> str:
        """Format a signal for webhook or Markdown display."""
        lines = [
            f"# Trading Signal: {signal.action}",
            "",
            f"**Ticker:** `{signal.ticker}`  ",
            f"**Confidence:** {signal.confidence:.1%}  ",
            f"**Time:** {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "## Reasons",
            "",
        ]
        lines.extend(f"- {reason}" for reason in signal.reasons)
        return "\n".join(lines).strip()
