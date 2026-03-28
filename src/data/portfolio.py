"""Portfolio management and aggregation."""

from __future__ import annotations

import json
from typing import Any

import structlog

from src.data.database import get_database
from src.data.history import get_sentiment_history

logger = structlog.get_logger(__name__)


class PortfolioManager:
    """Manage user portfolios and calculate aggregated sentiment."""

    def __init__(self) -> None:
        self.db = get_database()
        self.logger = logger.bind(component="portfolio")

    def add_holding(self, ticker: str, quantity: float, portfolio_id: int = 1) -> None:
        """Add or update a holding in the portfolio."""
        ticker = ticker.upper().strip()
        self.logger.info("adding_holding", ticker=ticker, quantity=quantity)

        with self.db.get_connection() as conn:
            # Ensure default portfolio exists
            conn.execute(
                """
                INSERT OR IGNORE INTO portfolios (id, name)
                VALUES (?, ?)
                """,
                (portfolio_id, "Default Portfolio"),
            )

            # Add or update holding
            conn.execute(
                """
                INSERT INTO portfolio_holdings (portfolio_id, ticker, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(portfolio_id, ticker) DO UPDATE SET
                    quantity = excluded.quantity
                """,
                (portfolio_id, ticker, quantity),
            )
            conn.commit()

    def remove_holding(self, ticker: str, portfolio_id: int = 1) -> None:
        """Remove a holding from the portfolio."""
        ticker = ticker.upper().strip()
        self.logger.info("removing_holding", ticker=ticker)

        with self.db.get_connection() as conn:
            conn.execute(
                """
                DELETE FROM portfolio_holdings
                WHERE portfolio_id = ? AND ticker = ?
                """,
                (portfolio_id, ticker),
            )
            conn.commit()

    def get_holdings(self, portfolio_id: int = 1) -> list[dict[str, Any]]:
        """Get all holdings with latest sentiment."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT ticker, quantity
                FROM portfolio_holdings
                WHERE portfolio_id = ?
                ORDER BY ticker
                """,
                (portfolio_id,),
            )
            rows = cursor.fetchall()

        history = get_sentiment_history()
        holdings = []

        for row in rows:
            ticker = row["ticker"]
            latest = history.get_latest_for_ticker(ticker)

            holdings.append({
                "ticker": ticker,
                "quantity": row["quantity"],
                "sentiment": latest["sentiment"] if latest else None,
                "bull_score": latest["bull_score"] if latest else None,
                "bear_score": latest["bear_score"] if latest else None,
                "confidence": latest["confidence"] if latest else None,
            })

        return holdings

    def get_aggregated_sentiment(self, portfolio_id: int = 1) -> dict[str, Any]:
        """Calculate portfolio-level aggregated sentiment."""
        holdings = self.get_holdings(portfolio_id)

        if not holdings:
            return {
                "sentiment": "NEUTRAL",
                "avg_bull_score": 0.5,
                "avg_bear_score": 0.5,
                "risk_score": 0.5,
                "holdings_count": 0,
            }

        # Simple equally-weighted average
        valid_holdings = [h for h in holdings if h["sentiment"]]

        if not valid_holdings:
            return {
                "sentiment": "NEUTRAL",
                "avg_bull_score": 0.5,
                "avg_bear_score": 0.5,
                "risk_score": 0.5,
                "holdings_count": len(holdings),
            }

        avg_bull = sum(h["bull_score"] for h in valid_holdings) / len(valid_holdings)
        avg_bear = sum(h["bear_score"] for h in valid_holdings) / len(valid_holdings)
        risk_score = avg_bear  # Simple risk = bearishness

        if avg_bull > 0.6:
            sentiment = "BULL"
        elif avg_bear > 0.6:
            sentiment = "BEAR"
        else:
            sentiment = "NEUTRAL"

        return {
            "sentiment": sentiment,
            "avg_bull_score": avg_bull,
            "avg_bear_score": avg_bear,
            "risk_score": risk_score,
            "holdings_count": len(holdings),
        }


_portfolio_manager: PortfolioManager | None = None


def get_portfolio() -> PortfolioManager:
    """Get the portfolio manager singleton."""
    global _portfolio_manager
    if _portfolio_manager is None:
        _portfolio_manager = PortfolioManager()
    return _portfolio_manager
