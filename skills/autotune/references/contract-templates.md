# Contract Templates

Use these templates as starting points. Keep them small and edit only what the loop needs.

## Minimal loop contract

```text
Target:
Writable scope:
Immutable:
Eval set:
Holdout:
Optimize:
Guards:
Verify:
Review mode:
Loop mode:
Autonomy:
Budget:
Decision rule:
Stop rules:
Rollback:
Log:
Dashboard:
State file:
Baseline:
Current best:
Next hypothesis:
```

## Code improvement contract

```text
Target:
- src/feature_x.py

Writable scope:
- src/feature_x.py
- tests/test_feature_x.py

Immutable:
- benchmark inputs
- lint config
- perf harness

Optimize:
- p95_latency min

Guards:
- tests_failed <= 0
- lint_errors <= 0

Verify:
- pytest tests/test_feature_x.py -q
- python3 bench/feature_x.py --sample fixed

Budget:
- 3

Rollback:
- python3 scripts/rollback.py snapshot src/feature_x.py  # before edit
- python3 scripts/rollback.py restore src/feature_x.py   # on reject or crash

Log:
- /tmp/autotune-feature-x.tsv

Baseline:
- collect before first edit
```

## Skill or prompt improvement contract

```text
Target:
- SKILL.md
- references/*

Writable scope:
- SKILL.md
- references/*

Immutable:
- benchmark prompt set
- scoring rubric
- holdout prompt set

Eval set:
- 10 to 30 realistic prompts with near-miss negatives

Holdout:
- at least 20 percent of prompts held out from tuning

Optimize:
- task_success_rate max

Guards:
- false_trigger_rate <= baseline
- avg_tokens <= baseline * 1.05

Verify:
- run fixed benchmark prompts
- score against rubric

Review mode:
- numeric + side-by-side human review on 3 representative prompts

Loop mode:
- bounded

Autonomy:
- supervised

Budget:
- 3

Decision rule:
- keep only if task_success_rate improves and guards pass; if tied, prefer the simpler draft

Stop rules:
- stop after 3 iterations
- stop early if no credible new hypothesis remains

Rollback:
- python3 scripts/rollback.py snapshot SKILL.md  # before edit
- python3 scripts/rollback.py restore SKILL.md   # on reject or crash

Log:
- /tmp/autotune-skill.tsv

Dashboard:
- /tmp/autotune-skill-dashboard.md

State file:
- /tmp/autotune-skill-state.json

Baseline:
- collect before first edit

Current best:
- baseline until a candidate beats it

Next hypothesis:
- note before each new candidate
```

## Skill self-improvement contract

```text
Target:
- SKILL.md
- references/*
- agents/openai.yaml

Writable scope:
- SKILL.md
- references/*
- agents/openai.yaml

Immutable:
- benchmark prompts
- holdout prompts
- binary pass/fail rubric

Eval set:
- 12 to 24 realistic prompts with clear positives, hard negatives, and near misses

Holdout:
- at least 20 percent held out from tuning

Optimize:
- correct_trigger_rate max

Guards:
- false_trigger_rate <= baseline
- binary_guard_pass_rate >= baseline

Verify:
- run fixed routing prompts
- score with binary yes/no grading

Review mode:
- numeric + side-by-side review on 3 representative prompts

Loop mode:
- bounded or threshold

Autonomy:
- supervised until the eval contract is proven stable

Budget:
- 3 to 5

Decision rule:
- keep only if trigger quality improves and false positives do not regress

Stop rules:
- stop on target score
- stop on max_non_improving_streak
- stop if the rubric changes

Rollback:
- python3 scripts/rollback.py snapshot SKILL.md  # before edit
- python3 scripts/rollback.py restore SKILL.md   # on reject or crash
```

## Threshold-driven continuous contract

```text
Target:
- prompts/support-pack.md

Writable scope:
- prompts/support-pack.md
- references/support-examples.md

Immutable:
- fixed eval set
- holdout eval set
- scorer

Eval set:
- 24 benchmark prompts

Holdout:
- 8 prompts held out from tuning

Optimize:
- task_success_rate max

Guards:
- hallucination_rate <= 0.02
- avg_tokens <= baseline * 1.05

Verify:
- run benchmark prompts
- run holdout prompts on retained candidates

Review mode:
- numeric only until a candidate is retained, then human review on 3 representative prompts

Loop mode:
- threshold

Autonomy:
- high-autonomy

Budget:
- unlimited until stop rules fire

Decision rule:
- keep only if optimize improves, guards pass, and scorecard improves by at least 0.01

Stop rules:
- stop when overall_score >= 0.92
- stop when holdout task_success_rate >= 0.90 and no hard guards fail
- stop on max_non_improving_streak=5
- stop on max_reject_streak=8

Rollback:
- python3 scripts/rollback.py snapshot prompts/support-pack.md  # before edit
- python3 scripts/rollback.py restore prompts/support-pack.md   # on reject or crash

Log:
- /tmp/autotune-threshold.tsv

Dashboard:
- /tmp/autotune-threshold-dashboard.md

State file:
- /tmp/autotune-threshold-state.json

Baseline:
- collect before first edit

Current best:
- baseline until replaced

Next hypothesis:
- note before each candidate
```

## Review-assisted doc contract

```text
Target:
- docs/architecture.md

Writable scope:
- docs/architecture.md

Immutable:
- fixed Q&A set
- implementation task
- scoring rubric

Eval set:
- 8 fixed questions
- 1 representative implementation task

Holdout:
- 2 questions reserved for final check

Optimize:
- implementation_task_success max

Guards:
- contradiction_count <= 0
- stale_command_count <= 0

Verify:
- answer fixed questions using the doc only
- run the representative task using the doc only

Review mode:
- numeric + side-by-side answer review

Budget:
- 3

Decision rule:
- keep only if implementation_task_success improves and both guard metrics remain at zero

Rollback:
- python3 scripts/rollback.py snapshot docs/architecture.md  # before edit
- python3 scripts/rollback.py restore docs/architecture.md   # on reject or crash

Log:
- /tmp/autotune-architecture.tsv

Dashboard:
- /tmp/autotune-architecture-dashboard.md

Baseline:
- collect before first edit

Current best:
- baseline until replaced

Next hypothesis:
- note before each new candidate
```

## Eval spec template

```json
{
  "optimize": [
    {
      "name": "task_success_rate",
      "direction": "max",
      "min_delta": 0.01
    }
  ],
  "guards": [
    {
      "name": "tests_failed",
      "kind": "absolute_max",
      "value": 0
    },
    {
      "name": "avg_tokens",
      "kind": "relative_max",
      "value": 1.05
    }
  ]
}
```

Run `python3 scripts/lint_eval_spec.py spec.json` before using it with `eval_gate.py`.
