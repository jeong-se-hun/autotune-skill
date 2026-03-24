#!/usr/bin/env python3
"""Render a review-pack.json into a static HTML side-by-side review page."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Review Pack — {skill_name} (iteration {iteration})</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 1100px; margin: 2rem auto; padding: 0 1rem; }}
h1 {{ margin-bottom: 0.25rem; }}
.case {{ border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin: 1.5rem 0; }}
.case h2 {{ margin: 0 0 0.5rem; }}
.prompt {{ background: #f5f5f5; padding: 0.75rem; border-radius: 4px; margin: 0.5rem 0; white-space: pre-wrap; }}
.columns {{ display: flex; gap: 1rem; margin: 0.5rem 0; }}
.column {{ flex: 1; }}
.column h3 {{ margin: 0 0 0.5rem; }}
.output {{ background: #fafafa; border: 1px solid #eee; padding: 0.75rem; border-radius: 4px; white-space: pre-wrap; min-height: 4rem; }}
.baseline .output {{ border-left: 3px solid #90caf9; }}
.candidate .output {{ border-left: 3px solid #a5d6a7; }}
.metrics {{ font-size: 0.9rem; color: #555; margin: 0.5rem 0; }}
.notes {{ font-style: italic; color: #666; margin: 0.5rem 0; }}
.decision {{ font-weight: bold; padding: 0.25rem 0.5rem; border-radius: 4px; display: inline-block; }}
.decision.keep {{ background: #e8f5e9; color: #2e7d32; }}
.decision.reject {{ background: #ffebee; color: #c62828; }}
</style>
</head>
<body>
<h1>Review Pack: {skill_name}</h1>
<p>Iteration {iteration} | {summary}</p>
{cases_html}
</body>
</html>
"""


def render_case(case: dict) -> str:
    case_id = esc(str(case.get("id", "")))
    title = esc(str(case.get("title", case_id)))
    prompt = esc(str(case.get("prompt", "")))

    baseline = case.get("baseline", {})
    candidate = case.get("candidate", {})
    if isinstance(baseline, str):
        baseline = {"label": "Baseline", "text": baseline}
    if isinstance(candidate, str):
        candidate = {"label": "Candidate", "text": candidate}

    baseline_label = esc(str(baseline.get("label", "Baseline")))
    baseline_text = esc(str(baseline.get("text", "")))
    candidate_label = esc(str(candidate.get("label", "Candidate")))
    candidate_text = esc(str(candidate.get("text", "")))

    metrics = case.get("metrics", {})
    metrics_html = ", ".join(f"{esc(k)}: {esc(str(v))}" for k, v in metrics.items()) if metrics else ""

    notes = case.get("notes", [])
    notes_html = "<br>".join(esc(str(n)) for n in notes) if notes else ""

    decision = str(case.get("decision", "")).lower()
    decision_class = decision if decision in ("keep", "reject") else ""

    return f"""<div class="case">
<h2>{title}</h2>
<div class="prompt">{prompt}</div>
<div class="columns">
<div class="column baseline"><h3>{baseline_label}</h3><div class="output">{baseline_text}</div></div>
<div class="column candidate"><h3>{candidate_label}</h3><div class="output">{candidate_text}</div></div>
</div>
{'<div class="metrics">' + metrics_html + '</div>' if metrics_html else ''}
{'<div class="notes">' + notes_html + '</div>' if notes_html else ''}
{'<span class="decision ' + decision_class + '">' + esc(decision) + '</span>' if decision else ''}
</div>"""


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: render_review_pack.py <review-pack.json> [-o output.html]", file=sys.stderr)
        return 2

    pack_path = Path(sys.argv[1])
    output_path = None
    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        if idx + 1 < len(sys.argv):
            output_path = sys.argv[idx + 1]

    if not pack_path.exists():
        print(f"file not found: {pack_path}", file=sys.stderr)
        return 1

    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    skill_name = esc(str(pack.get("skill_name", "autotune")))
    iteration = str(pack.get("iteration", "?"))
    summary = esc(str(pack.get("summary", "")))
    cases = pack.get("cases", [])

    cases_html = "\n".join(render_case(case) for case in cases)
    html = HTML_TEMPLATE.format(
        skill_name=skill_name,
        iteration=iteration,
        summary=summary,
        cases_html=cases_html,
    )

    if output_path:
        Path(output_path).write_text(html, encoding="utf-8")
        print(f"review pack rendered to {output_path}")
    else:
        sys.stdout.write(html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
