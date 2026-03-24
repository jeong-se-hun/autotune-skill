#!/usr/bin/env python3
"""Parse METRIC name=value lines from benchmark output into JSON."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

METRIC_RE = re.compile(r"^METRIC\s+(\S+)\s*=\s*(.+)$", re.MULTILINE)


def parse_metrics(text: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for match in METRIC_RE.finditer(text):
        name = match.group(1)
        raw = match.group(2).strip()
        try:
            metrics[name] = float(raw)
        except ValueError:
            pass
    return metrics


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: extract_metrics.py <file> [file...]", file=sys.stderr)
        print("       cat output.log | extract_metrics.py -", file=sys.stderr)
        return 2

    combined: dict[str, float] = {}
    for arg in sys.argv[1:]:
        if arg == "-":
            text = sys.stdin.read()
        else:
            text = Path(arg).read_text(encoding="utf-8")
        combined.update(parse_metrics(text))

    if not combined:
        print("warning: no METRIC lines found", file=sys.stderr)

    json.dump(combined, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
