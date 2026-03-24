# JSON Schemas

Exact schemas for all JSON files autotune produces or consumes. Reference this when generating files manually or validating existing ones.

---

## evals.json

Skill eval prompts. Located at `evals/evals.json`.

```json
{
  "skill_name": "autotune",
  "evals": [
    {
      "id": 1,
      "prompt": "The user's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

**Fields:**
- `skill_name`: Must match the skill's frontmatter name
- `evals[].id`: Unique integer
- `evals[].prompt`: Task to evaluate
- `evals[].expected_output`: Human-readable success description
- `evals[].files`: Optional input file paths

---

## trigger-eval-set.json

Trigger benchmark queries. Located at `evals/trigger-eval-set.json`.

```json
[
  {
    "query": "pytest는 전부 통과해야 해. p95 latency를 줄이고 싶은데...",
    "should_trigger": true,
    "split": "train",
    "tags": ["code", "guards", "fixed-eval"],
    "note": "optional explanation"
  }
]
```

**Fields:**
- `query`: Realistic user prompt
- `should_trigger`: Whether autotune should activate
- `split`: `"train"` or `"holdout"` — determines which cases are used for live benchmark
- `tags`: Array of routing tags (e.g. `"code"`, `"guards"`, `"missing-stop-rules"`, `"review-first"`)
- `note`: Optional context for edge cases

---

## experiments.jsonl

Append-only experiment log. One JSON object per line.

```json
{"iteration":1,"hypothesis":"remove unused import","optimize_value":11,"guard_passed":true,"decision":"keep","note":"12→11, tests pass"}
```

**Required fields:**
- `iteration` (int): Iteration number, starting from 0 for baseline
- `hypothesis` (string): Non-empty testable claim
- `optimize_value` (number): Measured value of the optimize metric
- `guard_passed` (bool): Whether all guards passed
- `decision` (string): One of `"keep"`, `"reject"`, `"crash"`, `"baseline"`, `"reset_baseline"`
- `note` (string): Brief explanation of the decision

Validate with: `python3 scripts/validate_log.py experiments.jsonl`

---

## spec.json (eval spec)

Defines optimize metrics, guards, and strategy. Used by `eval_gate.py` and `lint_eval_spec.py`.

```json
{
  "strategy": "all",
  "optimize": [
    {
      "name": "lint_warnings",
      "direction": "min",
      "min_delta": 1
    }
  ],
  "guards": [
    {
      "name": "tests_failed",
      "kind": "absolute_max",
      "value": 0
    },
    {
      "name": "token_cost",
      "kind": "relative_max",
      "value": 1.05
    }
  ]
}
```

**Top-level fields:**
- `strategy` (optional): `"all"` (default), `"primary"`, or `"pareto"`
- `optimize[]`: At least one required
- `guards[]`: Optional array

**optimize[] fields:**
- `name` (string): Metric name
- `direction`: `"min"` or `"max"`
- `min_delta` (number, optional): Minimum improvement threshold (default: 0)

**guards[] fields:**
- `name` (string): Metric name (must not overlap with optimize names)
- `kind`: `"absolute_max"`, `"absolute_min"`, `"relative_max"`, or `"relative_min"`
- `value` (number): Threshold. For relative kinds, this is a multiplier (e.g., 1.05 = 5% above baseline)

Validate with: `python3 scripts/lint_eval_spec.py spec.json`

---

## grading.json (from grader subagent)

Output from `agents/grader.md`. Used for non-code targets.

```json
{
  "results": [
    {
      "question": "How do you recover from a cache miss?",
      "passed": true,
      "evidence": "Section 3.2: 'restart memcached, then run warm-up script'"
    }
  ],
  "summary": {
    "passed": 1,
    "failed": 1,
    "total": 2,
    "pass_rate": 0.5
  }
}
```

**Fields:**
- `results[].question`: The question evaluated
- `results[].passed`: Boolean verdict
- `results[].evidence`: Quoted passage or explanation of what's missing
- `summary`: Aggregate counts

---

## review-pack.json

Side-by-side human review artifact for baseline versus candidate outputs. Often stored under `experiments/review-pack.json`.

```json
{
  "skill_name": "autotune",
  "iteration": 2,
  "summary": "Candidate improves task success with flat token cost.",
  "cases": [
    {
      "id": "holdout-doc-3",
      "title": "Holdout cache-failover runbook case",
      "prompt": "Fixed prompt or task shown to both baseline and candidate",
      "baseline": {
        "label": "Baseline",
        "text": "Summarized or raw baseline output"
      },
      "candidate": {
        "label": "Candidate",
        "text": "Summarized or raw candidate output"
      },
      "metrics": {
        "task_success": "0.72 -> 0.79",
        "token_cost": "103 -> 101"
      },
      "notes": [
        "Candidate is clearer about prerequisites."
      ],
      "decision": "keep"
    }
  ]
}
```

**Fields:**
- `skill_name`: Skill or target name
- `iteration`: Loop iteration number or label
- `summary`: Optional loop-level summary
- `cases[]`: Representative baseline-versus-candidate examples
- `cases[].id`: Stable case identifier
- `cases[].title`: Human-readable label
- `cases[].prompt`: Shared input shown to both versions
- `cases[].baseline` / `cases[].candidate`: Either a string or an object with `label` and `text`
- `cases[].metrics`: Optional per-case metric dictionary
- `cases[].notes`: Optional reviewer notes as a string array
- `cases[].decision`: Optional case-level decision such as `keep`, `reject`, or `undecided`

Render with: `python3 scripts/render_review_pack.py experiments/review-pack.json`

---

## resume output (from resume_session.py)

```json
{
  "status": "active",
  "total_iterations": 3,
  "current_segment_iterations": 2,
  "kept": 2,
  "rejected": 1,
  "baseline_value": 12,
  "current_best": {
    "iteration": 2,
    "optimize_value": 7,
    "hypothesis": "inline helper function"
  },
  "last_entry": {
    "iteration": 3,
    "decision": "reject",
    "optimize_value": 8
  },
  "rejected_hypotheses": ["remove error handler"],
  "direction": "min",
  "warnings": ["ignored malformed trailing line 4: Expecting ',' delimiter"]
}
```

**Notes:**
- `baseline_value` is taken from the latest `baseline` or `reset_baseline` entry in the active segment.
- `current_segment_iterations` counts entries since the latest baseline reset.
- `warnings` is optional and appears when the tool ignores a malformed trailing line caused by an interrupted append.
