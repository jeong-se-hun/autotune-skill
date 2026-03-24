# Autotune Session

Objective:
- [Describe the measurable improvement goal.]

Target:
- [List the exact files or artifacts to change.]

Writable scope:
- [List files or modules that may change.]

Immutable:
- [List benchmark files, fixtures, or evaluators that must not change.]

Eval set:
- [List fixed prompts, fixtures, benchmark sample, or dataset slice.]

Holdout:
- [List holdout prompts or say none with reason.]

Primary metric:
- [Name, direction, required minimum change.]

Guards:
- [List correctness or safety gates.]

Verify:
- [Benchmark and checks commands.]

Review mode:
- [numeric only | numeric + human review | blind comparison]

Loop mode:
- [bounded | threshold | continuous]

Autonomy:
- [supervised | batched-review | high-autonomy]

Budget:
- [Set the maximum iterations for this turn.]

Decision rule:
- [State the exact keep or reject rule.]

Stop rules:
- [State the exact stop conditions.]

Rollback:
- [Describe the safe rollback method for candidate-only changes.]

Log:
- [Point to the append-only experiment log path.]

Dashboard:
- [Point to the human-readable status summary path.]

State file:
- [Point to the machine-readable loop state path.]

Baseline:
- [Record the unmodified baseline before the first edit.]

Current best:
- [Record the current best result here.]

Next hypothesis:
- [Record the next candidate idea before editing.]
