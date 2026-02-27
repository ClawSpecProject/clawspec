"""Parse markdown spec files into structured dataclasses."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FeatureSpec:
    """A parsed feature spec from specs/<feature>.md."""

    name: str
    path: Path
    raw: str
    entities: str = ""
    rules: str = ""
    constraints: str = ""
    user_stories: str = ""
    sections: dict[str, str] = field(default_factory=dict)


@dataclass
class SpecProject:
    """A parsed spec project from PROJECT.md + specs/*.md."""

    name: str
    project_md: str
    features: list[FeatureSpec] = field(default_factory=list)

    def all_spec_content(self) -> str:
        """Return all spec content concatenated for LLM context."""
        parts = [f"# PROJECT.md\n\n{self.project_md}"]
        for feat in self.features:
            parts.append(f"# specs/{feat.name}.md\n\n{feat.raw}")
        return "\n\n---\n\n".join(parts)


# Mapping from normalized heading text to FeatureSpec field name
_SECTION_FIELD_MAP = {
    "entities": "entities",
    "objects": "entities",
    "models": "entities",
    "rules": "rules",
    "business logic": "rules",
    "business rules": "rules",
    "constraints": "constraints",
    "technical constraints": "constraints",
    "engineering constraints": "constraints",
    "user stories": "user_stories",
    "cujs": "user_stories",
    "critical user journeys": "user_stories",
    "journeys": "user_stories",
}


def _parse_sections(content: str) -> dict[str, str]:
    """Split markdown content by ## headings into {heading: body} dict."""
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in content.splitlines():
        match = re.match(r"^##\s+(.+)$", line)
        if match:
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def parse_feature_spec(path: Path) -> FeatureSpec:
    """Parse a single feature spec file."""
    raw = path.read_text()
    sections = _parse_sections(raw)

    spec = FeatureSpec(
        name=path.stem,
        path=path,
        raw=raw,
        sections=sections,
    )

    for heading, body in sections.items():
        normalized = heading.lower().strip()
        field_name = _SECTION_FIELD_MAP.get(normalized)
        if field_name:
            setattr(spec, field_name, body)

    return spec


def _extract_project_name(project_md: str) -> str:
    """Extract project name from the first # heading in PROJECT.md."""
    for line in project_md.splitlines():
        match = re.match(r"^#\s+(.+)$", line)
        if match:
            return match.group(1).strip()
    return "Unnamed Project"


def parse_project(root: Path) -> SpecProject:
    """Parse a full spec project from a directory containing PROJECT.md and specs/."""
    project_md_path = root / "PROJECT.md"
    if not project_md_path.exists():
        raise FileNotFoundError(f"No PROJECT.md found in {root}")

    project_md = project_md_path.read_text()
    specs_dir = root / "specs"

    features: list[FeatureSpec] = []
    if specs_dir.is_dir():
        for spec_path in sorted(specs_dir.glob("*.md")):
            features.append(parse_feature_spec(spec_path))

    return SpecProject(
        name=_extract_project_name(project_md),
        project_md=project_md,
        features=features,
    )
