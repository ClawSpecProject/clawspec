"""Shared state for cross-workstream coordination during parallel generation."""

from __future__ import annotations

from dataclasses import dataclass, field

import anyio


@dataclass
class TrackerEntry:
    """A single file being tracked across workstreams."""

    path: str
    workstream: str
    status: str = "pending"  # "pending" | "done"
    content: str | None = None


class BuildTracker:
    """Thread-safe shared state across workstreams.

    Uses anyio primitives so workstreams can await their dependencies
    before starting generation.
    """

    def __init__(self) -> None:
        self._entries: dict[str, TrackerEntry] = {}
        self._workstream_events: dict[str, anyio.Event] = {}
        self._lock = anyio.Lock()

    def register(self, path: str, workstream: str) -> None:
        """Register a file as pending (call before generation starts)."""
        self._entries[path] = TrackerEntry(path=path, workstream=workstream)

    def register_workstream(self, name: str) -> None:
        """Register a workstream so others can wait on it."""
        self._workstream_events[name] = anyio.Event()

    async def mark_done(self, path: str, content: str) -> None:
        """Mark a file as done and store its content."""
        async with self._lock:
            entry = self._entries[path]
            entry.status = "done"
            entry.content = content

    async def get_completed(self) -> dict[str, str]:
        """Return all completed files across all workstreams."""
        async with self._lock:
            return {
                e.path: e.content
                for e in self._entries.values()
                if e.status == "done" and e.content is not None
            }

    async def get_completed_in(self, workstream: str) -> dict[str, str]:
        """Return completed files in a specific workstream."""
        async with self._lock:
            return {
                e.path: e.content
                for e in self._entries.values()
                if e.workstream == workstream
                and e.status == "done"
                and e.content is not None
            }

    async def mark_workstream_done(self, name: str) -> None:
        """Signal that a workstream has finished all its files."""
        self._workstream_events[name].set()

    async def wait_for_workstreams(self, names: list[str]) -> None:
        """Block until all named workstreams are complete."""
        for name in names:
            await self._workstream_events[name].wait()
