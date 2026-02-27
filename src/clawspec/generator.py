"""Orchestrate code generation across files using an agent backend."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import anyio
import click

from clawspec.parser import SpecProject
from clawspec.planner import BuildPlan, Workstream
from clawspec.tracker import BuildTracker

if TYPE_CHECKING:
    from clawspec.backends import AgentBackend


async def generate_all(
    plan: BuildPlan,
    project: SpecProject,
    output_dir: Path,
    backend: AgentBackend,
    *,
    sequential: bool = False,
) -> list[Path]:
    """Generate all files in the build plan.

    Uses parallel workstreams when available, falls back to sequential.
    Pass sequential=True to force the old sequential behavior.
    """
    if plan.workstreams and not sequential:
        return await generate_parallel(plan, project, output_dir, backend)
    return await _generate_sequential(plan, project, output_dir, backend)


async def _generate_sequential(
    plan: BuildPlan,
    project: SpecProject,
    output_dir: Path,
    backend: AgentBackend,
) -> list[Path]:
    """Generate all files sequentially (original behavior)."""
    generated_files: dict[str, str] = {}
    written_paths: list[Path] = []

    for i, task in enumerate(plan.files, 1):
        click.echo(f"  [{i}/{len(plan.files)}] Generating {task.path}...")

        code = await backend.generate_file(
            task, project, plan, generated_files, output_dir
        )
        generated_files[task.path] = code

        file_path = output_dir / task.path
        written_paths.append(file_path)

    return written_paths


async def generate_parallel(
    plan: BuildPlan,
    project: SpecProject,
    output_dir: Path,
    backend: AgentBackend,
) -> list[Path]:
    """Generate files in parallel workstreams."""
    tracker = BuildTracker()

    # Register all workstreams and files
    for ws in plan.workstreams:
        tracker.register_workstream(ws.name)
        for task in ws.files:
            tracker.register(task.path, ws.name)

    written_paths: list[Path] = []
    written_lock = anyio.Lock()

    async def run_workstream(ws: Workstream) -> None:
        paths = await generate_workstream(
            ws, plan, project, output_dir, backend, tracker
        )
        async with written_lock:
            written_paths.extend(paths)

    async with anyio.create_task_group() as tg:
        for ws in plan.workstreams:
            tg.start_soon(run_workstream, ws)

    return written_paths


async def generate_workstream(
    ws: Workstream,
    plan: BuildPlan,
    project: SpecProject,
    output_dir: Path,
    backend: AgentBackend,
    tracker: BuildTracker,
) -> list[Path]:
    """Generate all files in a single workstream, sequentially."""
    # Wait for dependency workstreams to finish
    if ws.depends_on:
        click.echo(f"  [{ws.name}] Waiting for: {', '.join(ws.depends_on)}...")
        await tracker.wait_for_workstreams(ws.depends_on)

    written_paths: list[Path] = []

    for i, task in enumerate(ws.files, 1):
        click.echo(f"  [{ws.name} {i}/{len(ws.files)}] Generating {task.path}...")

        # Context: own workstream's completed files + all completed files from dependencies
        generated_files = await tracker.get_completed_in(ws.name)
        for dep_name in ws.depends_on:
            dep_files = await tracker.get_completed_in(dep_name)
            generated_files.update(dep_files)

        code = await backend.generate_file(
            task, project, plan, generated_files, output_dir
        )
        await tracker.mark_done(task.path, code)

        file_path = output_dir / task.path
        written_paths.append(file_path)

    await tracker.mark_workstream_done(ws.name)
    click.echo(f"  [{ws.name}] Done ({len(ws.files)} files)")
    return written_paths
