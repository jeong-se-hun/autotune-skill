# Review Patterns

Use this reference when numeric metrics are necessary but not sufficient.

## When to use review packs

Use a review pack when:

- the target is a skill, prompt, doc, policy, or UI-heavy code path
- the optimize metric is real but incomplete
- you need to compare baseline versus candidate outputs on the same fixed inputs

Do not replace hard guards with vibes. Human review complements the loop; it does not waive correctness failures.

## Review-pack contents

Keep the pack small per iteration, usually 3 to 5 representative cases.

For each case, preserve:

- input prompt or task
- baseline output
- candidate output
- key metrics for that case
- short reviewer note
- final keep or reject reason

If the pack will go back to a human, store it as JSON and render it with `scripts/render_review_pack.py` so the same cases can be reviewed consistently across iterations.

If the session scaffold is active, record the notes in `experiments/review-notes.md` and keep the machine-readable decision in `autotune.jsonl`.
If the loop is high-autonomy, batch review on retained candidates or when the score nears the stop threshold instead of reviewing every rejection.

## Review workflow

1. Pick representative cases before editing.
2. Keep the exact same cases for baseline and candidate.
3. Review them after metrics are available.
4. Record what changed, not just whether the candidate felt better.
5. Generalize from repeated patterns before inventing the next hypothesis.
6. If multiple cases or metrics are involved, ask `agents/analyzer.md` for a short benchmark-analysis note instead of relying on raw dumps alone.

## Blind comparison

Use blind comparison when:

- the operator wants a cleaner A/B decision
- the same input was preserved for both sides
- the numeric metrics are tied or incomplete

For this mode, hand the paired outputs to `agents/comparator.md` and keep the comparator blind to which side is baseline versus candidate.

## Suggested rubrics

### Skills and prompts

- task completion
- trigger quality
- format adherence
- wasted motion
- token cost or latency tradeoff

### Docs and runbooks

- answer correctness
- missing prerequisites
- stale commands
- contradiction count
- implementation usefulness

### Code with user-visible output

- correctness
- regressions
- output quality
- operator ergonomics
- performance cost of the change

## Anti-overfitting rules

- Keep at least one holdout case outside the tuning loop.
- Do not rewrite the rubric mid-loop to rescue a candidate.
- Do not let a favorite example dominate the decision.
- If baseline and candidate are effectively tied, prefer the simpler retained state.
