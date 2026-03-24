# Eval Patterns

Use this reference when the target is not traditional code and the metric design is the hard part.

For targets where quality is partly qualitative, pair the metrics below with a small review pack. Read `references/review-patterns.md`.
For higher-autonomy loops, pair the metrics below with explicit stop thresholds or a scorecard. Read `references/scorecard-patterns.md`.

## Binary evals first

Prefer yes/no checks before scales.

- Binary checks are easier to keep stable across runs.
- Binary checks make keep-or-reject decisions easier to explain.
- Use scales or weighted scorecards only when multiple non-binary tradeoffs really matter.

## Skills

Benchmark with 10 to 30 realistic prompts.

Do not benchmark only with short obvious positives. Include:

- normal requests
- hard but valid requests
- near-miss negatives that mention adjacent concepts
- ambiguous requests where trigger behavior matters

Track:

- Task success rate
- Correct trigger rate
- False trigger rate
- Output length or token cost
- Time to first useful action

Hold out at least 20 percent of prompts from the tuning loop.

Keep the grader stable for the whole loop. If you change the rubric, reset the baseline.
When trigger quality matters, keep false-positive prompts in both train and holdout splits so the loop does not overfit to easy positives.
Keep baseline and candidate outputs for a few representative prompts so a reviewer can inspect what the numbers hide.

## Prompts and policies

Benchmark with paired prompts:

- Normal requests
- Edge cases
- Refusal cases
- Ambiguous requests

Track:

- Correct acceptance rate
- Correct refusal rate
- Hallucination count
- Average latency or token cost

Keep refusal and edge-case prompts in the holdout set so the loop does not optimize only for easy accepts.
Use realistic user phrasing with context, filenames, or backstory when possible so benchmark wins transfer to real use.
For prompts with subjective quality components, preserve baseline and candidate outputs for the same prompt and review them side by side.

## Architecture docs and runbooks

Benchmark with fixed tasks and questions:

- "Implement change X using the doc only"
- "Answer ownership and dependency questions"
- "Recover from incident Y using the runbook only"

Track:

- Question-answer accuracy
- Task completion rate
- Missing prerequisite count
- Contradiction count
- Stale command count

Prefer scoring answers from fixed questions plus one execution-grounded task over free-form editorial feedback.
Keep the same questions and task across the whole loop, and preserve baseline versus candidate answers for reviewer inspection.

## Code

Common optimize metrics:

- Smaller bundle size
- Lower latency
- Lower memory use
- Fewer warnings

Common guards:

- All relevant tests pass
- No new lint or type failures
- Public behavior remains unchanged

When possible, benchmark the same input sample or workload size on every iteration.
If the code loop changes user-visible output, archive a tiny artifact pack alongside the metrics so the final decision remains explainable.
For unattended loops, define metric thresholds that cause the loop to stop without a human vote.

## Example contracts

### Skill tuning

```text
Target: SKILL.md, references/*
Optimize: task_success_rate max
Guards: false_trigger_rate <= baseline, avg_tokens <= baseline * 1.05
Verify: run benchmark prompts and score outputs
Budget: 3
Rollback: python3 scripts/rollback.py snapshot <file>  # before edit; restore <file> on reject
```

### Architecture doc refinement

```text
Target: docs/architecture.md
Optimize: implementation_task_success max
Guards: contradiction_count <= 0, stale_command_count <= 0
Verify: run fixed Q&A plus one representative implementation task
Budget: 3
Rollback: python3 scripts/rollback.py snapshot <file>  # before edit; restore <file> on reject
```

## Fixed-budget guidance

Karpathy's original loop uses a fixed 5-minute run so results are directly comparable. Recreate that idea whenever possible:

- use the same benchmark sample size every iteration
- keep timeout and resource limits fixed
- compare against the same baseline until you intentionally restart the loop
- if you restart the evaluator, mark that as a new baseline instead of mixing old and new scores in one table
