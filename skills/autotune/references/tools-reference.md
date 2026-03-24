# Tools Reference

Quick reference for all bundled scripts and resources. Read the relevant section when you need to use a specific tool.

## Core loop scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/extract_metrics.py` | Parse `METRIC name=value` lines → JSON | `python3 scripts/extract_metrics.py benchmark.log` |
| `scripts/eval_gate.py` | Keep/reject decision from numeric metrics | `python3 scripts/eval_gate.py spec.json baseline.json candidate.json` |
| `scripts/rollback.py` | Snapshot files before edits; restore on reject or crash | `python3 scripts/rollback.py snapshot file.py` / `python3 scripts/rollback.py restore file.py` |
| `scripts/lint_eval_spec.py` | Validate eval spec before loop | `python3 scripts/lint_eval_spec.py spec.json` |
| `scripts/validate_log.py` | Validate experiments.jsonl schema | `python3 scripts/validate_log.py experiments.jsonl` |
| `scripts/generate_dashboard.py` | experiments.jsonl → dashboard.html | `python3 scripts/generate_dashboard.py experiments.jsonl -d min` |
| `scripts/render_review_pack.py` | review-pack.json → static HTML side-by-side review page | `python3 scripts/render_review_pack.py experiments/review-pack.json` |
| `scripts/resume_session.py` | Summarize session state for resume | `python3 scripts/resume_session.py experiments.jsonl [spec.json]` |
| `scripts/run_codex_trigger_benchmark.py` | Live holdout routing benchmark against Codex | `python3 scripts/run_codex_trigger_benchmark.py --split holdout --retry-timeout 30` |

## Non-code graders

These produce `METRIC name=value` output compatible with `extract_metrics.py` and `eval_gate.py`.

| Grader | Purpose | Usage |
|--------|---------|-------|
| `scripts/graders/qa_grader.py` | Grade docs against fixed Q&A | `python3 scripts/graders/qa_grader.py qa_set.json target.md` |
| `scripts/graders/section_checker.py` | Check required sections | `python3 scripts/graders/section_checker.py target.md "Setup" "API"` |
| `scripts/graders/assertion_runner.py` | Run binary assertions | `python3 scripts/graders/assertion_runner.py assertions.json target.md` |

These graders are string-matching tools. They work well for factual checks (port numbers, section headers, word counts) but cannot judge subjective quality. For quality grading on documents, proposals, or runbooks, use a grader subagent — see `agents/grader.md`.

## Multi-optimize strategies

`eval_gate.py` supports three strategies via `"strategy"` in spec.json:

| Strategy | Behavior | Use when |
|----------|----------|----------|
| `"all"` (default) | All optimize metrics must improve | Metrics are independent |
| `"primary"` | Only first optimize must improve | One metric dominates |
| `"pareto"` | At least one improves, none regress | Exploring tradeoffs |

## Project detection

`scripts/auto_detect_contract.py` scans a project directory and infers a contract:

Supported: Node.js (package.json), Python (pyproject.toml), Go (go.mod), Rust (Cargo.toml), Skills (SKILL.md), Markdown docs.

```bash
python3 scripts/auto_detect_contract.py /path/to/project --format text
```

## Session scaffold

For long-running or resumable sessions:

```bash
python3 scripts/init_session_scaffold.py <repo_root> --write-agents-block
```

Creates: `autotune.md`, `autotune.spec.json`, `autotune.sh`, `autotune.checks.sh`, `autotune-dashboard.md`, `autotune.ideas.md`, `autotune.jsonl`, `experiments/worklog.md`, `experiments/review-notes.md`, `experiments/review-pack.json`.

See `references/session-scaffold.md` for details.

## Quality checks

| Script | Purpose |
|--------|---------|
| `scripts/self_check.py` | Verify package integrity before sharing |
| `scripts/self_test.py` | Smoke test all bundled scripts |
| `scripts/run_fixture_tests.py` | End-to-end fixture tests |

## Reference docs

| File | When to read |
|------|-------------|
| `references/eval-guide.md` | Writing good evals, optimize vs guard, common mistakes |
| `references/eval-patterns.md` | Benchmark ideas for skills, docs, prompts, code |
| `references/loop-design.md` | Contract design, rollback, anti-gaming |
| `references/contract-templates.md` | Ready-to-copy contracts and eval specs |
| `references/target-guidance.md` | Domain-specific advice (code, docs, proposals, skills, runbooks) |
| `references/schemas.md` | JSON schemas for all file formats |
| `references/session-scaffold.md` | Persistent repo-local session setup |
| `agents/grader.md` | Grader subagent protocol for non-code targets |
| `agents/comparator.md` | Blind pairwise review for baseline versus candidate outputs |
| `agents/analyzer.md` | Post-run synthesis for benchmark noise, tied cases, and next hypotheses |
