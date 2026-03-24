#!/usr/bin/env python3
"""Score how well autotune's trigger-facing metadata covers the routing benchmark."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVALS_PATH = ROOT / "evals" / "evals.json"
SKILL_PATH = ROOT / "SKILL.md"
OPENAI_PATH = ROOT / "agents" / "openai.yaml"

TAG_PATTERNS = {
    "bounded": ("bounded", "iteration cap", "keep-or-revert"),
    "threshold": ("threshold", "target score", "target-score", "stop target"),
    "continuous": ("continuous", "high autonomy", "higher-autonomy", ".autotune-off"),
    "eval-first": ("build that evaluator first", "build the eval harness first", "step zero", "evaluator first"),
    "human-review": ("human review", "blind comparison", "review pack"),
    "code": ("code", "warning", "latency", "bundle", "tests"),
    "docs": ("docs", "documentation", "runbooks", "runbook"),
    "prompts": ("prompts", "prompt"),
    "skills": ("skills", "skill"),
    "guards": ("guard", "non-regression", "stale command", "contradiction"),
    "holdout": ("holdout",),
    "baseline": ("baseline", "unmodified baseline"),
    "stop-rules": ("stop rules", "stop rule"),
    "high-autonomy": ("high autonomy", "higher-autonomy", "unattended"),
    "review-first": ("do not use", "review findings", "risk discovery", "route to review"),
    "open-ended": ("open-ended", "vague", "make it better"),
    "metric-discovery": ("discovering what metric matters", "what the benchmark should be", "metric matters"),
    "debugging-first": ("debugging", "debugging triage", "route to review, debugging", "investigation"),
    "missing-eval": ("no reproducible eval harness exists yet", "build the eval harness first", "stable evaluator"),
    "missing-stop-rules": ("explicit stop rules", "stop rules", "stop rule"),
    "fixed-eval": ("fixed eval", "fixed evaluator", "fixed metrics", "benchmark"),
}


def _frontmatter_value(skill_text: str, key: str) -> str:
    match = re.match(r"^---\n(.*?)\n---\n", skill_text, flags=re.DOTALL)
    if not match:
        return ""
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        current_key, value = line.split(":", 1)
        if current_key.strip() == key:
            return value.strip()
    return ""


def _section_block(skill_text: str, heading: str) -> str:
    lines = skill_text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index + 1
            break
    if start is None:
        return ""

    block: list[str] = []
    for line in lines[start:]:
        if line.startswith("## ") and line.strip() != heading:
            break
        block.append(line)
    return "\n".join(block).strip()


def load_text_bundle() -> dict[str, str]:
    skill_text = SKILL_PATH.read_text(encoding="utf-8")
    openai_text = OPENAI_PATH.read_text(encoding="utf-8")
    frontmatter_description = _frontmatter_value(skill_text, "description")
    trigger_sections = "\n\n".join(
        part
        for part in (
            frontmatter_description,
            _section_block(skill_text, "## Quick Triage"),
            _section_block(skill_text, "## Use This Skill When"),
            _section_block(skill_text, "## Do Not Use When"),
        )
        if part
    )
    return {
        "combined": f"{trigger_sections}\n{openai_text}".lower(),
        "skill": trigger_sections.lower(),
        "openai": openai_text.lower(),
    }


def has_pattern(text: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern in text for pattern in patterns)


def main() -> int:
    data = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    evals = data.get("evals", [])
    text_bundle = load_text_bundle()
    combined = text_bundle["combined"]

    tag_counts: dict[str, int] = {}
    trigger_total = 0
    reject_total = 0
    covered = 0
    missed: list[dict[str, object]] = []

    for item in evals:
        routing = item.get("routing")
        if not isinstance(routing, dict):
            continue
        should_trigger = bool(routing.get("should_trigger"))
        tags = routing.get("tags", [])
        if not isinstance(tags, list):
            continue
        if should_trigger:
            trigger_total += 1
        else:
            reject_total += 1

        sample_misses = []
        for tag in tags:
            if not isinstance(tag, str):
                continue
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            patterns = TAG_PATTERNS.get(tag, ())
            if not patterns or has_pattern(combined, patterns):
                covered += 1
            else:
                sample_misses.append(tag)

        if sample_misses:
            missed.append(
                {
                    "id": item.get("id"),
                    "should_trigger": should_trigger,
                    "missed_tags": sample_misses,
                    "prompt": item.get("prompt", ""),
                }
            )

    total_tag_expectations = sum(tag_counts.values())
    if total_tag_expectations == 0:
        print(json.dumps({"error": "no routing tags found"}, ensure_ascii=False, indent=2))
        return 1

    unique_tag_coverage = {
        tag: has_pattern(combined, TAG_PATTERNS.get(tag, ()))
        for tag in sorted(tag_counts)
    }
    unique_tags_hit = sum(1 for passed in unique_tag_coverage.values() if passed)

    report = {
        "skill_name": data.get("skill_name"),
        "trigger_samples": trigger_total,
        "reject_samples": reject_total,
        "tag_expectations": total_tag_expectations,
        "covered_tag_expectations": covered,
        "coverage_ratio": round(covered / total_tag_expectations, 4),
        "unique_tags": len(unique_tag_coverage),
        "unique_tags_hit": unique_tags_hit,
        "unique_tag_coverage_ratio": round(unique_tags_hit / len(unique_tag_coverage), 4),
        "missed_cases": missed,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not missed else 2


if __name__ == "__main__":
    raise SystemExit(main())
