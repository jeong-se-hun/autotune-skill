---
name: autotune
description: Run metric-driven bounded, threshold, or continuous improvement loops when the user already has a fixed eval set, benchmark, review rubric, blind comparison pack, holdout set, or explicit guard metrics, or explicitly wants to build that evaluator first and then continue into tuning in the same task. Use this for measurable benchmark gains, fixed-question accuracy gains, trigger or prompt tuning against stable evals, warning cleanup under explicit guards, holdout-backed tuning, target-score stopping, or higher-autonomy keep-or-revert loops with append-only logs and explicit stop rules. For threshold or continuous requests, explicit target thresholds or machine-checkable stop rules must already exist. Do not use this for open-ended rewriting, first-pass review, debugging triage, metric discovery only, baseline-only diagnosis, or "run as long as possible" requests with no stop rule.
---

# Autotune
Use this skill to run a metric-driven optimize, verify, keep-or-revert loop inside one interactive coding workspace.
The default is still conservative, but this skill can also run in higher-autonomy modes when the user explicitly asks for it and the evaluator is stable enough to support unattended iteration.
Favor Karpathy-style research discipline:

- keep the writable scope narrow
- freeze the eval harness during a loop
- establish an unmodified baseline first
- log every experiment
- prefer simpler retained changes when gains are comparable
- keep the benchmark realistic enough that a good score means real-world improvement
## Compatibility
- Best when `python3` and the relevant verify commands are available in the current environment.
- Works well in Codex and other Agent Skills-compatible tools when a reproducible eval harness exists.
- Requires a reproducible eval harness for the active loop.
- Strongest for code, prompts, skills, docs, and runbooks where success can be measured by fixed metrics or fixed question sets.
- Works best when you can preserve comparable artifacts between baseline and candidate runs, especially for prompts, skills, docs, and policy work.
- Not a good fit for vague "just make it nicer" work with no stable evaluator.
## Quick Triage
Use this skill only when the request can be grounded in a loop contract:

- There is a measurable optimize metric.
- There is a fixed evaluator already — meaning an optimize metric, at least one guard, and a reproducible verify command are all defined — or the user explicitly wants to build it as step zero.
- There are guard metrics or hard non-regression constraints.
- When generalization matters, there is a holdout set already or the user explicitly wants one.
- The loop can explain how it will log decisions and preserve baseline versus candidate evidence.
- The user is asking to start a real optimization loop now, not only to discover the metric or capture a baseline and stop.
- If the user wants threshold, continuous, or high-autonomy operation, the loop has explicit stop rules and a machine-readable state model.
- A fixed eval alone is not enough for threshold or continuous routing. Missing target thresholds or stop rules is a hard reject, not a precondition to silently patch inside this skill.
- If the prompt says "run as long as possible", "stop when it seems better", or "just start an infinite loop" but does not define a target or stop rule, do not route to this skill yet.

If these are missing, or the user only wants metric discovery, baseline capture, or a weakness summary before deciding whether to optimize, route to review, debugging, or eval-harness setup first instead of pretending an optimization loop already exists.
## Binary Eval Rule
Prefer binary evals whenever you can.

- Ask yes/no or pass/fail questions before you reach for a vague score.
- Keep scales or scorecards for the few tradeoffs that cannot be reduced to binary checks.
- If the metric is too fuzzy to say why a candidate won, the loop is not strict enough yet.
## Use This Skill When
Use this skill whenever the user asks for work like:

- "Raise this benchmark score without breaking the tests."
- "Keep the tests green and remove the warnings."
- "Tune this prompt pack against a fixed eval set."
- "Improve this skill's trigger precision without increasing false positives."
- "Increase this runbook's accuracy against a fixed question set."
- "Run a keep-or-reject loop for three iterations against measurable criteria."
- "Tune this prompt or skill with a holdout set so it does not overfit."
- "Keep improving until the score passes 0.92 while preserving hallucination and token guards."
- "Build the evaluator first, then continue into a threshold loop."
- "Improve this operations document with fixed Q&A plus a blind comparison review pack while keeping contradiction count at zero."

