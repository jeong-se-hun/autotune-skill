#!/usr/bin/env python3
"""Scan a project directory and infer a starter autotune contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DETECTORS = [
    {
        "marker": "package.json",
        "type": "node",
        "target": "src/",
        "optimize": "lint_warnings min",
        "guards": ["tests_failed <= 0", "type_errors <= 0"],
        "verify": ["npm run lint", "npm test"],
    },
    {
        "marker": "pyproject.toml",
        "type": "python",
        "target": "src/",
        "optimize": "lint_warnings min",
        "guards": ["tests_failed <= 0"],
        "verify": ["python3 -m pytest -q", "python3 -m ruff check ."],
    },
    {
        "marker": "go.mod",
        "type": "go",
        "target": ".",
        "optimize": "lint_warnings min",
        "guards": ["tests_failed <= 0"],
        "verify": ["go test ./...", "go vet ./..."],
    },
    {
        "marker": "Cargo.toml",
        "type": "rust",
        "target": "src/",
        "optimize": "lint_warnings min",
        "guards": ["tests_failed <= 0"],
        "verify": ["cargo test", "cargo clippy -- -D warnings"],
    },
    {
        "marker": "SKILL.md",
        "type": "skill",
        "target": "SKILL.md",
        "optimize": "task_success_rate max",
        "guards": ["false_trigger_rate <= baseline"],
        "verify": ["run benchmark prompts and score outputs"],
    },
]


def detect(project_root: Path) -> dict | None:
    for detector in DETECTORS:
        if (project_root / detector["marker"]).exists():
            return detector

    md_files = list(project_root.glob("*.md"))
    if md_files:
        return {
            "type": "docs",
            "target": md_files[0].name,
            "optimize": "qa_accuracy max",
            "guards": ["contradiction_count <= 0"],
            "verify": ["run fixed Q&A against target doc"],
        }
    return None


def format_text(detector: dict, project_root: Path) -> str:
    lines = [
        f"Target:",
        f"- {detector['target']}",
        f"",
        f"Writable scope:",
        f"- {detector['target']}",
        f"",
        f"Immutable:",
        f"- benchmark inputs",
        f"- eval harness",
        f"",
        f"Optimize:",
        f"- {detector['optimize']}",
        f"",
        f"Guards:",
    ]
    for guard in detector.get("guards", []):
        lines.append(f"- {guard}")
    lines.append("")
    lines.append("Verify:")
    for cmd in detector.get("verify", []):
        lines.append(f"- {cmd}")
    lines.extend([
        "",
        "Budget:",
        "- 3",
        "",
        "Rollback:",
        "- python3 scripts/rollback.py snapshot <file>  # before edit",
        "- python3 scripts/rollback.py restore <file>   # on reject or crash",
        "",
        "Log:",
        "- /tmp/autotune.tsv",
        "",
        "Baseline:",
        "- collect before first edit",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", help="Project directory to scan")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        print(f"not a directory: {project_root}", file=sys.stderr)
        return 1

    detector = detect(project_root)
    if detector is None:
        print("no recognizable project markers found", file=sys.stderr)
        return 1

    if args.format == "json":
        json.dump(detector, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(format_text(detector, project_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
