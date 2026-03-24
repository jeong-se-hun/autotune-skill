#!/usr/bin/env python3
"""Export a clean public repository layout from the local skill source.

This is a maintainer-only script. It is excluded from the public skill bundle.
Run it to prepare a release-ready export that passes public_release_check.py.

Usage:
    python3 scripts/export_public_repo.py <export_root> [options]

Options:
    --with-claude-plugin      Include .claude-plugin/ wrapper
    --owner-name NAME         Owner name for marketplace metadata
    --plugin-description DESC Plugin description (defaults to SKILL.md description)
    --repo-slug SLUG          GitHub repo slug (e.g. jeong-se-hun/autotune-skill)
    --license-file PATH       Path to LICENSE file to include
    --force                   Overwrite existing export directory
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]

# Files copied from repo root into export root
ROOT_FILES = [
    ("README.md", "README.md"),
    ("README.ko.md", "README.ko.md"),
    (".gitignore", ".gitignore"),
]

# Skill files copied relative to skills/autotune/ → export/skills/autotune/
# Excludes maintainer-only scripts (self_check, self_test, export_public_repo)
SKILL_FILES = [
    "SKILL.md",
    "agents/openai.yaml",
    "agents/grader.md",
    "agents/comparator.md",
    "agents/analyzer.md",
    "scripts/eval_gate.py",
    "scripts/rollback.py",
    "scripts/lint_eval_spec.py",
    "scripts/extract_metrics.py",
    "scripts/validate_log.py",
    "scripts/resume_session.py",
    "scripts/generate_dashboard.py",
    "scripts/auto_detect_contract.py",
    "scripts/lint_contract.py",
    "scripts/render_review_pack.py",
    "scripts/init_session_scaffold.py",
    "scripts/check_routing_eval_set.py",
    "scripts/run_codex_trigger_benchmark.py",
    "scripts/score_routing_contract.py",
    "scripts/score_autotune_quality.py",
    "scripts/run_fixture_tests.py",
    "scripts/public_release_check.py",
    "scripts/graders/qa_grader.py",
    "scripts/graders/section_checker.py",
    "scripts/graders/assertion_runner.py",
    "evals/evals.json",
    "evals/trigger-eval-set.json",
    "evals/autotune-quality.spec.json",
    "references/autonomy-modes.md",
    "references/contract-templates.md",
    "references/eval-guide.md",
    "references/eval-patterns.md",
    "references/live-trigger-benchmark.md",
    "references/log-template.tsv",
    "references/loop-design.md",
    "references/public-publishing.md",
    "references/review-patterns.md",
    "references/schemas.md",
    "references/scorecard-patterns.md",
    "references/session-scaffold.md",
    "references/target-guidance.md",
    "references/tools-reference.md",
    "assets/templates/AGENTS.autotune.md",
    "assets/templates/autotune-dashboard.md",
    "assets/templates/autotune.checks.sh",
    "assets/templates/autotune.ideas.md",
    "assets/templates/autotune.md",
    "assets/templates/autotune.sh",
    "assets/templates/autotune.spec.json",
    "assets/templates/autotune.state.json",
    "assets/templates/experiments-review-notes.md",
    "assets/templates/experiments-review-pack.json",
    "assets/templates/experiments-worklog.md",
    "assets/fixtures/autonomy-threshold/baseline.json",
    "assets/fixtures/autonomy-threshold/contract.txt",
    "assets/fixtures/autonomy-threshold/keep.json",
    "assets/fixtures/autonomy-threshold/reject.json",
    "assets/fixtures/autonomy-threshold/spec.json",
    "assets/fixtures/code-latency/baseline.json",
    "assets/fixtures/code-latency/contract.txt",
    "assets/fixtures/code-latency/keep.json",
    "assets/fixtures/code-latency/reject.json",
    "assets/fixtures/code-latency/spec.json",
    "assets/fixtures/docs-runbook/baseline.json",
    "assets/fixtures/docs-runbook/contract.txt",
    "assets/fixtures/docs-runbook/keep.json",
    "assets/fixtures/docs-runbook/reject.json",
    "assets/fixtures/docs-runbook/spec.json",
    "assets/fixtures/policy-coverage/baseline.json",
    "assets/fixtures/policy-coverage/contract.txt",
    "assets/fixtures/policy-coverage/keep.json",
    "assets/fixtures/policy-coverage/reject.json",
    "assets/fixtures/policy-coverage/spec.json",
    "assets/fixtures/skill-trigger/baseline.json",
    "assets/fixtures/skill-trigger/contract.txt",
    "assets/fixtures/skill-trigger/keep.json",
    "assets/fixtures/skill-trigger/reject.json",
    "assets/fixtures/skill-trigger/spec.json",
]


def _read_skill_description() -> str:
    skill_md = ROOT / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        return ""
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            if key.strip() == "description":
                return value.strip()
    return ""


def _copy(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    if dest.suffix == ".sh":
        dest.chmod(0o755)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export_root", help="Destination directory for the export")
    parser.add_argument("--with-claude-plugin", action="store_true")
    parser.add_argument("--owner-name", default="")
    parser.add_argument("--plugin-description", default="")
    parser.add_argument("--repo-slug", default="")
    parser.add_argument("--license-file", default="")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    export_root = Path(args.export_root).resolve()

    if export_root.exists():
        if not args.force:
            print(f"export directory already exists (use --force): {export_root}", file=sys.stderr)
            return 1
        shutil.rmtree(export_root)

    export_root.mkdir(parents=True)

    # Copy root-level files from the repo root
    for src_name, dest_name in ROOT_FILES:
        src = REPO_ROOT / src_name
        if src.exists():
            _copy(src, export_root / dest_name)

    # Copy skill files
    skill_dest = export_root / "skills" / "autotune"
    for rel in SKILL_FILES:
        src = ROOT / rel
        if src.exists():
            _copy(src, skill_dest / rel)
        else:
            print(f"warning: skill file missing from source: {rel}", file=sys.stderr)

    # Optional license
    if args.license_file:
        license_src = Path(args.license_file)
        if license_src.exists():
            _copy(license_src, export_root / "LICENSE")

    # Optional Claude plugin wrapper
    if args.with_claude_plugin:
        description = args.plugin_description or _read_skill_description()
        owner_name = args.owner_name or "Unknown"

        plugin_data = {
            "name": "autotune",
            "description": description,
            "skills": ["./skills/autotune"],
        }
        marketplace_data = {
            "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
            "name": "autotune",
            "description": description,
            "owner": {"name": owner_name},
            "plugins": [
                {
                    "name": "autotune",
                    "source": "./",
                    "description": description,
                    "skills": ["./skills/autotune"],
                    "strict": False,
                    "category": "development",
                }
            ],
        }

        plugin_dir = export_root / ".claude-plugin"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        (plugin_dir / "plugin.json").write_text(
            json.dumps(plugin_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (plugin_dir / "marketplace.json").write_text(
            json.dumps(marketplace_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    print(f"export complete: {export_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