## Do Not Use When
- The user wants review findings, risk discovery, or cross-AI agreement more than measurable optimization.
- The user first needs help discovering what metric matters or what the benchmark should be.
- The user only wants a baseline run, weakness summary, or current-state diagnosis and has explicitly said not to start the loop yet.
- No reproducible eval harness exists yet and building one is out of scope.
- A fixed eval exists, but a threshold or continuous request still lacks an explicit target or machine-checkable stop rule.
- The user wants "run as long as possible", "stop when it seems better", or "just start an infinite loop" with no explicit target or stop rule.
- The user is asking for broad creative rewriting with no stable pass or fail signal.

## Workflow

### 1. Establish the loop contract

Define these items before editing:

- Target files or artifacts
- Writable scope
- Immutable files and eval harness
- Eval set or benchmark sample
- Holdout set, if applicable
- Optimize metric
- Guard metrics
- Verification commands
- Review mode (`numeric only`, `numeric + human review`, or `blind comparison`)
- Loop mode (`bounded`, `threshold`, or `continuous`)
- Autonomy level (`supervised`, `batched-review`, or `high-autonomy`)
- Iteration budget
- Decision rule
- Stop rules
- Safe rollback method
- Experiment log path
- Dashboard or session summary path if the loop will span multiple turns
- State file path if the loop will span multiple turns

If any item is missing, infer conservatively or ask one short question only when guessing would be risky.

If the target is a skill, prompt, architecture doc, runbook, or policy and there is no reproducible eval yet, build the eval harness first. Read `references/eval-patterns.md`.
When building the eval from scratch:
- Draft the full contract: optimize metric, at least one guard, verify command, and at least 5 representative eval cases.
- In supervised or batched-review mode: present the drafted eval contract clearly to the user and ask for explicit confirmation before proceeding. Do not touch the target until the user confirms.
- In high-autonomy mode: log the drafted eval contract to the session notes and proceed without waiting for confirmation.
- In all modes: stop this turn after presenting or logging the contract. Treat the optimization as a fresh loop once the eval is confirmed.
If the target skill is meant for public distribution, keep the core package portable and move vendor-specific packaging to sidecar metadata. Read `references/public-publishing.md`.
If the target needs side-by-side output review, read `references/review-patterns.md` and decide what artifacts must be preserved before the first edit.
If the user wants higher autonomy or an unattended loop, read `references/autonomy-modes.md` and `references/scorecard-patterns.md` before proposing the final contract.
If the loop uses numeric metrics, validate the eval spec before editing. Use `scripts/lint_eval_spec.py` and copy a starter contract from `references/contract-templates.md`.
If the contract is still vague, use `scripts/auto_detect_contract.py` to bootstrap one from the repo tree. Present the inferred contract to the user and confirm it is correct before freezing. Then validate with `scripts/lint_contract.py`.
If the verify commands depend on an interpreter or tool alias, confirm the exact executable first and then keep that command fixed for the active loop.
If the target is a skill or prompt, use realistic prompts instead of toy one-liners. Include near-miss negatives when trigger quality matters.
If the loop will span multiple turns or days, initialize the repo-local scaffold first. Read `references/session-scaffold.md` and use `scripts/init_session_scaffold.py`.

### 2. Choose the loop mode explicitly

Pick one of these modes before editing:

- `bounded`: default and safest. Use for a short session with a fixed iteration cap.
- `threshold`: continue until an explicit metric or score target is reached, or a hard stop fires.
- `continuous`: closest to `autoresearch`. Continue iterating until `.autotune-off` appears, a hard stop fires, or the contract says to stop on target attainment.

Default to `bounded` unless the user explicitly asks for longer or unattended operation.

Only use `continuous` when:

- the verify commands are reproducible
- the optimize and guard metrics are machine-checkable
- the rollback method is safe
- the resource or cost limits are explicit
- the state files are initialized so the loop can resume cleanly

For `threshold` and `continuous` modes, define the stop rules in machine-checkable language. Prefer target metrics or a scorecard over vague prose like "until it seems good enough."

