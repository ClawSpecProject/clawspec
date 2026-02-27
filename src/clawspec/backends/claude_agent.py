"""Claude Agent SDK backend for clawspec."""

from __future__ import annotations

import os
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from clawspec.parser import SpecProject
from clawspec.planner import (
    BuildPlan,
    FileTask,
    Workstream,
    build_plan_summary,
    parse_file_manifest,
    parse_workstream_manifest,
)

# The Agent SDK spawns a Claude Code subprocess. If we're already inside a
# Claude Code session (e.g. the user ran `clawspec build` from Claude Code),
# the CLAUDECODE env var will cause the child to refuse to start. Strip it.
os.environ.pop("CLAUDECODE", None)

ARCHITECT_SYSTEM = """\
You are an expert software architect. You are given product specifications that \
may be written by product managers, engineers, or both. Your job is to design the \
technical architecture and produce a file manifest grouped into parallel workstreams.

The specs have a layered format:
- **Entities**: the data objects (always present, plain language)
- **Rules**: business logic and constraints (always present, plain language)
- **User Stories**: what users can do, with **Acceptance criteria** that define \
  "done" for each story (always present, plain language)
- **Constraints**: optional engineering decisions that MUST be followed exactly \
  (specific frameworks, services, data stores, API shapes). When present, these \
  override your own architectural choices.
- **Tech Stack** in PROJECT.md: optional high-level tech preferences.

When constraints are specified, follow them exactly. When they are not specified, \
make good architectural decisions based on the tech stack and best practices.

Rules:
- Output ONLY a JSON object with a "workstreams" array. No explanation before or after.
- Group files into workstreams by feature or concern. Each workstream contains \
  files that are closely related and should be generated together.
- Always have a "shared" workstream for project configs, shared models, and \
  utilities. This workstream has no dependencies and runs first.
- Each feature (e.g., auth, tasks) should be its own workstream that depends on "shared".
- Always have a "docs" workstream containing README.md as the final workstream \
  that depends on ALL other workstreams.
- Declare "depends_on" for cross-workstream dependencies. Workstreams that do not \
  depend on each other will run in parallel.
- Order files within each workstream so that internal dependencies come first \
  (e.g., models before routes within the same workstream).

Output format:
```json
{
  "workstreams": [
    {
      "name": "shared",
      "description": "Project configuration and shared utilities",
      "depends_on": [],
      "files": [
        {"path": "package.json", "description": "Project dependencies and scripts"},
        {"path": "tsconfig.json", "description": "TypeScript configuration"}
      ]
    },
    {
      "name": "auth",
      "description": "Authentication feature",
      "depends_on": ["shared"],
      "files": [
        {"path": "lib/auth.ts", "description": "Auth service layer"}
      ]
    },
    {
      "name": "docs",
      "description": "Project documentation",
      "depends_on": ["shared", "auth"],
      "files": [
        {"path": "README.md", "description": "Project documentation"}
      ]
    }
  ]
}
```

File rules:
- "path" is relative to the output directory.
- "description" explains what the file contains and its role.
- Choose a sensible directory structure based on the tech stack.
- Include all necessary files: configs, models, routes, services, components, etc.
- Translate user stories into appropriate API endpoints and UI pages.
- Translate entities into database models and schemas.
- Translate rules into service-layer logic and validations.
- The acceptance criteria on each user story define what "correct" means. \
  Make sure the architecture supports verifying each one.
- Do NOT include package manager lock files, .env files, or node_modules.
- The README.md in the "docs" workstream must cover:
  - Project overview (what it does)
  - Prerequisites (runtime versions, tools)
  - Environment variables (every env var the app needs, with descriptions)
  - Setup instructions (install deps, create database, run migrations, etc.)
  - How to run locally (dev server commands for each component)
  - How to deploy (production build steps, hosting recommendations)
  - Project structure (brief directory overview)
"""

BUILDER_SYSTEM = """\
You are an expert software engineer. You are given product specifications and a \
technical build plan. Your job is to generate production-quality source code.

The specs have a layered format:
- **Entities / Rules / User Stories**: describe WHAT the product does.
- **Constraints**: optional engineering decisions that MUST be followed exactly.
- **Acceptance criteria** on each user story: define what "correct" means for \
  that feature. Your code must satisfy every acceptance criterion.

When constraints are specified, follow them exactly. When they are not, use best \
practices for the tech stack.

Rules:
- Use the Write tool to create the requested file at the exact path specified.
- Write valid, complete, working code. No placeholders or TODOs.
- Import from other project files using the paths described in the build plan.
- Ensure consistency with previously generated files shown in context.
- Pay close attention to acceptance criteria — they are the definition of done. \
  If an acceptance criterion says "show error X", your code must show exactly that.
- After writing, validate the file if appropriate:
  - Python: run `python -c "import ast; ast.parse(open('<path>').read())"`
  - TypeScript/JS: run `npx tsc --noEmit <path>` if tsconfig exists
  - JSON: run `python -c "import json; json.load(open('<path>'))"`
- If validation fails, read the error, fix the file, and re-validate.
- When generating README.md or other documentation, be comprehensive and specific. \
  List every environment variable with its purpose and example value. \
  Give exact commands to run, not vague instructions. \
  Reference the actual file paths and config files in the generated codebase.
"""


class ClaudeAgentBackend:
    """Agent backend using the Claude Agent SDK."""

    async def plan(self, project: SpecProject) -> BuildPlan:
        spec_content = project.all_spec_content()
        result = ""

        async for message in query(
            prompt=(
                f"Here are the full project specifications:\n\n{spec_content}"
            ),
            options=ClaudeAgentOptions(
                system_prompt=ARCHITECT_SYSTEM,
                allowed_tools=[],
                max_turns=1,
            ),
        ):
            if isinstance(message, ResultMessage):
                result = message.result

        ws_data = parse_workstream_manifest(result)
        plan = BuildPlan()

        for ws_item in ws_data:
            file_tasks = [
                FileTask(path=f["path"], description=f["description"])
                for f in ws_item["files"]
            ]
            plan.workstreams.append(
                Workstream(
                    name=ws_item["name"],
                    description=ws_item.get("description", ""),
                    files=file_tasks,
                    depends_on=ws_item.get("depends_on", []),
                )
            )
            # Flatten into files list for backward compat
            plan.files.extend(file_tasks)

        return plan

    async def generate_file(
        self,
        task: FileTask,
        project: SpecProject,
        plan: BuildPlan,
        generated_files: dict[str, str],
        output_dir: Path,
    ) -> str:
        spec_content = project.all_spec_content()
        plan_summary = build_plan_summary(plan)

        prior_context = ""
        if generated_files:
            parts = [
                f"--- {path} ---\n{content}"
                for path, content in generated_files.items()
            ]
            prior_context = (
                "\n\nPreviously generated files:\n\n" + "\n\n".join(parts)
            )

        file_path = output_dir / task.path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async for message in query(
            prompt=(
                f"Generate and write the file: {file_path}\n"
                f"Description: {task.description}\n\n"
                f"Project specifications:\n\n{spec_content}\n\n"
                f"Build plan:\n{plan_summary}"
                f"{prior_context}"
            ),
            options=ClaudeAgentOptions(
                system_prompt=BUILDER_SYSTEM,
                allowed_tools=["Write", "Read", "Bash"],
                permission_mode="acceptEdits",
                cwd=str(output_dir),
                max_turns=10,
            ),
        ):
            pass

        return file_path.read_text()
