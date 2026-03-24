# Live Trigger Benchmark

Use this reference when proxy routing coverage is not enough and you want to verify whether a real agent CLI actually consults the skill on holdout prompts.

## Why this matters

Pattern coverage in `SKILL.md` and metadata is useful, but it is still a proxy.

A stricter check is:

- keep a holdout routing split
- run the real agent CLI on those prompts
- detect whether it consulted the skill
- compare observed trigger behavior against the expected labels

## Codex benchmark

Use `scripts/run_codex_trigger_benchmark.py`.

It currently:

- selects `routing.split == "holdout"` prompts from `evals/evals.json`
- runs `codex exec --json` in read-only mode
- asks Codex for a single structured JSON routing decision without executing commands
- marks a case as triggered when the run reads `SKILL.md` or returns `{"skill_used":"autotune", ...}`
- supports a one-time longer retry timeout so infrastructure stalls do not get mixed into routing misses

This is intentionally stricter than the keyword proxy but still cheap enough to rerun during tuning.

## Interpreting the report

The script reports:

- `accuracy`
- `precision`
- `recall`
- `specificity`
- `completion_rate`
- `balanced_accuracy`
- `live_trigger_score`

Final timeouts are treated as `inconclusive`, not as silent true negatives or false negatives.

`live_trigger_score` is the strict gate. It is the minimum of `accuracy`, `precision`, `recall`, `specificity`, and `completion_rate`, so a false positive, false negative, or unresolved timeout lowers it.

## Practical rules

- Keep the live benchmark on holdout prompts, not the train split.
- Keep the prompts realistic and slightly ambiguous.
- Do not "teach to the benchmark" by stuffing literal phrases from a single missed prompt into the description.
- If the live benchmark and the proxy benchmark disagree, trust the live benchmark first and then inspect the mismatch.
- Treat final timeouts as infrastructure noise first. Retry them once with a longer timeout before you classify them as routing failures.
