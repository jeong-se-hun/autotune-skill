#!/usr/bin/env python3
"""Score autotune itself across strict package-quality axes."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELF_CHECK = ROOT / "scripts" / "self_check.py"
SELF_TEST = ROOT / "scripts" / "self_test.py"
FIXTURE_TESTS = ROOT / "scripts" / "run_fixture_tests.py"
ROUTING_CHECK = ROOT / "scripts" / "check_routing_eval_set.py"
ROUTING_SCORE = ROOT / "scripts" / "score_routing_contract.py"
LIVE_TRIGGER = ROOT / "scripts" / "run_codex_trigger_benchmark.py"
EXPORT_PUBLIC_REPO = ROOT / "scripts" / "export_public_repo.py"
PUBLIC_RELEASE_CHECK = ROOT / "scripts" / "public_release_check.py"
EVALS_PATH = ROOT / "evals" / "evals.json"
SKILL_PATH = ROOT / "SKILL.md"
PUBLIC_PATH = ROOT / "references" / "public-publishing.md"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def read_json_output(cmd: list[str]) -> tuple[int, dict]:
    completed = run(cmd)
    data = json.loads(completed.stdout or "{}")
    return completed.returncode, data


def ratio(parts: list[bool]) -> float:
    if not parts:
        return 0.0
    return sum(1 for item in parts if item) / len(parts)


def main() -> int:
    self_check = run(["python3", str(SELF_CHECK)])
    self_test = run(["python3", str(SELF_TEST)])
    fixture_tests = run(["python3", str(FIXTURE_TESTS)])
    routing_check = run(["python3", str(ROUTING_CHECK)])
    routing_score_code, routing_score = read_json_output(["python3", str(ROUTING_SCORE)])

    with tempfile.TemporaryDirectory(prefix="autotune-quality-export-") as tmp:
        export_root = Path(tmp) / "public-skill"
        export_run = run(
            [
                "python3",
                str(EXPORT_PUBLIC_REPO),
                str(export_root),
                "--with-claude-plugin",
                "--owner-name",
                "Example Owner",
                "--plugin-description",
                "Example public description",
                "--repo-slug",
                "example/autotune-skill",
                "--license-file",
                "/etc/hosts",
            ]
        )
        public_release = run(
            [
                "python3",
                str(PUBLIC_RELEASE_CHECK),
                str(export_root),
                "--expect-claude-plugin",
                "--expect-license",
            ]
        )

    live_code = None
    live_report: dict = {"runner_available": False}
    if shutil.which("codex") is not None:
        live_code, live_report = read_json_output(["python3", str(LIVE_TRIGGER)])

    evals = json.loads(EVALS_PATH.read_text(encoding="utf-8")).get("evals", [])
    positives = [item for item in evals if item["routing"]["should_trigger"]]
    negatives = [item for item in evals if not item["routing"]["should_trigger"]]
    train = [item for item in evals if item["routing"]["split"] == "train"]
    holdout = [item for item in evals if item["routing"]["split"] == "holdout"]
    holdout_positive = [item for item in holdout if item["routing"]["should_trigger"]]
    holdout_negative = [item for item in holdout if not item["routing"]["should_trigger"]]
    prompts = [item["prompt"] for item in evals]

    skill_lines = len(SKILL_PATH.read_text(encoding="utf-8").splitlines())
    public_lines = len(PUBLIC_PATH.read_text(encoding="utf-8").splitlines())
    skill_text = SKILL_PATH.read_text(encoding="utf-8")
    public_text = PUBLIC_PATH.read_text(encoding="utf-8").lower()

    routing_dataset_score = ratio(
        [
            len(evals) >= 18,
            len(positives) >= 10,
            len(negatives) >= 6,
            bool(train),
            bool(holdout),
            len(holdout_positive) >= 3,
            len(holdout_negative) >= 3,
            any(any("a" <= ch.lower() <= "z" for ch in prompt) for prompt in prompts),
            any(any("\uac00" <= ch <= "\ud7a3" for ch in prompt) for prompt in prompts),
        ]
    )

    clarity_score = ratio(
        [
            skill_lines <= 350,
            public_lines <= 120,
            "## Quick Triage" in skill_text,
            "## Use This Skill When" in skill_text,
            "## Do Not Use When" in skill_text,
            "portable" in public_text,
        ]
    )

    autonomy_score = ratio(
        [
            "`bounded`" in skill_text,
            "`threshold`" in skill_text,
            "`continuous`" in skill_text,
            "Stop rules" in skill_text,
            "holdout" in skill_text.lower(),
            "scorecard" in skill_text.lower(),
            ".autotune-off" in skill_text,
        ]
    )

    tooling_coverage_score = ratio(
        [
            (ROOT / "scripts" / "eval_gate.py").exists(),
            (ROOT / "scripts" / "lint_eval_spec.py").exists(),
            (ROOT / "scripts" / "check_routing_eval_set.py").exists(),
            (ROOT / "scripts" / "score_routing_contract.py").exists(),
            (ROOT / "scripts" / "run_codex_trigger_benchmark.py").exists(),
            (ROOT / "scripts" / "score_autotune_quality.py").exists(),
            (ROOT / "evals" / "autotune-quality.spec.json").exists(),
            (ROOT / "references" / "live-trigger-benchmark.md").exists(),
        ]
    )

    integrity_score = ratio(
        [
            self_check.returncode == 0,
            self_test.returncode == 0,
            fixture_tests.returncode == 0,
            routing_check.returncode == 0,
        ]
    )
    portability_score = ratio([export_run.returncode == 0, public_release.returncode == 0])
    proxy_trigger_score = float(routing_score.get("coverage_ratio", 0.0)) if routing_score_code == 0 else 0.0
    live_trigger_score = float(live_report.get("live_trigger_score", 0.0)) if live_report.get("runner_available") else 0.0

    aspects = {
        "integrity_score": round(integrity_score, 4),
        "portability_score": round(portability_score, 4),
        "routing_dataset_score": round(routing_dataset_score, 4),
        "proxy_trigger_score": round(proxy_trigger_score, 4),
        "live_trigger_score": round(live_trigger_score, 4),
        "clarity_score": round(clarity_score, 4),
        "autonomy_score": round(autonomy_score, 4),
        "tooling_coverage_score": round(tooling_coverage_score, 4),
    }
    overall_score = round(sum(aspects.values()) / len(aspects), 4)

    report = {
        "overall_score": overall_score,
        "overall_score_10": round(overall_score * 10, 2),
        "aspect_scores": aspects,
        "aspect_scores_10": {name: round(value * 10, 2) for name, value in aspects.items()},
        "raw": {
            "skill_lines": skill_lines,
            "public_lines": public_lines,
            "eval_count": len(evals),
            "positive_count": len(positives),
            "negative_count": len(negatives),
            "train_count": len(train),
            "holdout_count": len(holdout),
            "holdout_positive_count": len(holdout_positive),
            "holdout_negative_count": len(holdout_negative),
            "proxy_trigger": routing_score,
            "live_trigger": live_report,
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