### 3. Capture a baseline

Run the first verification on the unmodified target. This baseline run is mandatory.

Run the narrowest baseline verification that measures the optimize metric and every guard.

Record the baseline in the task notes:

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

If the worktree is dirty, run `python3 scripts/rollback.py snapshot <file>` for each file you will touch before editing. Do not reset unrelated user changes.

Freeze the benchmark set, scorer, and guard thresholds for the active loop. Do not rewrite the eval harness mid-loop just to make a candidate look better.
If you must change the evaluator, declare a new loop and capture a new baseline instead of quietly carrying the old scores forward.
If you are using the scaffold, update `autotune.md`, `autotune-dashboard.md`, `autotune.state.json`, and the append-only machine log before the first candidate edit so the session can resume cleanly later.
If the verify runner prints `METRIC name=value` lines, parse them with `scripts/extract_metrics.py` instead of transcribing scores by hand.

### 4. Build a strict scorecard when one metric is not enough

When the loop needs a finer-grained notion of progress, create a scorecard in the eval spec and validate it with `scripts/lint_eval_spec.py`.

Use a scorecard when:

- multiple metrics matter and they trade off against each other
- the loop should stop at a target score
- the user wants a strict machine-readable reason for keeping, rejecting, or stopping

Use `references/scorecard-patterns.md` for templates.

When using a scorecard:

- keep hard guards separate from the scorecard
- treat score improvement as an extra keep gate, not as a substitute for correctness
- use explicit target thresholds such as `overall_score >= 0.92`
- record score deltas in the machine log and dashboard

### 5. Preserve review artifacts when metrics are incomplete
For prompts, skills, docs, policies, and other output-heavy targets, numeric metrics are often necessary but not sufficient.
Before the first candidate run:

- Decide which prompts, questions, or tasks must be preserved for side-by-side review.
- Keep baseline and candidate outputs from the same fixed inputs.
- Keep the review set small per iteration, usually 3 to 5 representative cases.
- When the review artifacts need to go back to a human, assemble them into a JSON review pack and render it with `scripts/render_review_pack.py` so baseline versus candidate evidence stays comparable.
- Record reviewer notes separately from the machine log. Use `experiments/review-notes.md` when the scaffold is active.
- Do not let human preference override hard guard failures.
- Prefer deterministic non-code graders first: `scripts/graders/qa_grader.py`, `scripts/graders/section_checker.py`, and `scripts/graders/assertion_runner.py`.
- Use `agents/grader.md` only when the grading task requires judgment that the deterministic graders cannot capture.
- Use `agents/comparator.md` when the loop needs a blind A/B choice between baseline and candidate outputs on the same fixed input.
- Use `agents/analyzer.md` after benchmark or review-pack generation when you need a compact readout of noisy assertions, tied cases, or the most credible next hypothesis.

Use `references/review-patterns.md` for review-pack structure and scoring rubrics.

### 6. Iterate

For each iteration:

1. Form one small hypothesis.
2. Make one small change.
3. Run the narrowest verification that can reject the hypothesis.
4. Compare candidate metrics to the baseline or current best result.
5. Keep the change only if the optimize metric improves and every guard passes.
6. If the gain is negligible, prefer the simpler candidate or keep the baseline.
7. Revert only the candidate change if it fails.
8. Append one row to the experiment log with the hypothesis, key metrics, a normalized decision label, and crash notes if any.
9. Update the dashboard or session brief with the latest candidate, latest decision, and current best result.
10. Update the state file with the iteration count, streaks, target status, and stop status.
11. If the loop uses human review, record a short review note that explains why the candidate was kept or rejected.
12. Record the next hypothesis.

Prefer deterministic checks over model self-grading. Use `scripts/eval_gate.py` when metrics are numeric and repeatable.
Use `scripts/lint_eval_spec.py` before the first candidate run whenever a JSON eval spec exists.
Use append-only logging. Prefer decision labels such as `keep`, `reject`, `crash`, or `reset_baseline` so later analysis is easy.
When using a holdout set, do not use holdout failures to invent prompt-by-prompt patches. Generalize from the pattern of misses instead.
If the loop is `continuous`, do not ask the user whether to continue after each candidate. Continue until a declared stop rule fires or `.autotune-off` appears.

