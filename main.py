"""Main entry point for TinyFish Financial Agent."""

from __future__ import annotations

import argparse
import asyncio
import signal
import sys
from typing import Any

import structlog

from src.agent.core import FinancialAgent
from src.trading.signals import SignalFormatter
from src.utils.config import get_settings
from src.utils.logger import setup_logging


logger = structlog.get_logger(__name__)


class AgentRunner:
    """Main runner for the financial agent."""

    def __init__(self) -> None:
        self.settings = get_settings()
        setup_logging(
            level=self.settings.log_level,
            format=self.settings.log_format,
        )
        self.logger = logger.bind(component="agent_runner")
        self.formatter = SignalFormatter()
        self.agent: FinancialAgent | None = None
        self.running = False

    async def start(
        self,
        tickers: list[str],
        run_once: bool = True,
        scan_interval: int | None = None,
        output_format: str = "text",
    ) -> None:
        """Start the agent in one-shot or watch mode."""
        effective_interval = scan_interval or self.settings.scan_interval

        self.logger.info(
            "agent_starting",
            tickers=tickers,
            interval=effective_interval,
            run_once=run_once,
        )

        try:
            self.agent = FinancialAgent(
                openai_api_key=self.settings.openai_api_key,
                tinyfish_key=self.settings.tinyfish_api_key,
                settings=self.settings,
            )
            self.running = True

            while self.running:
                signal_result = await self.agent.monitor_sentiment(tickers=tickers)
                self._emit_signal(signal_result, output_format)

                if run_once:
                    break

                self.logger.info("scan_complete", next_scan_in=effective_interval)
                await asyncio.sleep(effective_interval)

        except KeyboardInterrupt:
            self.logger.info("shutdown_requested")
        except Exception as exc:
            self.logger.error("agent_error", error=str(exc), exc_info=True)
            raise
        finally:
            await self.cleanup()

    async def cleanup(self) -> None:
        """Cleanup resources on shutdown."""
        self.running = False
        if self.agent:
            await self.agent.cleanup()
        self.logger.info("cleanup_complete")

    def handle_signal(self, sig: Any, frame: Any) -> None:
        """Handle shutdown signals."""
        self.logger.info("signal_received", signal=sig)
        self.running = False

    def _emit_signal(self, signal_result: Any, output_format: str) -> None:
        if output_format == "json":
            print(self.formatter.to_json(signal_result))
            return
        if output_format == "markdown":
            print(self.formatter.to_markdown(signal_result))
            return
        print(self.formatter.to_text(signal_result))


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="TinyFish Financial Sentiment Agent")
    parser.add_argument(
        "--tickers",
        nargs="+",
        help="Tickers to analyze. Defaults to the tickers in settings.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run continuously instead of executing a single scan.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Polling interval in seconds for watch mode.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format for the generated signal.",
    )
    return parser.parse_args()


async def async_main() -> None:
    """Async program entry point."""
    args = parse_args()
    settings = get_settings()
    tickers = [ticker.upper() for ticker in (args.tickers or settings.tickers_list)]

    runner = AgentRunner()
    signal.signal(signal.SIGINT, runner.handle_signal)
    signal.signal(signal.SIGTERM, runner.handle_signal)

    await runner.start(
        tickers=tickers,
        run_once=not args.watch,
        scan_interval=args.interval,
        output_format=args.format,
    )


if __name__ == "__main__":
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nAgent stopped by user.")
    except Exception as exc:
        print(f"\nFatal error: {exc}", file=sys.stderr)
        sys.exit(1)
