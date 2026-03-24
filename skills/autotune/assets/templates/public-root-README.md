# autotune

[한국어 README](README.ko.md)

`autotune` is a public Agent Skill for **metric-driven improvement loops** over code, prompts, docs, tests, skills, and other measurable artifacts.

Its job is not to “make something nicer” in one pass. Its job is to run a disciplined loop when you already have, or explicitly want to build, a stable evaluator:

- fixed benchmarks
- fixed question sets
- assertion checklists
- guard metrics
- holdout splits
- threshold targets
- explicit stop rules

## Why this exists

Many “automatic improvement” workflows fail for one of two reasons:

- the evaluator is loose, so the loop rewards cosmetic changes instead of real gains
- the loop runs without a baseline, guards, or stop rules, so it silently regresses or overfits

`autotune` exists to make those loops stricter.

The core discipline is:

- freeze the eval
- capture a baseline
- test one small hypothesis at a time
- keep or reject with evidence
- refuse high-autonomy looping when stop rules are missing

## What it is specialized for

`autotune` is strongest when the task already has a measurable contract, especially for:

- code optimization against fixed benchmarks
- runbooks, docs, and policies checked by fixed Q&A or assertions
- prompt and skill tuning against frozen eval and holdout sets
- warning cleanup with explicit non-regression guards
- scorecard-driven or review-pack-driven improvement loops

It is intentionally not the default tool for:

- open-ended rewriting
- first-pass debugging or root-cause analysis
- metric discovery with no evaluator yet
- baseline-only diagnosis
- continuous looping with no target threshold or stop rule

## Design influences

This public package was shaped by two strong references:

- Anthropic’s [`skill-creator`](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
  - especially its emphasis on evals, iteration, review, and trigger quality
- Karpathy’s [`autoresearch`](https://github.com/karpathy/autoresearch)
  - especially its emphasis on disciplined loops, simple hypotheses, baselines, and experimental rigor

`autotune` is not trying to clone either project. It narrows those ideas into a stricter reusable skill for **eval-first tuning loops**.

## Key capabilities

- supports `bounded`, `threshold`, and `continuous` loop modes
- requires optimize metrics, guard metrics, and explicit stop logic
- supports holdout-backed tuning and public trigger evaluation
- includes scaffolding for logs, dashboards, state, and repeatable loop contracts
- includes scorecard, grader, analyzer, comparator, and review-pack support
- includes public-release checks and live trigger benchmarking for Codex

## Install

### skills.sh

```bash
npx skills add __REPO_SLUG__ --skill autotune
```

### Codex

Point Codex at the exported `skills/autotune` directory through a standard Agent Skills location such as:

- project: `.agents/skills/autotune`
- user: another Codex-recognized Agent Skills directory

### Claude Code, Gemini CLI, and other skills-compatible tools

Install or copy the exported `skills/autotune` directory into the tool’s standard skills location.

## Repository layout

```text
repo-root/
├── README.md
├── README.ko.md
├── .gitignore
├── LICENSE
├── skills/
│   └── autotune/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       ├── scripts/
│       ├── references/
│       ├── assets/
│       └── evals/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
```

## Validation

From the exported repo root:

```bash
python3 skills/autotune/scripts/public_release_check.py .
```

The package also includes:

- fixture tests
- routing contract checks
- live trigger benchmarking
- quality scoring

## Packaging notes

- The portable core skill lives in `skills/autotune/`.
- `agents/openai.yaml` preserves Codex-facing metadata where supported.
- `.claude-plugin/` is an optional Claude Code marketplace wrapper.
- skills.sh users can ignore `.claude-plugin/`.