If verification crashes, inspect only the relevant error output first. Retry only when the failure is clearly incidental, such as a typo, missing import, or malformed test fixture. After one or two obvious repair attempts, discard the hypothesis and move on.
When metrics stall, read the failure outputs, saved artifacts, or transcripts before inventing the next hypothesis. Do not optimize against aggregate scores alone if the failure mode is still unclear.
If the loop is `continuous`, periodically rewrite the dashboard and state file so the session remains resumable after interruption or compaction.

### 7. Stop

Stop when any of these is true:

- The budget is exhausted
- A declared target score or metric threshold has been reached
- No credible improving hypothesis remains
- The next verification step requires user approval or high cost
- The metric is too noisy to support a reliable keep or revert decision
- `.autotune-off` exists in the repo root for scaffolded sessions
- A hard stop rule in the state file fires, such as max reject streak or max non-improving streak

Report the best retained change, the final metrics, and any remaining uncertainty.

Use this closing structure:

```text
Best retained change:
Optimize result:
Guard results:
Holdout or review result:
Stop reason:
Iterations used:
Rejected hypotheses:
Remaining uncertainty:
```

## Session Rules

- Default to a budget of `3` iterations. Rarely exceed `5` in one turn unless the user explicitly asked for `threshold` or `continuous` mode.
- If the user explicitly asks for higher autonomy, you may switch to `threshold` or `continuous` mode, but only after writing down explicit stop rules.
- Prefer targeted tests, lint, benchmarks, or scripted scoring over broad suites until a candidate looks promising.
- Do not spawn subagents unless the user explicitly asked for delegation.
- Do not create hidden long-running loops that would repeatedly consume approvals, money, or external resources unless the user explicitly asked for high autonomy and the loop contract already covers those costs.
- Do not use destructive git commands to recover from a bad iteration. Use `scripts/rollback.py snapshot <file>` before editing and `scripts/rollback.py restore <file>` to revert. For ad-hoc cases, targeted `apply_patch` reverts also work.
- If verification depends on network, approvals, or privileged commands in the current environment, stop the loop at that boundary and ask before running them.
- When possible, keep the verify budget fixed across iterations so comparisons stay fair.
- Redirect noisy command output to a file when it would flood the context, then extract only the metrics or tail the failure.
- If a scaffolded session is active, keep `autotune.md`, `autotune-dashboard.md`, `autotune.state.json`, `autotune.jsonl`, `experiments/review-notes.md`, and `experiments/review-pack.json` coherent after every retained or rejected candidate.
- Do not silently expand the writable scope or benchmark sample mid-loop. Restate the contract first.
- In `continuous` mode, prefer one small hypothesis at a time and use explicit streak-based or threshold-based stop rules instead of intuition.

## Target-specific guidance
### Skills and prompts

- Optimize for task success rate, trigger precision, false positive rate, response length, latency, or token cost.
- Use a fixed benchmark set and keep at least one holdout case out of the tuning loop.
- Include realistic prompts with concrete context, and include near-miss negatives when trigger behavior matters.
- Reject cosmetic rewrites that do not move benchmark results.
- Treat edits to the benchmark, scorer, or examples used for grading as out of scope unless the user explicitly asked to improve the eval itself.
- Keep baseline and candidate outputs for the same prompt when the reviewer needs to judge quality that the numeric metrics do not capture.
- If trigger behavior matters, review a few near-miss negatives manually even when the aggregate numbers look good.
- If the user wants low-touch automation, batch review only on retained candidates or when the scorecard nears the target threshold.

### Architecture docs, runbooks, and policies

