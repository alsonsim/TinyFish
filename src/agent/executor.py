"""TinyFish browser automation executor."""

from __future__ import annotations

import asyncio
import gzip
import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import structlog

logger = structlog.get_logger(__name__)


class TinyFishExecutor:
    """Wrap the TinyFish automation API and provide direct HTTP fallbacks."""

    automation_url = "https://agent.tinyfish.ai/v1/automation/run-async"
    runs_batch_url = "https://agent.tinyfish.ai/v1/runs/batch"

    def __init__(self, api_key: str | None, headless: bool = True) -> None:
        self.api_key = api_key
        self.headless = headless
        self.logger = logger.bind(component="tinyfish_executor")
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        self.logger.info(
            "executor_initialized",
            headless=headless,
            tinyfish_enabled=bool(api_key),
        )

    async def fetch_page(
        self,
        url: str,
        wait_for: str | None = None,
    ) -> str:
        """Fetch raw HTML directly, without TinyFish automation."""
        self.logger.info("fetching_page", url=url, wait_for=wait_for)
        try:
            return await asyncio.to_thread(self._http_get_text, url)
        except Exception as exc:
            self.logger.error("fetch_page_failed", url=url, error=str(exc))
            return ""

    async def run_extraction(
        self,
        *,
        url: str,
        goal: str,
        country_code: str | None = None,
        timeout_seconds: int = 90,
    ) -> dict[str, Any]:
        """Execute a TinyFish automation run and wait for the structured result."""
        if not self.api_key:
            raise RuntimeError("TinyFish API key is missing")

        payload: dict[str, Any] = {
            "url": url,
            "goal": goal,
            "browser_profile": "stealth" if self.headless else "lite",
            "api_integration": "tinyfish-financial-agent",
        }
        if country_code:
            payload["proxy_config"] = {
                "enabled": True,
                "country_code": country_code,
            }

        self.logger.info("tinyfish_run_start", url=url)
        created = await asyncio.to_thread(
            self._post_json,
            self.automation_url,
            payload,
            {"X-API-Key": self.api_key},
        )
        run_id = created.get("run_id")
        if not run_id:
            raise RuntimeError(f"TinyFish did not return a run_id: {created}")

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            status_payload = await asyncio.to_thread(
                self._post_json,
                self.runs_batch_url,
                {"run_ids": [run_id]},
                {"X-API-Key": self.api_key},
            )
            run = self._extract_run(status_payload, run_id)
            status = str(run.get("status", "")).upper()

            if status == "COMPLETED":
                self.logger.info("tinyfish_run_complete", run_id=run_id)
                result = (
                    run.get("result")
                    or run.get("resultJson")
                    or run.get("output")
                    or run.get("data")
                    or {}
                )
                if isinstance(result, str):
                    try:
                        return json.loads(result)
                    except json.JSONDecodeError:
                        return {"text": result}
                if isinstance(result, dict):
                    return result
                if isinstance(result, list):
                    return {"items": result}
                return {"raw": result}

            if status in {"FAILED", "CANCELLED"}:
                raise RuntimeError(run.get("error") or f"TinyFish run {status.lower()}")

            await asyncio.sleep(3)

        raise TimeoutError(f"TinyFish run timed out after {timeout_seconds} seconds")

    def _extract_run(self, payload: dict[str, Any], run_id: str) -> dict[str, Any]:
        candidates: list[dict[str, Any]] = []
        for key in ("runs", "data", "items", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                candidates.extend(item for item in value if isinstance(item, dict))
        if isinstance(payload.get("run"), dict):
            candidates.append(payload["run"])
        if payload.get("run_id") == run_id:
            return payload
        for item in candidates:
            if item.get("run_id") == run_id or item.get("id") == run_id:
                return item
        raise RuntimeError(f"Unable to locate TinyFish run {run_id} in response: {payload}")

    def _http_get_text(self, url: str) -> str:
        request = Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip",
            },
            method="GET",
        )
        with urlopen(request, timeout=20) as response:
            raw = response.read()
            encoding = response.headers.get("Content-Encoding", "")
            if encoding == "gzip":
                raw = gzip.decompress(raw)
            return raw.decode("utf-8", errors="replace")

    def _post_json(
        self,
        url: str,
        payload: dict[str, Any],
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
        }
        if extra_headers:
            headers.update(extra_headers)

        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:  # pragma: no cover - network/runtime
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"TinyFish HTTP {exc.code}: {detail}") from exc
        except URLError as exc:  # pragma: no cover - network/runtime
            raise RuntimeError(f"TinyFish network error: {exc.reason}") from exc

    async def close(self) -> None:
        """Close the executor and release resources."""
        self.logger.info("closing_executor")
