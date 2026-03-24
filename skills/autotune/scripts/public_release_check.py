#!/usr/bin/env python3
"""Validate an exported public autotune repository layout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SKILL_NAME = "autotune"
REQUIRED_ROOT_FILES = ("README.md", "README.ko.md", ".gitignore")
# Keep this in sync with export_public_repo.py::SKILL_FILES.
REQUIRED_SKILL_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "agents/grader.md",
    "agents/comparator.md",
    "agents/analyzer.md",
    "scripts/eval_gate.py",
    "scripts/rollback.py",
    "scripts/lint_eval_spec.py",
    "scripts/init_session_scaffold.py",
    "scripts/check_routing_eval_set.py",
    "scripts/run_codex_trigger_benchmark.py",
    "scripts/score_routing_contract.py",
    "scripts/score_autotune_quality.py",
    "scripts/run_fixture_tests.py",
    "scripts/public_release_check.py",
    "scripts/extract_metrics.py",
    "scripts/validate_log.py",
    "scripts/resume_session.py",
    "scripts/generate_dashboard.py",
    "scripts/auto_detect_contract.py",
    "scripts/lint_contract.py",
    "scripts/render_review_pack.py",
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
)
FORBIDDEN_SKILL_FILES = (
    "README.md",
    ".gitignore",
    "scripts/export_public_repo.py",
    "scripts/self_check.py",
    "scripts/self_test.py",
)
FORBIDDEN_SNIPPETS = (
    "/" + "Users" + "/",
    "\\" + "Users" + "\\",
    "~/" + ".codex",
    "/" + "home" + "/",
    "\\\\" + "wsl.localhost" + "\\",
    "file" + "://",
)


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", help="root of the exported public repository")
    parser.add_argument("--expect-claude-plugin", action="store_true")
    parser.add_argument("--expect-license", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        return fail(f"repo root does not exist: {repo_root}")

    for rel in REQUIRED_ROOT_FILES:
        path = repo_root / rel
        if not path.exists():
            return fail(f"missing required repo-root file: {path}")

    skill_root = repo_root / "skills" / SKILL_NAME
    if not skill_root.exists():
        return fail(f"missing skill root: {skill_root}")

    for rel in REQUIRED_SKILL_FILES:
        path = skill_root / rel
        if not path.exists():
            return fail(f"missing required skill file: {path}")

    for rel in FORBIDDEN_SKILL_FILES:
        path = skill_root / rel
        if path.exists():
            return fail(f"unexpected maintainer-only file leaked into public skill export: {path}")

    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")
    readme_ko_text = (repo_root / "README.ko.md").read_text(encoding="utf-8")
    if "npx skills add " not in readme_text or "--skill autotune" not in readme_text:
        return fail("repo README is missing the skills.sh install example")
    if "python3 skills/autotune/scripts/public_release_check.py ." not in readme_text:
        return fail("repo README is missing the exported-repo validation command")
    if "skills/autotune/scripts/export_public_repo.py" in readme_text:
        return fail("repo README should not instruct users to run a source-only export helper from the exported repo")
    if "README.ko.md" not in readme_text:
        return fail("repo README should link to README.ko.md")
    if "README.md" not in readme_ko_text:
        return fail("README.ko.md should link back to README.md")
    if "npx skills add " not in readme_ko_text or "--skill autotune" not in readme_ko_text:
        return fail("README.ko.md is missing the skills.sh install example")

    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for snippet in FORBIDDEN_SNIPPETS:
            if snippet in text:
                return fail(f"user-specific path marker found in {path}: {snippet}")

    if args.expect_claude_plugin:
        plugin_path = repo_root / ".claude-plugin" / "plugin.json"
        marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"
        for path in (plugin_path, marketplace_path):
            if not path.exists():
                return fail(f"missing Claude plugin wrapper file: {path}")

        try:
            plugin_data = json.loads(plugin_path.read_text(encoding="utf-8"))
            marketplace_data = json.loads(marketplace_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return fail(f"Claude plugin metadata is invalid JSON: {exc}")

        if plugin_data.get("name") != SKILL_NAME:
            return fail("Claude plugin wrapper has unexpected name")
        if plugin_data.get("skills") != [f"./skills/{SKILL_NAME}"]:
            return fail("Claude plugin wrapper should reference ./skills/autotune")
        plugin_description = str(plugin_data.get("description", "")).strip()
        if not plugin_description:
            return fail("Claude plugin wrapper should include a non-empty description")

        owner = marketplace_data.get("owner", {}).get("name", "")
        if not str(owner).strip() or owner == "TODO":
            return fail("Claude marketplace metadata still contains a placeholder owner name")
        if str(marketplace_data.get("description", "")).strip() != plugin_description:
            return fail("Claude marketplace metadata should reuse the same description as plugin.json")

        plugins = marketplace_data.get("plugins")
        if not isinstance(plugins, list) or not plugins:
            return fail("Claude marketplace metadata should contain at least one plugin entry")

        primary = plugins[0]
        if primary.get("name") != SKILL_NAME:
            return fail("Claude marketplace metadata should use the skill name in the primary plugin entry")
        if primary.get("source") != "./":
            return fail("Claude marketplace metadata should point plugin source to ./")
        if primary.get("skills") != [f"./skills/{SKILL_NAME}"]:
            return fail("Claude marketplace metadata should reference ./skills/autotune")
        if str(primary.get("description", "")).strip() != plugin_description:
            return fail("Claude marketplace metadata should reuse the same description as plugin.json")

    if args.expect_license and not (repo_root / "LICENSE").exists():
        return fail("expected exported repo to contain LICENSE")

    print("PASS: public release layout checks succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
