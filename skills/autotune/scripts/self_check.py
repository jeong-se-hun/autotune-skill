#!/usr/bin/env python3
"""Verify autotune package integrity before sharing."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
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
    "scripts/render_review_pack.py",
    "scripts/auto_detect_contract.py",
    "scripts/lint_contract.py",
    "scripts/init_session_scaffold.py",
    "scripts/self_check.py",
    "scripts/self_test.py",
    "scripts/run_fixture_tests.py",
    "scripts/check_routing_eval_set.py",
    "scripts/score_routing_contract.py",
    "scripts/run_codex_trigger_benchmark.py",
    "scripts/score_autotune_quality.py",
    "scripts/public_release_check.py",
    "scripts/graders/qa_grader.py",
    "scripts/graders/section_checker.py",
    "scripts/graders/assertion_runner.py",
    "evals/evals.json",
    "evals/trigger-eval-set.json",
    "evals/autotune-quality.spec.json",
    "references/autonomy-modes.md",
    "references/contract-templates.md",
    "references/eval-patterns.md",
    "references/eval-guide.md",
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
    "assets/templates/autotune.md",
    "assets/templates/autotune.spec.json",
    "assets/templates/autotune.state.json",
    "assets/templates/autotune.sh",
    "assets/templates/autotune.checks.sh",
    "assets/templates/autotune-dashboard.md",
    "assets/templates/autotune.ideas.md",
    "assets/templates/AGENTS.autotune.md",
    "assets/templates/experiments-worklog.md",
    "assets/templates/experiments-review-notes.md",
    "assets/templates/experiments-review-pack.json",
]


def main() -> int:
    missing: list[str] = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            missing.append(rel)

    if missing:
        print("self-check: failed", file=sys.stderr)
        for path in missing:
            print(f"  missing: {path}", file=sys.stderr)
        return 1

    print(f"self-check: ok ({len(REQUIRED_FILES)} files verified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
