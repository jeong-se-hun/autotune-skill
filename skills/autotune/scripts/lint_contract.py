#!/usr/bin/env python3
"""Validate a text-based autotune loop contract."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_FIELDS = [
    "Target",
    "Optimize",
    "Guards",
    "Verify",
    "Budget",
    "Rollback",
]

RECOMMENDED_FIELDS = [
    "Writable scope",
    "Immutable",
    "Log",
    "Baseline",
    "Stop rules",
]


def parse_contract(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z\s]*?):\s*$", line)
        if match:
            if current_key is not None:
                fields[current_key] = "\n".join(current_lines).strip()
            current_key = match.group(1).strip()
            current_lines = []
        elif current_key is not None:
            current_lines.append(line)

    if current_key is not None:
        fields[current_key] = "\n".join(current_lines).strip()

    return fields


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: lint_contract.py <contract.txt>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"file not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    fields = parse_contract(text)
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in fields:
            errors.append(f"missing required field: {field}")
        elif not fields[field].strip():
            errors.append(f"empty required field: {field}")

    loop_mode = fields.get("Loop mode", "").lower()
    continuous_mode = any(kw in loop_mode for kw in ("threshold", "continuous", "high-autonomy"))
    if continuous_mode and "Stop rules" not in fields:
        errors.append(
            "missing required field: Stop rules (required for threshold, continuous, or high-autonomy loops)"
        )

    for field in RECOMMENDED_FIELDS:
        if field == "Stop rules" and continuous_mode:
            continue  # already enforced as error above
        if field not in fields:
            warnings.append(f"missing recommended field: {field}")

    if errors:
        print("lint-contract: failed", file=sys.stderr)
        for error in errors:
            print(f"  error: {error}", file=sys.stderr)
        for warning in warnings:
            print(f"  warning: {warning}", file=sys.stderr)
        return 1

    if warnings:
        for warning in warnings:
            print(f"  warning: {warning}", file=sys.stderr)

    print(f"lint-contract: ok ({len(fields)} fields found)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
