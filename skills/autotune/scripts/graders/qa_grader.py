#!/usr/bin/env python3
"""Grade a document against a fixed Q&A set using string matching.

Outputs METRIC lines compatible with extract_metrics.py and eval_gate.py.

Q&A set format (JSON):
[
  {"question": "What port does the API run on?", "answer": "8080"},
  {"question": "Who owns the cache service?", "answer": "platform-team"}
]

Each question is graded as pass if the expected answer appears in the document.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def grade(qa_set: list[dict], doc_text: str) -> list[dict]:
    doc_lower = doc_text.lower()
    results = []
    for item in qa_set:
        question = str(item.get("question", ""))
        expected = str(item.get("answer", ""))
        passed = expected.lower() in doc_lower
        results.append({
            "question": question,
            "expected": expected,
            "passed": passed,
        })
    return results


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: qa_grader.py <qa_set.json> <target.md>", file=sys.stderr)
        return 2

    qa_path = Path(sys.argv[1])
    doc_path = Path(sys.argv[2])

    if not qa_path.exists():
        print(f"file not found: {qa_path}", file=sys.stderr)
        return 1
    if not doc_path.exists():
        print(f"file not found: {doc_path}", file=sys.stderr)
        return 1

    raw = json.loads(qa_path.read_text(encoding="utf-8"))
    qa_set = raw if isinstance(raw, list) else [raw]
    doc_text = doc_path.read_text(encoding="utf-8")
    results = grade(qa_set, doc_text)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    accuracy = passed / total if total > 0 else 0.0

    for result in results:
        status = "pass" if result["passed"] else "FAIL"
        print(f"[{status}] {result['question']}")
        if not result["passed"]:
            print(f"       expected: {result['expected']}")

    print(f"\nMETRIC qa_passed={passed}")
    print(f"METRIC qa_total={total}")
    print(f"METRIC qa_accuracy={accuracy:.4f}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
