"""Local web app server for the TinyFish dashboard."""

from __future__ import annotations

import argparse
import asyncio
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from src.agent.core import FinancialAgent
from src.trading.signals import SignalFormatter
from src.utils.config import get_settings
from src.utils.logger import setup_logging


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"


class DashboardService:
    """Application service for one-shot sentiment analysis requests."""

    def __init__(self) -> None:
        self.settings = get_settings()
        setup_logging(
            level=self.settings.log_level,
            format=self.settings.log_format,
        )
        self.formatter = SignalFormatter()

    async def analyze(self, tickers: list[str]) -> dict[str, Any]:
        """Run the financial agent for the requested tickers."""
        normalized = [ticker.strip().upper() for ticker in tickers if ticker.strip()]
        if not normalized:
            raise ValueError("At least one ticker is required")

        agent = FinancialAgent(
            openai_api_key=self.settings.openai_api_key,
            tinyfish_key=self.settings.tinyfish_api_key,
            settings=self.settings,
        )
        try:
            result = await agent.analyze_market(normalized)
            signal = result["signal"]
            scores = result["scores"]
            plan = result["plan"]
            per_ticker = result["per_ticker"]
            return {
                "signal": signal.model_dump(),
                "scores": [score.model_dump() for score in scores],
                "per_ticker": per_ticker,
                "plan": plan.model_dump(),
                "text": self.formatter.to_text(signal),
                "markdown": self.formatter.to_markdown(signal),
                "meta": {
                    "tickers": normalized,
                    "tinyfish_enabled": bool(self.settings.tinyfish_api_key),
                    "openai_enabled": bool(self.settings.openai_api_key),
                    "sources": ["Yahoo Finance Singapore", "Bloomberg Asia"],
                },
            }
        finally:
            await agent.cleanup()


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP handler for the TinyFish dashboard."""

    service = DashboardService()

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", ""}:
            self._serve_file(WEB_DIR / "index.html")
            return

        if self.path == "/api/health":
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "default_tickers": self.service.settings.tickers_list,
                    "tinyfish_enabled": bool(self.service.settings.tinyfish_api_key),
                    "openai_enabled": bool(self.service.settings.openai_api_key),
                    "sources": ["Yahoo Finance Singapore", "Bloomberg Asia"],
                },
            )
            return

        target = (WEB_DIR / self.path.lstrip("/")).resolve()
        if not str(target).startswith(str(WEB_DIR.resolve())) or not target.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        self._serve_file(target)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/analyze":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length else b"{}"

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body"})
            return

        tickers = payload.get("tickers", [])
        if isinstance(tickers, str):
            tickers = [part.strip() for part in tickers.split(",")]

        try:
            result = asyncio.run(self.service.analyze(tickers))
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except Exception as exc:  # pragma: no cover - runtime safety net
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "Analysis failed", "details": str(exc)},
            )
            return

        self._send_json(HTTPStatus.OK, result)

    def log_message(self, format: str, *args: Any) -> None:
        """Silence default HTTP request logs."""

    def _serve_file(self, path: Path) -> None:
        content_type, _ = mimetypes.guess_type(str(path))
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the web server."""
    parser = argparse.ArgumentParser(description="TinyFish web dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind")
    return parser.parse_args()


def main() -> None:
    """Start the local dashboard server."""
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"TinyFish dashboard running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
