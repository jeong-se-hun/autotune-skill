# Eval Guide

How to write evals that actually improve your target instead of giving you false confidence.

---

## The golden rule

Every eval must be answerable as **yes/no or a single number**. Not a scale. Not a vibe check.

Why: "Scales compound variability. If you have 4 evals scored 1-7, your total score has massive variance across runs." Binary or numeric evals give you a reliable signal for keep-or-revert decisions.

---

## Good evals vs bad evals

### Code (performance, lint, tests)

**Bad evals:**
- "Is the code clean?" (subjective)
- "Rate code quality 1-10" (scale = unreliable keep/revert)
- "Does it follow best practices?" (which ones?)

**Good evals:**
- "Does `npm test` exit 0?" (binary, executable)
- "Is `lint_warnings` count lower than baseline?" (numeric, measurable)
- "Is bundle size under 150KB?" (numeric, measurable)
- "Does p95 latency stay under 200ms?" (numeric, guard-ready)

### Skills and prompts

**Bad evals:**
- "Does the skill work well?" (too vague)
- "Rate the output quality 1-5" (scale)

**Good evals:**
- "Does the skill trigger on this specific prompt?" (binary)
- "Does the output contain the required section headers?" (binary, greppable)
- "Is the false positive rate below 10%?" (numeric)
- "Is output token count under 500?" (numeric)

### Documents and specs

**Bad evals:**
- "Is it comprehensive?" (compared to what?)
- "Does it address the client's needs?" (too open-ended)

**Good evals:**
- "Does the doc contain all required sections: [list]?" (binary)
- "Is every claim backed by a specific number or source?" (binary)
- "Can a reader implement feature X using only this doc?" (binary, task-grounded)
- "Is stale_command_count == 0?" (numeric)

### Ideas and proposals

**Bad evals:**
- "Is it convincing?" (subjective)
- "Would stakeholders approve this?" (unverifiable by script)

**Good evals:**
- "Does every claim cite a specific number, date, or source?" (binary, checkable)
- "Is there a concrete next-step action item in the conclusion?" (binary)
- "Does the proposal stay within the stated budget constraint?" (binary, numeric)
- "Are all acceptance criteria from the brief addressed?" (binary, countable)
- "Is total word count under the requested limit?" (numeric)

### Runbooks and operational docs

**Bad evals:**
- "Is the runbook complete?" (compared to what?)
- "Would oncall use this?" (unknowable)

**Good evals:**
- "Does every step have an expected output or success indicator?" (binary)
- "Are all prerequisite tools listed before the first command?" (binary)
- "Can a reader recover from incident X following only this doc?" (binary, task-grounded)
- "Is unsafe_command_count == 0?" (numeric)

---

## Optimize vs Guard — autotune's unique concept

Most eval systems only have one metric. autotune separates two:

**Optimize metric** — the thing you want to improve:
- lint warning count (lower is better)
- task success rate (higher is better)
- p95 latency (lower is better)

**Guard metric** — the thing that must NOT get worse:
- all tests still pass
- no new type errors
- public API behavior unchanged

This separation lets you say: **"improve X without breaking Y"** — something autoresearch and autoimprove cannot express.

### Why guards matter — a real failure scenario

**Without guard:**
```
Iteration 1: removed 5 unused imports → lint 12→7 → tests pass ✓ KEEP
Iteration 2: inlined 3 functions → lint 7→3 → tests pass ✓ KEEP
Iteration 3: deleted "redundant" error handling → lint 3→0 → tests FAIL ✗
  → but without guard, the loop KEEPS this change because lint score improved
  → deployed code now crashes on edge cases
```

**With guard (test_pass_rate >= 1.0):**
```
Iteration 3: deleted error handling → lint 3→0 → tests FAIL ✗
  → guard fails → REVERT → lint stays at 3 → safe
```

Guard metrics are the difference between "optimized" and "optimized without breaking production".

### Writing guard metrics

A guard should be:
- cheap to run (fast feedback)
- binary or threshold-based (pass/fail, not scored)
- independent of the optimize metric

```
# Good guards
guard: test_pass_rate >= 1.0
guard: type_errors == 0
guard: bundle_size_kb <= baseline * 1.1

# Bad guards
guard: "code quality is acceptable" (subjective)
guard: lint_warnings < 5 (this should be optimize, not guard)
```

---

## The 3-question test

Before finalizing an eval, ask:

1. **Could two different runs score the same output and agree?** If not, the eval is too subjective. Make it executable.
2. **Could the target game this eval without actually improving?** If yes, the eval is too narrow. Broaden it.
3. **Does this eval test something the user actually cares about?** If not, drop it. Every weak eval dilutes the signal.

---

## Common mistakes

### 1. Too many evals
More than 6 evals and the target starts gaming them — it optimizes for passing tests instead of producing good output.

**Fix:** Pick 3-6 checks that matter most.

### 2. Overlapping evals
If eval 1 is "Are tests passing?" and eval 3 is "Are there test failures?" — these are the same thing. Double-counting.

**Fix:** Each eval should test something distinct.

### 3. Unmeasurable by a script
"Would a human find this useful?" — an agent or script can't reliably answer this.

**Fix:** Translate subjective qualities into observable signals. "Useful" might mean: "Does the output contain a concrete action item?"

### 4. Eval harness changes mid-loop
Changing the benchmark to make a candidate pass is the #1 way to get fake improvements.

**Fix:** Freeze the eval for the entire loop. If the eval is wrong, restart with a new baseline.

---

## Template

### For numeric metrics (code, performance)
```
Optimize: <metric_name> <direction>
Guard: <metric_name> <operator> <threshold>
Verify: <command that prints METRIC name=value>
```

Example:
```
Optimize: lint_warnings min
Guard: test_pass_rate >= 1.0
Guard: bundle_size_kb <= 155
Verify: npm run lint 2>&1 | tail -1; npm test
```

### For binary assertions (skills, docs)
```
EVAL [N]: [Short name]
Question: [Yes/no question]
Pass: [What "yes" looks like]
Fail: [What triggers "no"]
```

Example:
```
EVAL 1: Required sections
Question: Does the doc contain Overview, Setup, and Troubleshooting sections?
Pass: All three section headers are present
Fail: Any section header is missing
```

---

## Choosing a grading method

autotune offers three grading tiers. Pick the lightest one that captures what matters.

| Tier | Tool | Reproducible | Can judge quality | Use when |
|------|------|:---:|:---:|------|
| 1. Script | `eval_gate.py`, `qa_grader.py`, etc. | Yes | No | Metrics are numeric or answers are exact strings |
| 2. Grader subagent | `agents/grader.md` | No (LLM variability) | Yes | Answer requires reading comprehension |
| 3. Human review | Dashboard + manual inspection | N/A | Yes | Subjective quality, creative output |

**Be honest about what each tier can and can't do:**

Script graders (`qa_grader.py`, `section_checker.py`, `assertion_runner.py`) are string-matching tools. They answer "Does the document contain X?" but not "Does the document explain X well enough to act on?" If your eval question requires understanding, a script grader will give you false confidence. Use the grader subagent instead.

The grader subagent introduces variability — the same document might get different verdicts on different runs. Mitigate this by requiring quoted evidence for every verdict. If the grader can't quote a passage, the answer should be FAIL.

When neither scripts nor the grader can capture what matters (visual design, writing tone, persuasiveness), don't force an automated eval. Use the dashboard for human review and make keep/revert decisions based on qualitative feedback.
