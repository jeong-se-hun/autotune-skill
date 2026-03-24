# Loop Design

Use this reference when the loop contract is underspecified or when rollback safety is unclear.

## Contract checklist

- `target`: exact files or artifacts to change
- `writable_scope`: exact files that may change during the loop
- `immutable`: files, fixtures, datasets, and eval logic that must not change during the loop
- `optimize`: the metric to improve
- `guards`: conditions that must not regress
- `verify`: commands or scripts that produce the metrics
- `loop_mode`: bounded, threshold, or continuous
- `autonomy`: how much unattended execution is allowed
- `budget`: maximum iterations for this turn
- `stop_rules`: explicit conditions that end the loop
- `rollback`: how to undo only the candidate change
- `log`: where to append experiment results

Reject loops like "make it better" or "improve the docs" until they are rewritten into a measurable contract.

The strongest Karpathy pattern is narrow scope plus frozen evaluation. If the loop can freely modify both the target and the judge, the score is meaningless.
For higher-autonomy loops, add a machine-readable state file and explicit target thresholds so the loop can stop without improvising.

## Good optimize metrics

- Test pass count
- Lint error count
- Type error count
- Bundle size
- P50 or P95 latency
- Exact-match answer accuracy on a fixed set
- Task success rate on a fixed set
- Human rubric score only when the rubric is explicit and stable

## Good guards

- `tests_failed <= 0`
- `lint_errors <= 0`
- `type_errors <= 0`
- `token_cost <= baseline * 1.05`
- `runtime_seconds <= baseline * 1.10`
- `required_sections_present == 1`
- `overall_score >= 0.90`

Use at least one correctness guard when optimizing speed, size, or style.

If two candidates are effectively tied, prefer the one that removes code, narrows scope, or reduces moving parts.

## Rollback choices

Prefer this order:

1. Use `scripts/rollback.py snapshot <file>` before each candidate edit. Restore with `scripts/rollback.py restore <file>` on reject or crash. Use `scripts/rollback.py list` to inspect stored snapshots and `scripts/rollback.py clean` to remove old ones.
2. For small targeted changes, `apply_patch` reverts also work.
3. Do not rely on `git reset --hard` or broad checkout operations.

## Anti-gaming rules

- Do not tune against the same tiny example until it memorizes the benchmark.
- Keep a holdout set for skills, prompts, docs, and review rubrics.
- Separate the optimize metric from guard metrics.
- Treat missing data as a failed verification, not a pass.
- If the metric is noisy, rerun or widen the sample before keeping a change.
- Do not modify the scorer, fixtures, or benchmark set during an active loop unless the loop goal is explicitly to improve the eval itself.
- Do not let a candidate expand the writable scope without restating the contract first.
- Do not use `continuous` mode unless the stop rules are explicit and the machine log can explain every keep or reject decision.

## Suggested iteration log

```text
Iteration 1
Hypothesis:
Change:
Verify:
Candidate metrics:
Decision:
Next:
```

For a tabular log, use `log-template.tsv`.
