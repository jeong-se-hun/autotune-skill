#!/usr/bin/env python3
"""Summarize session state from an experiments log for loop resumption."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BASELINE_DECISIONS = {"baseline", "reset_baseline"}


def load_entries(path: Path) -> tuple[list[dict], list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    entries: list[dict] = []
    warnings: list[str] = []
    non_empty_indices = [index for index, raw in enumerate(lines) if raw.strip()]
    last_non_empty_index = non_empty_indices[-1] if non_empty_indices else None

    for index, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            if index == last_non_empty_index:
                warnings.append(f"ignored malformed trailing line {index + 1}: {exc.msg}")
                break
            raise ValueError(f"invalid JSON on line {index + 1}: {exc}") from exc
        if not isinstance(entry, dict):
            raise ValueError(f"line {index + 1} must be a JSON object")
        entries.append(entry)

    return entries, warnings


def infer_direction(spec_path: str | None) -> str:
    if spec_path is None:
        return "min"
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    optimize = spec.get("optimize", [])
    if optimize:
        return str(optimize[0].get("direction", "min"))
    return "min"


def current_segment(entries: list[dict]) -> list[dict]:
    start = 0
    for index, entry in enumerate(entries):
        if entry.get("decision") in BASELINE_DECISIONS:
            start = index
    return entries[start:]


def main() -> int:
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("usage: resume_session.py <experiments.jsonl> [spec.json]", file=sys.stderr)
        return 2

    log_path = Path(sys.argv[1])
    spec_path = sys.argv[2] if len(sys.argv) == 3 else None

    if not log_path.exists():
        print(f"file not found: {log_path}", file=sys.stderr)
        return 1

    try:
        entries, warnings = load_entries(log_path)
    except ValueError as exc:
        print(f"resume-session: {exc}", file=sys.stderr)
        return 1

    if not entries:
        print(json.dumps({"status": "empty", "total_iterations": 0}, indent=2))
        return 0

    direction = infer_direction(spec_path)
    segment = current_segment(entries)
    kept = [e for e in segment if e.get("decision") == "keep"]
    rejected = [e for e in segment if e.get("decision") == "reject"]
    baseline_entry = next(
        (e for e in reversed(segment) if e.get("decision") in BASELINE_DECISIONS),
        None,
    )
    baseline_value = baseline_entry["optimize_value"] if baseline_entry else None

    if direction == "min":
        best = min(kept, key=lambda e: e["optimize_value"]) if kept else baseline_entry
    else:
        best = max(kept, key=lambda e: e["optimize_value"]) if kept else baseline_entry

    result = {
        "status": "active",
        "total_iterations": len(entries),
        "current_segment_iterations": len(segment),
        "kept": len(kept),
        "rejected": len(rejected),
        "baseline_value": baseline_value,
        "current_best": {
            "iteration": best["iteration"],
            "optimize_value": best["optimize_value"],
            "hypothesis": best.get("hypothesis", ""),
        } if best else None,
        "last_entry": {
            "iteration": entries[-1]["iteration"],
            "decision": entries[-1]["decision"],
            "optimize_value": entries[-1]["optimize_value"],
        },
        "rejected_hypotheses": [e.get("hypothesis", "") for e in rejected],
        "direction": direction,
    }
    if warnings:
        result["warnings"] = warnings
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
