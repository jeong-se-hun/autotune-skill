# Scorecard Patterns

Use this reference when a single optimize metric is too coarse.

## Why scorecards help

Some loops have one headline optimize metric but still need a stricter machine-readable notion of progress.

Examples:

- prompt quality versus token cost
- skill success rate versus false positives
- doc usefulness versus contradiction count
- latency gains versus memory regressions

Use hard guards for non-negotiables. Use the scorecard for tradeoffs among metrics that can vary together.

## Eval spec shape

```json
{
  "optimize": [
    {"name": "task_success_rate", "direction": "max", "min_delta": 0.01}
  ],
  "guards": [
    {"name": "false_trigger_rate", "kind": "absolute_max", "value": 0.05}
  ],
  "scorecard": {
    "metrics": [
      {"name": "task_success_rate", "weight": 0.6, "best": 1.0, "worst": 0.0},
      {"name": "false_trigger_rate", "weight": 0.25, "best": 0.0, "worst": 0.2},
      {"name": "avg_tokens", "weight": 0.15, "best": 2500, "worst": 6000}
    ],
    "keep_if_score_improves_by": 0.01,
    "stop_if_score_at_least": 0.92
  },
  "targets": [
    {"name": "task_success_rate", "kind": "at_least", "value": 0.90},
    {"name": "overall_score", "kind": "at_least", "value": 0.92}
  ]
}
```

## Design rules

- Keep guards and scorecard metrics conceptually separate.
- Use scorecards for tradeoffs, not for hiding correctness regressions.
- Pick `best` and `worst` anchors that reflect meaningful operating bounds, not fantasy values.
- Prefer a small number of scorecard metrics, usually 3 to 5.
- Add a stop threshold only when the user genuinely wants target-driven iteration.

## Interpretation

- `optimize` still decides whether the candidate improved on the headline goal.
- `guards` still block regressions.
- `scorecard.keep_if_score_improves_by` adds a stricter composite improvement gate.
- `targets` and `scorecard.stop_if_score_at_least` tell the loop when it may stop.
