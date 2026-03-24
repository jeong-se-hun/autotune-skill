#!/usr/bin/env python3
"""Create repo-local autotune session scaffold files from bundled templates."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "assets" / "templates"

FILES = {
    "autotune.md": "autotune.md",
    "autotune.spec.json": "autotune.spec.json",
    "autotune-dashboard.md": "autotune-dashboard.md",
    "autotune.state.json": "autotune.state.json",
    "autotune.ideas.md": "autotune.ideas.md",
    "autotune.sh": "autotune.sh",
    "autotune.checks.sh": "autotune.checks.sh",
}
MACHINE_LOG = "autotune.jsonl"


def _write_if_missing(src: Path, dest: Path, force: bool) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        return f"skip {dest}"
    shutil.copyfile(src, dest)
    if dest.suffix == ".sh":
        dest.chmod(0o755)
    return f"write {dest}"


def _ensure_append_only_log(dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return f"skip {dest}"
    dest.write_text("", encoding="utf-8")
    return f"write {dest}"


def _append_agents_block(repo_root: Path) -> str:
    agents_path = repo_root / "AGENTS.md"
    block = (TEMPLATES / "AGENTS.autotune.md").read_text(encoding="utf-8")

    if agents_path.exists():
        existing = agents_path.read_text(encoding="utf-8")
        if "<!-- autotune:start -->" in existing:
            return f"skip {agents_path}"
        if not existing.endswith("\n"):
            existing += "\n"
        agents_path.write_text(existing + "\n" + block + "\n", encoding="utf-8")
    else:
        agents_path.write_text(block + "\n", encoding="utf-8")
    return f"write {agents_path}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", help="Repository root to scaffold")
    parser.add_argument("--force", action="store_true", help="Overwrite existing scaffold files")
    parser.add_argument(
        "--write-agents-block",
        action="store_true",
        help="Append the bundled autotune block to AGENTS.md",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.is_dir():
        print(f"repo root is not a directory: {repo_root}", file=sys.stderr)
        return 1

    actions: list[str] = []
    for template_name, dest_name in FILES.items():
        actions.append(
            _write_if_missing(TEMPLATES / template_name, repo_root / dest_name, args.force)
        )

    actions.append(
        _write_if_missing(
            TEMPLATES / "experiments-worklog.md",
            repo_root / "experiments" / "worklog.md",
            args.force,
        )
    )
    actions.append(
        _write_if_missing(
            TEMPLATES / "experiments-review-notes.md",
            repo_root / "experiments" / "review-notes.md",
            args.force,
        )
    )
    actions.append(
        _write_if_missing(
            TEMPLATES / "experiments-review-pack.json",
            repo_root / "experiments" / "review-pack.json",
            args.force,
        )
    )
    actions.append(_ensure_append_only_log(repo_root / MACHINE_LOG))

    if args.write_agents_block:
        actions.append(_append_agents_block(repo_root))

    for action in actions:
        print(action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
