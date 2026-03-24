#!/usr/bin/env python3
"""Generate an HTML dashboard from an experiments.jsonl log."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Autotune Dashboard</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: left; }}
th {{ background: #f5f5f5; }}
tr.keep {{ background: #e8f5e9; }}
tr.reject {{ background: #ffebee; }}
tr.crash {{ background: #fff3e0; }}
tr.baseline {{ background: #e3f2fd; }}
.summary {{ display: flex; gap: 2rem; margin: 1rem 0; }}
.summary div {{ padding: 1rem; border-radius: 8px; background: #f5f5f5; flex: 1; }}
.summary .value {{ font-size: 1.5rem; font-weight: bold; }}
h1 {{ margin-bottom: 0.5rem; }}
</style>
</head>
<body>
<h1>Autotune Dashboard</h1>
<p>Direction: <strong>{direction}</strong> | Entries: <strong>{total}</strong></p>
<div class="summary">
<div><div class="value">{kept}</div>Kept</div>
<div><div class="value">{rejected}</div>Rejected</div>
<div><div class="value">{crashed}</div>Crashed</div>
<div><div class="value">{best_value}</div>Best</div>
</div>
<table>
<thead><tr><th>#</th><th>Hypothesis</th><th>Value</th><th>Guards</th><th>Decision</th><th>Note</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</body>
</html>
"""


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", help="Path to experiments.jsonl")
    parser.add_argument("-d", "--direction", default="min", choices=["min", "max"])
    parser.add_argument("-o", "--output", help="Output HTML path (default: stdout)")
    args = parser.parse_args()

    path = Path(args.log)
    if not path.exists():
        print(f"file not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8").strip()
    entries = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))

    if not entries:
        print("no entries in log", file=sys.stderr)
        return 1

    kept = sum(1 for e in entries if e.get("decision") == "keep")
    rejected = sum(1 for e in entries if e.get("decision") == "reject")
    crashed = sum(1 for e in entries if e.get("decision") == "crash")
    values = [e["optimize_value"] for e in entries if "optimize_value" in e]
    best_value = min(values) if args.direction == "min" else max(values) if values else "N/A"

    rows = []
    for entry in entries:
        decision = entry.get("decision", "")
        row = (
            f'<tr class="{esc(decision)}">'
            f"<td>{entry.get('iteration', '')}</td>"
            f"<td>{esc(str(entry.get('hypothesis', '')))}</td>"
            f"<td>{entry.get('optimize_value', '')}</td>"
            f'<td>{"pass" if entry.get("guard_passed") else "fail"}</td>'
            f"<td>{esc(decision)}</td>"
            f"<td>{esc(str(entry.get('note', '')))}</td>"
            f"</tr>"
        )
        rows.append(row)

    html = HTML_TEMPLATE.format(
        direction=args.direction,
        total=len(entries),
        kept=kept,
        rejected=rejected,
        crashed=crashed,
        best_value=best_value,
        rows="\n".join(rows),
    )

    if args.output:
        Path(args.output).write_text(html, encoding="utf-8")
        print(f"dashboard written to {args.output}")
    else:
        sys.stdout.write(html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
