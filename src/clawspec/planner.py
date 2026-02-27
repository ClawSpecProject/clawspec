"""Build plan data structures and parsing helpers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass
class FileTask:
    """A single file to generate."""

    path: str
    description: str
    context: str = ""


@dataclass
class Workstream:
    """A group of related files that can be generated together."""

    name: str
    description: str
    files: list[FileTask] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)


@dataclass
class BuildPlan:
    """Ordered list of files to generate, optionally grouped into workstreams."""

    files: list[FileTask] = field(default_factory=list)
    workstreams: list[Workstream] = field(default_factory=list)

    def summary(self) -> str:
        if self.workstreams:
            return self._workstream_summary()
        lines = [f"Build plan: {len(self.files)} files to generate\n"]
        for i, ft in enumerate(self.files, 1):
            lines.append(f"  {i}. {ft.path}")
            lines.append(f"     {ft.description}")
        return "\n".join(lines)

    def _workstream_summary(self) -> str:
        total = sum(len(ws.files) for ws in self.workstreams)
        lines = [
            f"Build plan: {total} files in {len(self.workstreams)} workstream(s)\n"
        ]
        for ws in self.workstreams:
            deps = f" (depends on: {', '.join(ws.depends_on)})" if ws.depends_on else ""
            lines.append(f"  [{ws.name}] {ws.description}{deps}")
            for i, ft in enumerate(ws.files, 1):
                lines.append(f"    {i}. {ft.path}")
                lines.append(f"       {ft.description}")
        return "\n".join(lines)


def parse_file_manifest(text: str) -> list[dict]:
    """Extract JSON array from LLM response, tolerating markdown fences."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _strip_json_fences(text: str) -> str:
    """Remove markdown code fences from JSON text."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text


def parse_workstream_manifest(text: str) -> list[dict]:
    """Parse the architect's workstream JSON output.

    Expected format:
    {
      "workstreams": [
        {"name": "...", "description": "...", "depends_on": [], "files": [...]},
        ...
      ]
    }

    Also accepts a flat JSON array for backward compatibility.
    """
    cleaned = _strip_json_fences(text)
    data = json.loads(cleaned)

    # Flat array → backward compat
    if isinstance(data, list):
        return [{"name": "default", "description": "All files", "depends_on": [], "files": data}]

    return data["workstreams"]


def build_plan_summary(plan: BuildPlan) -> str:
    """Format the build plan as a text summary for LLM context."""
    lines = ["Files in this project:"]
    for ft in plan.files:
        lines.append(f"- {ft.path}: {ft.description}")
    return "\n".join(lines)


def build_workstream_plan_summary(plan: BuildPlan) -> str:
    """Format the full plan grouped by workstream for LLM context."""
    if not plan.workstreams:
        return build_plan_summary(plan)
    lines = ["Files in this project (grouped by workstream):"]
    for ws in plan.workstreams:
        deps = f" [depends on: {', '.join(ws.depends_on)}]" if ws.depends_on else ""
        lines.append(f"\n## {ws.name} — {ws.description}{deps}")
        for ft in ws.files:
            lines.append(f"- {ft.path}: {ft.description}")
    return "\n".join(lines)
