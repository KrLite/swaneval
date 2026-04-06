"""
In-memory import progress tracking.

Each import job gets a unique ID. The import service updates progress,
and the SSE endpoint streams it to the frontend.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ImportProgress:
    job_id: str
    name: str
    status: str = "pending"  # pending, downloading, processing, done, failed
    phase: str = ""  # e.g. "Connecting to HuggingFace", "Downloading", "Processing"
    progress: float = 0.0  # 0.0 - 1.0
    error: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Global progress store
_progress: dict[str, ImportProgress] = {}
_events: dict[str, asyncio.Event] = {}


def create_job(job_id: str, name: str) -> ImportProgress:
    p = ImportProgress(job_id=job_id, name=name)
    _progress[job_id] = p
    _events[job_id] = asyncio.Event()
    return p


def update_job(
    job_id: str,
    *,
    status: str | None = None,
    phase: str | None = None,
    progress: float | None = None,
    error: str | None = None,
) -> None:
    p = _progress.get(job_id)
    if not p:
        return
    if status is not None:
        p.status = status
    if phase is not None:
        p.phase = phase
    if progress is not None:
        p.progress = progress
    if error is not None:
        p.error = error
    p.updated_at = datetime.now(timezone.utc)
    # Signal waiters
    evt = _events.get(job_id)
    if evt:
        evt.set()
        evt.clear()


def get_job(job_id: str) -> ImportProgress | None:
    return _progress.get(job_id)


def get_event(job_id: str) -> asyncio.Event | None:
    return _events.get(job_id)


def remove_job(job_id: str) -> None:
    _progress.pop(job_id, None)
    _events.pop(job_id, None)
