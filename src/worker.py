"""Background worker for auto-refresh and alert checking."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from src.agent.core import FinancialAgent
from src.data.alerts import get_alerts
from src.data.watchlist import get_watchlist
from src.scheduler import get_scheduler
from src.utils.config import get_settings

logger = structlog.get_logger(__name__)


class BackgroundWorker:
    """Manage background tasks for watchlist refresh and alerts."""

    def __init__(self) -> None:
        self.scheduler = get_scheduler()
        self.settings = get_settings()
        self.logger = logger.bind(component="background_worker")

    def start(self) -> None:
        """Start all background tasks."""
        self.logger.info("starting_background_worker")

        # Watchlist auto-refresh every 15 minutes
        self.scheduler.add_interval_job(
            func=self._refresh_watchlist_job,
            seconds=900,  # 15 minutes
            job_id="watchlist_refresh",
        )

        # Alert checking every 5 minutes
        self.scheduler.add_interval_job(
            func=self._check_alerts_job,
            seconds=300,  # 5 minutes
            job_id="alert_check",
        )

        self.scheduler.start()
        self.logger.info("background_worker_started")

    def stop(self) -> None:
        """Stop all background tasks."""
        self.scheduler.stop()
        self.logger.info("background_worker_stopped")

    def _refresh_watchlist_job(self) -> None:
        """Job to refresh watchlist tickers."""
        try:
            watchlist = get_watchlist()
            tickers = watchlist.get_due_for_refresh()

            if tickers:
                self.logger.info("refreshing_watchlist", ticker_count=len(tickers))
                asyncio.run(self._refresh_tickers(tickers))
        except Exception as exc:
            self.logger.error("watchlist_refresh_failed", error=str(exc))

    async def _refresh_tickers(self, tickers: list[str]) -> None:
        """Refresh sentiment for tickers."""
        agent = FinancialAgent(
            openai_api_key=self.settings.openai_api_key,
            tinyfish_key=self.settings.tinyfish_api_key,
            settings=self.settings,
        )

        try:
            await agent.analyze_market(tickers)

            # Update last check timestamps
            watchlist = get_watchlist()
            for ticker in tickers:
                watchlist.update_last_check(ticker)

            self.logger.info("watchlist_refreshed", tickers=tickers)
        finally:
            await agent.cleanup()

    def _check_alerts_job(self) -> None:
        """Job to check alert conditions."""
        try:
            alerts_mgr = get_alerts()
            triggered = alerts_mgr.check_alerts()

            if triggered:
                self.logger.info("alerts_triggered", count=len(triggered))
                for alert in triggered:
                    self.logger.info("alert_fired", alert=alert)
        except Exception as exc:
            self.logger.error("alert_check_failed", error=str(exc))


_worker_instance: BackgroundWorker | None = None


def get_worker() -> BackgroundWorker:
    """Get the background worker singleton."""
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = BackgroundWorker()
    return _worker_instance
