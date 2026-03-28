"""Historical sentiment data storage and retrieval."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

import structlog

from src.data.database import get_database
from src.data.models import SentimentScore, TradingSignal

logger = structlog.get_logger(__name__)


class SentimentHistory:
    """Manage historical sentiment data storage and retrieval."""

    def __init__(self) -> None:
        self.db = get_database()
        self.logger = logger.bind(component="sentiment_history")

    def store_analysis(
        self,
        signal: TradingSignal,
        scores: list[SentimentScore],
    ) -> None:
        """Store analysis results in history."""
        self.logger.info("storing_analysis", ticker=signal.ticker, action=signal.action)

        with self.db.get_connection() as conn:
            for score in scores:
                conn.execute(
                    """
                    INSERT INTO sentiment_history (
                        ticker, action, confidence, bull_score, bear_score,
                        sentiment, reasons, bullish_points, bearish_points,
                        summary, news_count, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        score.ticker,
                        signal.action,
                        signal.confidence,
                        score.bull_score,
                        score.bear_score,
                        score.sentiment,
                        json.dumps(score.reasons),
                        json.dumps(score.bullish_points),
                        json.dumps(score.bearish_points),
                        score.summary,
                        len(score.bullish_points) + len(score.bearish_points),
                        datetime.utcnow().isoformat(),
                    ),
                )
            conn.commit()

        self.logger.info("analysis_stored", score_count=len(scores))

    def get_ticker_history(
        self,
        ticker: str,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """Get historical sentiment data for a ticker."""
        self.logger.info("fetching_history", ticker=ticker, days=days)

        cutoff = datetime.utcnow() - timedelta(days=days)

        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM sentiment_history
                WHERE ticker = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                """,
                (ticker, cutoff.isoformat()),
            )
            rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append({
                "id": row["id"],
                "ticker": row["ticker"],
                "action": row["action"],
                "confidence": row["confidence"],
                "bull_score": row["bull_score"],
                "bear_score": row["bear_score"],
                "sentiment": row["sentiment"],
                "reasons": json.loads(row["reasons"]) if row["reasons"] else [],
                "bullish_points": json.loads(row["bullish_points"]) if row["bullish_points"] else [],
                "bearish_points": json.loads(row["bearish_points"]) if row["bearish_points"] else [],
                "summary": row["summary"],
                "news_count": row["news_count"],
                "timestamp": row["timestamp"],
            })

        self.logger.info("history_fetched", ticker=ticker, count=len(results))
        return results

    def get_latest_for_ticker(self, ticker: str) -> dict[str, Any] | None:
        """Get the most recent analysis for a ticker."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM sentiment_history
                WHERE ticker = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (ticker,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": row["id"],
            "ticker": row["ticker"],
            "action": row["action"],
            "confidence": row["confidence"],
            "bull_score": row["bull_score"],
            "bear_score": row["bear_score"],
            "sentiment": row["sentiment"],
            "reasons": json.loads(row["reasons"]) if row["reasons"] else [],
            "bullish_points": json.loads(row["bullish_points"]) if row["bullish_points"] else [],
            "bearish_points": json.loads(row["bearish_points"]) if row["bearish_points"] else [],
            "summary": row["summary"],
            "news_count": row["news_count"],
            "timestamp": row["timestamp"],
        }

    def get_chart_data(
        self,
        ticker: str,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get formatted chart data for a ticker."""
        history = self.get_ticker_history(ticker, days)

        timestamps = [h["timestamp"] for h in history]
        bull_scores = [h["bull_score"] for h in history]
        bear_scores = [h["bear_score"] for h in history]
        confidence = [h["confidence"] for h in history]

        return {
            "ticker": ticker,
            "timestamps": timestamps,
            "bull_scores": bull_scores,
            "bear_scores": bear_scores,
            "confidence": confidence,
            "count": len(history),
        }

    def get_comparison_data(
        self,
        tickers: list[str],
        days: int = 30,
    ) -> dict[str, Any]:
        """Get comparison data for multiple tickers."""
        comparison = {}
        for ticker in tickers:
            comparison[ticker] = self.get_chart_data(ticker, days)
        return comparison


def get_sentiment_history() -> SentimentHistory:
    """Get the sentiment history singleton."""
    return SentimentHistory()
