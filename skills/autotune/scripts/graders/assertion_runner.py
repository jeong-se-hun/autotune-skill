#!/usr/bin/env python3
"""Run binary assertions from a JSON file against a target document.

Outputs METRIC lines compatible with extract_metrics.py and eval_gate.py.

Assertions format (JSON):
[
  {"name": "has-budget-constraint", "type": "contains", "value": "$50,000"},
  {"name": "under-word-limit",     "type": "max_words", "value": 2000},
  {"name": "has-next-steps",       "type": "contains", "value": "next step"}
]

Supported assertion types:
  contains      — case-insensitive substring check
  not_contains  — must NOT contain the substring
  regex         — must match the regex pattern
  min_words     — word count >= value
  max_words     — word count <= value
  min_lines     — line count >= value
  max_lines     — line count <= value
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def check_assertion(assertion: dict, text: str, word_count: int, line_count: int) -> bool:
    atype = str(assertion.get("type", ""))
    value = assertion.get("value")

    if atype == "contains":
        return str(value).lower() in text.lower()
    elif atype == "not_contains":
        return str(value).lower() not in text.lower()
    elif atype == "regex":
        return bool(re.search(str(value), text, re.MULTILINE))
    elif atype == "min_words":
        return word_count >= int(value)
    elif atype == "max_words":
        return word_count <= int(value)
    elif atype == "min_lines":
        return line_count >= int(value)
    elif atype == "max_lines":
        return line_count <= int(value)
    else:
        return False


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: assertion_runner.py <assertions.json> <target.md>", file=sys.stderr)
        return 2

    assertions_path = Path(sys.argv[1])
    doc_path = Path(sys.argv[2])

    if not assertions_path.exists():
        print(f"file not found: {assertions_path}", file=sys.stderr)
        return 1
    if not doc_path.exists():
        print(f"file not found: {doc_path}", file=sys.stderr)
        return 1

    assertions = json.loads(assertions_path.read_text(encoding="utf-8"))
    text = doc_path.read_text(encoding="utf-8")
    word_count = len(text.split())
    line_count = len(text.splitlines())

    passed = 0
    failed = 0
    for assertion in assertions:
        name = str(assertion.get("name", f"assertion-{passed + failed + 1}"))
        result = check_assertion(assertion, text, word_count, line_count)
        if result:
            passed += 1
            print(f"[pass] {name}")
        else:
            failed += 1
            print(f"[FAIL] {name} (type={assertion.get('type')}, value={assertion.get('value')})")

    total = passed + failed
    rate = passed / total if total > 0 else 0.0

    print(f"\nMETRIC assertions_passed={passed}")
    print(f"METRIC assertions_failed={failed}")
    print(f"METRIC assertions_total={total}")
    print(f"METRIC assertion_pass_rate={rate:.4f}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
