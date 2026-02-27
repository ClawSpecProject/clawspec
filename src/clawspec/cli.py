"""Click-based CLI for clawspec."""

from __future__ import annotations

from pathlib import Path

import anyio
import click

from clawspec import __version__


INIT_PROJECT_MD = """\
# My Project

Describe what this project does and who it's for.

## Tech Stack

<!-- What kind of app is this? Be as specific or general as you want. -->
<!-- Examples: "Web app", "Next.js with Firebase", "Python CLI tool" -->
- Web application

## Entities

<!-- The core data objects in your system. Describe them in plain language. -->

### User
A person who uses the app. Has a name, email (unique), and password.
"""

INIT_EXAMPLE_SPEC = """\
# Feature Name

## Entities

Describe the things this feature deals with in plain language.
What are they? What properties do they have? How do they relate to each other?

## Rules

Describe the business rules and constraints.
- What is allowed or disallowed?
- What happens in edge cases?
- What are the validation requirements?

## Constraints

<!-- Optional: pin down specific technical decisions. Remove this section -->
<!-- if you want the tool to decide. Examples: -->
<!-- - Use Firebase Auth for authentication -->
<!-- - Store data in a PostgreSQL `tasks` table -->
<!-- - API endpoint must be POST /api/tasks -->

## User Stories

### Story Name
Describe what the user does, step by step, in plain language.
What do they see? What do they interact with? What happens on success or failure?

**Acceptance criteria:**
- What must be true when this story is done?
- What does the user see on success?
- What does the user see on failure?
"""


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Clawspec: spec-driven code generation."""


@main.command()
@click.argument("directory", default=".", type=click.Path())
def init(directory: str) -> None:
    """Scaffold a new spec project with example files."""
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=True)

    project_md = root / "PROJECT.md"
    specs_dir = root / "specs"
    specs_dir.mkdir(exist_ok=True)

    if project_md.exists():
        click.echo(f"PROJECT.md already exists in {root}, skipping.")
    else:
        project_md.write_text(INIT_PROJECT_MD)
        click.echo(f"Created {project_md}")

    example_spec = specs_dir / "example.md"
    if not any(specs_dir.glob("*.md")):
        example_spec.write_text(INIT_EXAMPLE_SPEC)
        click.echo(f"Created {example_spec}")

    click.echo(f"\nSpec project initialized in {root}")
    click.echo("Edit PROJECT.md and add specs in specs/ to get started.")
    click.echo("Then run: clawspec build")


@main.command()
@click.argument("directory", default=".", type=click.Path(exists=True))
def check(directory: str) -> None:
    """Validate spec files and report issues."""
    from clawspec.checker import check_project

    root = Path(directory).resolve()
    result = check_project(root)

    if not result.issues:
        click.echo("All specs valid.")
        return

    for issue in result.issues:
        click.echo(str(issue))

    click.echo()
    error_count = len(result.errors)
    warn_count = len(result.warnings)
    parts = []
    if error_count:
        parts.append(f"{error_count} error(s)")
    if warn_count:
        parts.append(f"{warn_count} warning(s)")
    click.echo(", ".join(parts))

    if not result.passed:
        raise SystemExit(1)


@main.command()
@click.option(
    "--output-dir",
    type=click.Path(),
    default="src",
    help="Output directory for generated code.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show the build plan without generating code.",
)
@click.option(
    "--no-git",
    is_flag=True,
    default=False,
    help="Skip git branch/commit operations.",
)
@click.option(
    "--backend",
    type=click.Choice(["claude"]),
    default="claude",
    help="Agent backend to use for generation.",
)
@click.option(
    "--sequential",
    is_flag=True,
    default=False,
    help="Force sequential file generation (skip parallel workstreams).",
)
@click.argument("directory", default=".", type=click.Path(exists=True))
def build(
    output_dir: str,
    dry_run: bool,
    no_git: bool,
    backend: str,
    sequential: bool,
    directory: str,
) -> None:
    """Parse specs, plan, generate code, and commit to a branch."""
    anyio.run(_build, output_dir, dry_run, no_git, backend, sequential, directory)


async def _build(
    output_dir: str,
    dry_run: bool,
    no_git: bool,
    backend_name: str,
    sequential: bool,
    directory: str,
) -> None:
    from clawspec import git
    from clawspec.backends import create_backend
    from clawspec.generator import generate_all
    from clawspec.parser import parse_project

    root = Path(directory).resolve()
    backend = create_backend(backend_name)

    # 1. Parse specs
    click.echo("Parsing specs...")
    project = parse_project(root)
    click.echo(
        f"  Project: {project.name} "
        f"({len(project.features)} feature spec(s))"
    )

    # 2. Plan
    click.echo("Planning build...")
    plan = await backend.plan(project)
    click.echo(plan.summary())

    if dry_run:
        click.echo("\n--dry-run: stopping before code generation.")
        return

    # 3. Resolve output directory
    out = (root / output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    # 4. Git setup
    repo = None
    branch_name = None
    original_branch = None
    if not no_git:
        repo = git.get_repo(root)
        if repo:
            original_branch = repo.active_branch.name
            branch_name = git.create_build_branch(repo)
            click.echo(f"\nCreated branch: {branch_name}")
        else:
            click.echo("\nNo git repo found, skipping git operations.")

    # 5. Generate
    mode = "sequentially" if sequential or not plan.workstreams else "in parallel"
    click.echo(f"\nGenerating code ({mode})...")
    written = await generate_all(plan, project, out, backend, sequential=sequential)
    click.echo(f"\nGenerated {len(written)} files.")

    # 6. Git commit
    if repo and branch_name:
        git.commit_generated_files(repo, out, len(written))
        git.print_summary(repo, branch_name, original_branch)

        # Return to original branch
        repo.git.checkout(original_branch)
        click.echo(f"\nReturned to branch: {original_branch}")
