#!/usr/bin/env python3
"""Validate an experiments.jsonl log file."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_FIELDS = {
    "iteration": int,
    "hypothesis": str,
    "optimize_value": (int, float),
    "guard_passed": bool,
    "decision": str,
    "note": str,
}
VALID_DECISIONS = {"keep", "reject", "crash", "baseline", "reset_baseline"}


def validate_entry(index: int, entry: dict) -> list[str]:
    errors: list[str] = []
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in entry:
            errors.append(f"line {index + 1}: missing required field: {field}")
            continue
        value = entry[field]
        if isinstance(expected_type, tuple):
            if not isinstance(value, expected_type) or isinstance(value, bool):
                errors.append(f"line {index + 1}: {field} must be numeric, got {type(value).__name__}")
        elif not isinstance(value, expected_type):
            errors.append(f"line {index + 1}: {field} must be {expected_type.__name__}, got {type(value).__name__}")

    if "hypothesis" in entry and isinstance(entry["hypothesis"], str) and not entry["hypothesis"].strip():
        errors.append(f"line {index + 1}: hypothesis must be non-empty")

    if "decision" in entry and entry["decision"] not in VALID_DECISIONS:
        errors.append(f"line {index + 1}: decision must be one of {sorted(VALID_DECISIONS)}, got {entry['decision']!r}")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_log.py <experiments.jsonl>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"file not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        print("log is empty (no entries to validate)")
        return 0

    all_errors: list[str] = []
    entries = 0
    for index, line in enumerate(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            all_errors.append(f"line {index + 1}: invalid JSON: {exc}")
            continue
        if not isinstance(entry, dict):
            all_errors.append(f"line {index + 1}: entry must be a JSON object")
            continue
        all_errors.extend(validate_entry(index, entry))
        entries += 1

    if all_errors:
        print("validate-log: failed", file=sys.stderr)
        for error in all_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"validate-log: ok ({entries} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
