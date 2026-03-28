"""Watchlist management for monitoring tickers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog

from src.data.database import get_database

logger = structlog.get_logger(__name__)


class WatchlistManager:
    """Manage ticker watchlist for auto-refresh monitoring."""

    def __init__(self) -> None:
        self.db = get_database()
        self.logger = logger.bind(component="watchlist")

    def add_ticker(self, ticker: str, refresh_interval: int = 900) -> None:
        """Add a ticker to the watchlist."""
        ticker = ticker.upper().strip()
        self.logger.info("adding_to_watchlist", ticker=ticker)

        with self.db.get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO watchlist (ticker, refresh_interval, added_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (ticker, refresh_interval),
                )
                conn.commit()
                self.logger.info("ticker_added", ticker=ticker)
            except Exception as exc:
                self.logger.warning("ticker_already_exists", ticker=ticker, error=str(exc))

    def remove_ticker(self, ticker: str) -> None:
        """Remove a ticker from the watchlist."""
        ticker = ticker.upper().strip()
        self.logger.info("removing_from_watchlist", ticker=ticker)

        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker,))
            conn.commit()

        self.logger.info("ticker_removed", ticker=ticker)

    def get_all(self) -> list[dict[str, Any]]:
        """Get all watchlist tickers."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT ticker, added_at, last_check, refresh_interval
                FROM watchlist
                ORDER BY added_at DESC
                """
            )
            rows = cursor.fetchall()

        return [
            {
                "ticker": row["ticker"],
                "added_at": row["added_at"],
                "last_check": row["last_check"],
                "refresh_interval": row["refresh_interval"],
            }
            for row in rows
        ]

    def update_last_check(self, ticker: str) -> None:
        """Update the last check timestamp for a ticker."""
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE watchlist SET last_check = CURRENT_TIMESTAMP WHERE ticker = ?",
                (ticker,),
            )
            conn.commit()

    def get_due_for_refresh(self) -> list[str]:
        """Get tickers that are due for refresh based on their interval."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT ticker FROM watchlist
                WHERE last_check IS NULL
                   OR (julianday('now') - julianday(last_check)) * 86400 >= refresh_interval
                """
            )
            rows = cursor.fetchall()

        return [row["ticker"] for row in rows]


_watchlist_manager: WatchlistManager | None = None


def get_watchlist() -> WatchlistManager:
    """Get the watchlist manager singleton."""
    global _watchlist_manager
    if _watchlist_manager is None:
        _watchlist_manager = WatchlistManager()
    return _watchlist_manager
