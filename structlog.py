"""Minimal local fallback for structlog used by this project.

This module implements the subset of the structlog API that the codebase uses.
If the real dependency is installed, Python can still import this local module
first, so the implementation intentionally stays small and compatible.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


def configure(**_: Any) -> None:
    """Accept structlog.configure calls without requiring the real package."""


@dataclass
class BoundLogger:
    """Very small bound logger wrapper."""

    name: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    def bind(self, **kwargs: Any) -> "BoundLogger":
        return BoundLogger(name=self.name, context={**self.context, **kwargs})

    def debug(self, event: str, **kwargs: Any) -> None:
        self._log("debug", event, **kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        self._log("info", event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._log("warning", event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._log("error", event, **kwargs)

    def exception(self, event: str, **kwargs: Any) -> None:
        kwargs.setdefault("exc_info", True)
        self._log("exception", event, **kwargs)

    def _log(self, level: str, event: str, **kwargs: Any) -> None:
        payload = {**self.context, **kwargs}
        logger = logging.getLogger(self.name or "tinyfish")
        message = event
        if payload:
            message = f"{event} | {json.dumps(payload, default=str, sort_keys=True)}"
        getattr(logger, level, logger.info)(message)


def get_logger(name: str | None = None) -> BoundLogger:
    """Return a lightweight bound logger."""
    return BoundLogger(name=name or "tinyfish")


class _ContextVars:
    @staticmethod
    def merge_contextvars(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        return event_dict


class _Stdlib:
    BoundLogger = BoundLogger

    @staticmethod
    def add_log_level(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        return event_dict

    @staticmethod
    def add_logger_name(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        return event_dict

    class LoggerFactory:
        def __call__(self, *args: Any, **kwargs: Any) -> logging.Logger:
            return logging.getLogger(*args, **kwargs)


class _Processors:
    class TimeStamper:
        def __init__(self, fmt: str = "iso") -> None:
            self.fmt = fmt

        def __call__(self, _: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
            if self.fmt == "iso":
                event_dict.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
            return event_dict

    class StackInfoRenderer:
        def __call__(self, _: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
            return event_dict

    @staticmethod
    def format_exc_info(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        return event_dict

    class JSONRenderer:
        def __call__(self, _: Any, __: str, event_dict: dict[str, Any]) -> str:
            return json.dumps(event_dict, default=str, sort_keys=True)


class _Dev:
    class ConsoleRenderer:
        def __call__(self, _: Any, __: str, event_dict: dict[str, Any]) -> str:
            return " ".join(f"{key}={value}" for key, value in event_dict.items())


contextvars = _ContextVars()
stdlib = _Stdlib()
processors = _Processors()
dev = _Dev()
