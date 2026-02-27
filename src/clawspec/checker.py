"""Validate spec files and report issues."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from clawspec.parser import FeatureSpec, SpecProject, parse_project


@dataclass
class Issue:
    """A single validation issue."""

    level: str  # "error" or "warning"
    file: str
    message: str

    def __str__(self) -> str:
        icon = "\u2717" if self.level == "error" else "\u26a0"
        return f"  {icon} [{self.file}] {self.message}"


@dataclass
class CheckResult:
    """Result of validating a spec project."""

    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "warning"]

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def error(self, file: str, message: str) -> None:
        self.issues.append(Issue("error", file, message))

    def warn(self, file: str, message: str) -> None:
        self.issues.append(Issue("warning", file, message))


def _extract_story_names(user_stories: str) -> list[str]:
    """Extract ### heading names from user stories content."""
    return re.findall(r"^###\s+(.+)$", user_stories, re.MULTILINE)


def _story_has_acceptance_criteria(user_stories: str, story_name: str) -> bool:
    """Check if a specific story has acceptance criteria."""
    # Find the story heading and check if acceptance criteria follows
    # before the next ### heading or end of string
    pattern = (
        r"###\s+" + re.escape(story_name) + r"\s*\n"
        r"(.*?)"
        r"(?=###\s+|\Z)"
    )
    match = re.search(pattern, user_stories, re.DOTALL)
    if not match:
        return False
    story_body = match.group(1)
    return bool(re.search(r"\*\*acceptance criteria", story_body, re.IGNORECASE))


def _check_project_md(project: SpecProject, result: CheckResult) -> None:
    """Validate PROJECT.md content."""
    file = "PROJECT.md"

    if not project.project_md.strip():
        result.error(file, "File is empty")
        return

    if project.name == "Unnamed Project":
        result.warn(file, "Missing project name (add a # heading)")

    # Check for entities section
    sections = {h.lower() for h in re.findall(r"^##\s+(.+)$", project.project_md, re.MULTILINE)}
    if not sections & {"entities", "objects", "models"}:
        result.warn(file, "Missing ## Entities section — consider defining shared data objects")

    if not sections & {"tech stack"}:
        result.warn(file, "Missing ## Tech Stack section — the architect will choose for you")


def _check_feature_spec(spec: FeatureSpec, result: CheckResult) -> None:
    """Validate a single feature spec."""
    file = f"specs/{spec.name}.md"

    if not spec.raw.strip():
        result.error(file, "File is empty")
        return

    # Required sections
    if not spec.entities:
        result.error(file, "Missing ## Entities section")

    if not spec.rules:
        result.error(file, "Missing ## Rules section")

    if not spec.user_stories:
        result.error(file, "Missing ## User Stories section")
        return  # Can't check stories if there are none

    # Check each story for acceptance criteria
    stories = _extract_story_names(spec.user_stories)
    if not stories:
        result.error(file, "## User Stories section has no ### story headings")
        return

    for story in stories:
        if not _story_has_acceptance_criteria(spec.user_stories, story):
            result.warn(file, f'Story "{story}" is missing **Acceptance criteria:**')

    # Optional sections
    if not spec.constraints:
        result.warn(file, "No ## Constraints section — all technical decisions will be inferred")


def check_project(root: Path) -> CheckResult:
    """Validate a spec project directory."""
    result = CheckResult()

    project_md_path = root / "PROJECT.md"
    if not project_md_path.exists():
        result.error("PROJECT.md", "File not found")
        return result

    specs_dir = root / "specs"
    if not specs_dir.is_dir() or not list(specs_dir.glob("*.md")):
        result.error("specs/", "No feature specs found — add .md files to specs/")
        return result

    project = parse_project(root)
    _check_project_md(project, result)

    for spec in project.features:
        _check_feature_spec(spec, result)

    return result
