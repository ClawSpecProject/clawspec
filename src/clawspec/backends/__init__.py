"""Backend protocol and factory for agent-based code generation."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from clawspec.parser import SpecProject
from clawspec.planner import BuildPlan, FileTask


@runtime_checkable
class AgentBackend(Protocol):
    """Interface for agent backends that can plan and generate code."""

    async def plan(self, project: SpecProject) -> BuildPlan: ...

    async def generate_file(
        self,
        task: FileTask,
        project: SpecProject,
        plan: BuildPlan,
        generated_files: dict[str, str],
        output_dir: Path,
    ) -> str: ...


def create_backend(name: str = "claude") -> AgentBackend:
    """Create an agent backend by name."""
    if name == "claude":
        from clawspec.backends.claude_agent import ClaudeAgentBackend

        return ClaudeAgentBackend()
    raise ValueError(f"Unknown backend: {name!r}. Available: claude")
