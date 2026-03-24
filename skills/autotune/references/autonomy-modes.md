# Autonomy Modes

Use this reference when the user wants more or less automation from the loop.

## Mode summary

### `bounded`

Use when:

- the user wants a short, controlled session
- the loop is exploratory
- human steering is still important

Default shape:

- 3 to 5 iterations
- baseline first
- explicit closeout at the end of the turn

### `threshold`

Use when:

- the user wants the loop to continue until a target score or metric is reached
- the evaluator is stable
- the stop condition can be expressed numerically

Default shape:

- no fixed iteration cap required
- stop on target attainment, hard stop, or obvious stagnation
- best for "improve until score X" requests

### `continuous`

Use when:

- the user explicitly wants unattended or overnight operation
- the loop is fully machine-checkable
- cost, runtime, and rollback are already defined

Default shape:

- continue until `.autotune-off` exists, a declared stop rule fires, or the contract says to stop on target attainment
- do not ask "should I continue?" after each candidate

## Autonomy ladder

- `supervised`: ask or report at natural checkpoints; best for qualitative targets
- `batched-review`: run multiple numeric iterations, then request one human review pass
- `high-autonomy`: numeric keep or reject plus explicit stop rules; human review only on retained candidates or final output

## Hard stop suggestions

- target score reached
- max reject streak reached
- max non-improving streak reached
- evaluator becomes noisy or invalid
- required approvals or external dependencies appear
- `.autotune-off` pause sentinel exists

## Safety rule

Do not use `continuous` mode unless the loop contract can answer all of these:

- What is the evaluator?
- What are the hard guards?
- What is the rollback method?
- What ends the loop?
- Where is the state written?
