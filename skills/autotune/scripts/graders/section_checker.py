#!/usr/bin/env python3
"""Check that a document contains all required section headers.

Outputs METRIC lines compatible with extract_metrics.py and eval_gate.py.

Usage:
    section_checker.py target.md "Setup" "API Reference" "Troubleshooting"
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def find_sections(text: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(r"^#{1,6}\s+(.+)$", text, re.MULTILINE)
    ]


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: section_checker.py <target.md> <section1> [section2] ...", file=sys.stderr)
        return 2

    doc_path = Path(sys.argv[1])
    required = sys.argv[2:]

    if not doc_path.exists():
        print(f"file not found: {doc_path}", file=sys.stderr)
        return 1

    text = doc_path.read_text(encoding="utf-8")
    found_sections = find_sections(text)
    found_lower = [s.lower() for s in found_sections]

    present = 0
    missing: list[str] = []
    for section in required:
        if section.lower() in found_lower:
            present += 1
            print(f"[pass] {section}")
        else:
            missing.append(section)
            print(f"[FAIL] {section}")

    total = len(required)
    coverage = present / total if total > 0 else 0.0

    print(f"\nMETRIC sections_present={present}")
    print(f"METRIC sections_required={total}")
    print(f"METRIC sections_missing={len(missing)}")
    print(f"METRIC section_coverage={coverage:.4f}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
