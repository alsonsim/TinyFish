"""Alert rule management and checking."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog

from src.data.database import get_database
from src.data.history import get_sentiment_history

logger = structlog.get_logger(__name__)


class AlertManager:
    """Manage alert rules and check conditions."""

    def __init__(self) -> None:
        self.db = get_database()
        self.logger = logger.bind(component="alerts")

    def add_alert(
        self,
        ticker: str,
        condition_type: str,
        threshold: float,
        name: str | None = None,
    ) -> int:
        """Add a new alert rule."""
        ticker = ticker.upper().strip()
        name = name or f"{ticker} {condition_type} {threshold}"

        self.logger.info("adding_alert", ticker=ticker, condition=condition_type)

        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO alert_rules (name, ticker, condition_type, threshold, notification_channels)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, ticker, condition_type, threshold, "ui"),
            )
            conn.commit()
            return cursor.lastrowid

    def remove_alert(self, alert_id: int) -> None:
        """Remove an alert rule."""
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM alert_rules WHERE id = ?", (alert_id,))
            conn.commit()

    def get_all_alerts(self) -> list[dict[str, Any]]:
        """Get all alert rules."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, name, ticker, condition_type, threshold, enabled, last_triggered
                FROM alert_rules
                ORDER BY ticker
                """
            )
            rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "name": row["name"],
                "ticker": row["ticker"],
                "condition_type": row["condition_type"],
                "threshold": row["threshold"],
                "enabled": bool(row["enabled"]),
                "last_triggered": row["last_triggered"],
            }
            for row in rows
        ]

    def check_alerts(self) -> list[dict[str, Any]]:
        """Check all enabled alerts and return triggered ones."""
        alerts = self.get_all_alerts()
        triggered = []

        history = get_sentiment_history()

        for alert in alerts:
            if not alert["enabled"]:
                continue

            latest = history.get_latest_for_ticker(alert["ticker"])
            if not latest:
                continue

            value = None
            triggered_flag = False

            if alert["condition_type"] == "bull_above":
                value = latest["bull_score"]
                triggered_flag = value > alert["threshold"]
            elif alert["condition_type"] == "bear_above":
                value = latest["bear_score"]
                triggered_flag = value > alert["threshold"]
            elif alert["condition_type"] == "confidence_above":
                value = latest["confidence"]
                triggered_flag = value > alert["threshold"]

            if triggered_flag:
                message = (
                    f"{alert['ticker']}: {alert['condition_type'].replace('_', ' ')} "
                    f"triggered ({value:.2f} > {alert['threshold']})"
                )

                triggered.append({
                    "alert_id": alert["id"],
                    "ticker": alert["ticker"],
                    "message": message,
                    "value": value,
                })

                # Log trigger
                self._log_trigger(alert["id"], alert["ticker"], message, value)

        return triggered

    def _log_trigger(
        self,
        alert_id: int,
        ticker: str,
        message: str,
        value: float | None,
    ) -> None:
        """Log an alert trigger."""
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO alert_history (alert_rule_id, ticker, message, value)
                VALUES (?, ?, ?, ?)
                """,
                (alert_id, ticker, message, value),
            )
            conn.execute(
                """
                UPDATE alert_rules
                SET last_triggered = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (alert_id,),
            )
            conn.commit()


_alert_manager: AlertManager | None = None


def get_alerts() -> AlertManager:
    """Get the alert manager singleton."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
