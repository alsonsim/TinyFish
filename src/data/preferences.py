"""Preference and session management."""

from __future__ import annotations

import json
from typing import Any

import structlog

from src.data.database import get_database

logger = structlog.get_logger(__name__)


class PreferenceManager:
    """Manage user preferences and session state."""

    def __init__(self) -> None:
        self.db = get_database()
        self.logger = logger.bind(component="preferences")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a preference value."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT value FROM preferences WHERE key = ?",
                (key,),
            )
            row = cursor.fetchone()

        if not row:
            return default

        try:
            return json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            return row["value"]

    def set(self, key: str, value: Any) -> None:
        """Set a preference value."""
        json_value = json.dumps(value) if not isinstance(value, str) else value

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO preferences (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (key, json_value),
            )
            conn.commit()

        self.logger.info("preference_set", key=key)

    def delete(self, key: str) -> None:
        """Delete a preference."""
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM preferences WHERE key = ?", (key,))
            conn.commit()

        self.logger.info("preference_deleted", key=key)

    def get_all(self) -> dict[str, Any]:
        """Get all preferences."""
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT key, value FROM preferences")
            rows = cursor.fetchall()

        prefs = {}
        for row in rows:
            try:
                prefs[row["key"]] = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                prefs[row["key"]] = row["value"]

        return prefs


_preference_manager: PreferenceManager | None = None


def get_preferences() -> PreferenceManager:
    """Get the preference manager singleton."""
    global _preference_manager
    if _preference_manager is None:
        _preference_manager = PreferenceManager()
    return _preference_manager
