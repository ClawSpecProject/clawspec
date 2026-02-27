"""Git branch/commit operations for clawspec builds."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import click
from git import InvalidGitRepositoryError, Repo


def get_repo(path: Path) -> Repo | None:
    """Get the git repo containing the given path, or None."""
    try:
        return Repo(path, search_parent_directories=True)
    except InvalidGitRepositoryError:
        return None


def create_build_branch(repo: Repo) -> str:
    """Create and checkout a new branch for this build."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    branch_name = f"clawspec/build-{timestamp}"
    repo.git.checkout("-b", branch_name)
    return branch_name


def commit_generated_files(
    repo: Repo,
    output_dir: Path,
    file_count: int,
) -> str:
    """Stage and commit all generated files."""
    # Stage the output directory
    repo.git.add(str(output_dir), "--force")

    message = f"clawspec: generate {file_count} files from specs"
    repo.index.commit(message)
    return message


def print_summary(repo: Repo, branch_name: str, original_branch: str) -> None:
    """Print diff stats and review instructions."""
    click.echo(f"\n  Branch: {branch_name}")

    # Show diffstat against the original branch
    try:
        diff_stat = repo.git.diff(original_branch, branch_name, "--stat")
        if diff_stat:
            click.echo(f"\n{diff_stat}")
    except Exception:
        pass

    click.echo(f"\nTo review: git diff {original_branch}...{branch_name}")
    click.echo(f"To merge:  git checkout {original_branch} && git merge {branch_name}")