- Optimize for answer accuracy on fixed questions, implementation success on representative tasks, checklist coverage, or review rubric scores.
- Prefer task-grounded evaluation over stylistic preference.
- Treat unsupported claims, stale commands, and vague ownership as guard failures.
- Use a fixed question set per loop and prefer one representative task over many vague editorial judgments.
- Preserve the baseline and candidate answers to the same questions so a reviewer can see what actually changed.
- If the task includes an implementation or recovery drill, keep that task constant across the whole loop.
- Prefer `threshold` mode over `continuous` mode unless the user truly wants unattended iteration.

### Code and tests

- Optimize for the user-requested metric only after guarding correctness first.
- Use regression tests, lint, type checks, perf benchmarks, or bundle-size measurements as guards.
- Prefer one-file or one-module edits per iteration when feasible.
- If the loop is exploratory, lock a read-only boundary for config, fixtures, or the benchmark harness before editing code.
- If the loop cares about user-visible output or developer experience, save a short artifact pack in addition to raw metrics so the final comparison is explainable.
- For fully numeric code loops, human review can be omitted if guards and target thresholds are strong enough.

## Resources
- Read `references/loop-design.md` for contract design, rollback choices, and anti-gaming rules.
- Read `references/eval-patterns.md` for benchmark ideas for skills, docs, prompts, and code.
- Read `references/review-patterns.md` when the loop needs side-by-side human review in addition to numeric gates.
- Read `references/autonomy-modes.md` when choosing between bounded, threshold, and continuous loops.
- Read `references/scorecard-patterns.md` for weighted score design and target thresholds.
- Read `references/contract-templates.md` for ready-to-copy loop contracts and eval specs.
- Read `references/eval-guide.md` when the user wants to build the evaluator first.
- Read `references/target-guidance.md` for target-specific optimize and guard patterns.
- Read `references/tools-reference.md` for the helper script matrix.
- Read `references/schemas.md` for JSON format definitions (evals.json, experiments.jsonl, grading.json, trigger-eval-set.json, and all other structured files).
- Use `scripts/eval_gate.py` to make keep or reject decisions from numeric metrics.
- Use `scripts/rollback.py snapshot <file>` before each candidate edit; use `scripts/rollback.py restore <file>` if the candidate is rejected or verification crashes.
- Use `scripts/auto_detect_contract.py` to bootstrap contracts from common repo layouts.
- Use `scripts/lint_contract.py` to validate text-based contracts before the first run.
- Use `scripts/extract_metrics.py` when the verify command prints `METRIC` lines.
- Use `scripts/render_review_pack.py` to turn a baseline-versus-candidate review pack into a static HTML artifact for human review.
- Use `scripts/lint_eval_spec.py` to reject malformed or self-contradicting eval specs before the loop starts.
- Use `scripts/validate_log.py` and `scripts/resume_session.py` when continuing from an experiments log.
- Use `scripts/generate_dashboard.py` to turn an experiments log into an HTML dashboard.
- Use `scripts/self_test.py` to smoke test the bundled scripts before publishing or after edits.
- Use `scripts/run_fixture_tests.py` to execute the bundled code, skill, and docs fixtures end to end.
- Use `scripts/init_session_scaffold.py` when the user wants a repo-local long-running autotune session with persistent state files.
- Inspect `assets/fixtures/` for executable sample contracts and metrics.
- Inspect `assets/templates/experiments-review-pack.json` when you want a starter shape for manual side-by-side review.
- Inspect `references/session-scaffold.md` before creating persistent repo-local autotune files.
- Read `references/public-publishing.md` for public package scope, release checklist, and portability rules.
- Inspect `evals/evals.json` when you want concrete routing examples for public packaging or trigger review.
- Inspect `evals/trigger-eval-set.json` when you want a trigger-only benchmark that is simpler than the richer routing set.
- Use `references/log-template.tsv` as an append-only ledger and keep decision labels stable across the loop.
- Read `agents/comparator.md` when a blind pairwise judgment is the cleanest way to resolve a review-heavy tie.
- Read `agents/analyzer.md` when you need post-run synthesis instead of raw benchmark dumps.
- Run `scripts/self_check.py` before publishing or sharing the package outside the local environment.
