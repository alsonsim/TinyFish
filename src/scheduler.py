"""Background task scheduler for auto-refresh, alerts, and reports."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = structlog.get_logger(__name__)


class TaskScheduler:
    """Manage background tasks for watchlist refresh, alerts, and reports."""

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.logger = logger.bind(component="task_scheduler")
        self._started = False

    def start(self) -> None:
        """Start the scheduler."""
        if not self._started:
            self.scheduler.start()
            self._started = True
            self.logger.info("scheduler_started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self._started:
            self.scheduler.shutdown()
            self._started = False
            self.logger.info("scheduler_stopped")

    def add_interval_job(
        self,
        func: Callable[..., Any],
        seconds: int,
        job_id: str,
        **kwargs: Any,
    ) -> None:
        """Add a job that runs at fixed intervals."""
        self.logger.info(
            "adding_interval_job",
            job_id=job_id,
            interval_seconds=seconds,
        )

        self.scheduler.add_job(
            func,
            trigger=IntervalTrigger(seconds=seconds),
            id=job_id,
            replace_existing=True,
            **kwargs,
        )

    def add_cron_job(
        self,
        func: Callable[..., Any],
        job_id: str,
        hour: int = 0,
        minute: int = 0,
        **kwargs: Any,
    ) -> None:
        """Add a job that runs at specific time daily."""
        self.logger.info(
            "adding_cron_job",
            job_id=job_id,
            time=f"{hour:02d}:{minute:02d}",
        )

        self.scheduler.add_job(
            func,
            trigger="cron",
            hour=hour,
            minute=minute,
            id=job_id,
            replace_existing=True,
            **kwargs,
        )

    def remove_job(self, job_id: str) -> None:
        """Remove a scheduled job."""
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info("job_removed", job_id=job_id)
        except Exception as exc:
            self.logger.warning("job_removal_failed", job_id=job_id, error=str(exc))

    def get_jobs(self) -> list[dict[str, Any]]:
        """Get list of all scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            })
        return jobs


_scheduler_instance: TaskScheduler | None = None


def get_scheduler() -> TaskScheduler:
    """Get the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = TaskScheduler()
    return _scheduler_instance
