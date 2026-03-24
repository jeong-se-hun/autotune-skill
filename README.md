# autotune

[한국어 README](README.ko.md)

**Stop guessing. Improve with evidence.**

`autotune` is an Agent Skill that runs metric-driven keep-or-reject improvement loops over prompts, skills, docs, code, and tests — with guard metrics, rollback safety, and explicit stop rules.

- **Measured improvement** against a fixed benchmark
- **Guard metrics** that block regressions even when the optimize metric improves
- **Rollback safety** when a candidate fails
- **Explicit stop rules** for bounded, threshold, or continuous runs
- **One workflow** for prompts, skills, docs, and code

---

## What a session looks like

> No vibes. No "looks better to me."
> One hypothesis, one change, one verification step at a time.

```
Baseline:        lint_warnings=18, tests_failed=0
────────────────────────────────────────────────
Iter 1  remove unused imports          18 → 12   KEEP
Iter 2  inline redundant wrapper       12 →  9   KEEP
Iter 3  aggressive inlining attempt     9 →  9   REJECT  (no gain)
Iter 4  extract repeated expression     9 →  7   KEEP
────────────────────────────────────────────────
Result:  lint_warnings=7 (↓61%), tests_failed=0 (guard held)
Stop:    budget exhausted (3 kept / 1 rejected)
```

`baseline → propose → verify → keep or revert`

Guard metrics block regressions even when the optimize metric improves.

---

## The three things it does best

### 1. Prompt and skill tuning
Tune trigger accuracy, task success rate, or output quality against a fixed eval set with a holdout split. Cosmetic rewrites that don't move benchmark scores get rejected automatically.

### 2. Docs, runbooks, and policies
Improve answer accuracy against a fixed Q&A set while keeping contradiction count and stale command count at zero. Each candidate is compared against the same fixed questions as the baseline.

### 3. Code optimization
Reduce lint warnings, bundle size, latency, or memory while keeping tests and type checks green. One file at a time, with `/tmp` snapshots for clean rollback.

---

## Usage examples

> **An eval is ready when three things are defined: what to optimize, what must not break (guards), and how to measure both (verify command).** If all three are in place, autotune starts the loop immediately. If not, it drafts them first.

### No eval yet? State the goal — autotune drafts the eval first.

You don't need an eval ready before you start. Say what you want to improve and what must not break:

> "I want to improve this prompt. I don't have an eval set. It should handle edge cases better without increasing token cost."

autotune drafts the eval — fixed questions, guard conditions, verification command — and presents it for review. In supervised mode, the loop starts only after you confirm. In high-autonomy mode, it logs the draft and proceeds immediately. Building the eval is step zero, not something you handle separately.

### bounded — short session, fixed budget (default)

> "Run 3 iterations on `src/api.py`. Reduce lint warnings. Keep tests green."

Three iterations. Each candidate must reduce `lint_warnings` and keep `tests_failed=0`. The file is snapshotted before each edit and restored automatically on reject or crash.

### threshold — run until a target is reached

> "Improve this runbook's Q&A accuracy to 90% or above. Stop if contradiction_count goes above 0."

Runs until `answer_accuracy >= 0.90`. Any candidate that introduces a contradiction is rejected even if accuracy improves. Requires an explicit target score before starting.

### continuous — unattended loop with explicit stop rules

> "Tune this skill's trigger precision in high-autonomy mode. Stop after 3 consecutive rejects or if false_positive_rate exceeds 0.05. Drop `.autotune-off` to halt."

Runs until a declared stop rule fires. Every iteration logs a hypothesis, decision, and metric values to an append-only experiment log so the session can be resumed or audited later.

---

## When NOT to use this

- You want feedback, risk discovery, or cross-review — not optimization → use a review skill instead
- You only want the current state or a weakness summary → run a baseline first, then decide
- The request is "just make it nicer" with no stable pass/fail signal
- You want "run as long as possible, stop when it seems better" with no target score or stop rule
- You are still doing root-cause analysis or debugging before any metric is defined

---

## Install

### skills.sh

```bash
npx skills add jeong-se-hun/autotune-skill --skill autotune
```

### Codex

Copy or symlink `skills/autotune` into a Codex-recognized Agent Skills path:

- project: `.agents/skills/autotune`
- user: your Codex user skills directory

### Claude Code, Gemini CLI, and other skills-compatible tools

Copy `skills/autotune` into the tool's standard skills location.

---

## How it works

**Loop modes**

| Mode | When to use |
|------|-------------|
| `bounded` | Short session, fixed iteration cap (default) |
| `threshold` | Run until a target score is reached |
| `continuous` | Unattended loop with explicit stop rules |

**Autonomy levels**: `supervised` → `batched-review` → `high-autonomy`

Every loop requires: an optimize metric, at least one guard metric, a verification command, and explicit stop rules for threshold or continuous modes.

---

## Design influences

- Karpathy's [`autoresearch`](https://github.com/karpathy/autoresearch) — baseline discipline, small hypotheses, experimental rigor. autoresearch targets GPU research loops; autotune targets prompts, skills, docs, and code with eval guards and rollback safety.
- Anthropic's [`skill-creator`](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) — eval-first iteration, trigger quality, holdout discipline.

---

## Repository layout

```
repo-root/
├── README.md
├── README.ko.md
├── skills/
│   └── autotune/
│       ├── SKILL.md
│       ├── agents/
│       ├── scripts/       20 scripts + 3 graders
│       ├── references/    14 reference docs
│       ├── assets/        templates + fixtures
│       └── evals/
└── .claude-plugin/        optional Claude marketplace wrapper
```

## Validate the package

From the skill source directory:

```bash
python3 skills/autotune/scripts/self_check.py
python3 skills/autotune/scripts/self_test.py
```

From an exported public repo root (after running `export_public_repo.py`):

```bash
python3 skills/autotune/scripts/public_release_check.py .
```
