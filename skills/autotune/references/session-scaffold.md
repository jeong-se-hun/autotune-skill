# Session Scaffold

Use this reference when the user wants a long-running or resumable autotune loop inside a repository.

## Why session files help

Persistent repo-local files make the loop easier to resume after interruptions, compaction, or strategy changes.

Recommended split:

- tracked protocol file: durable loop objective and constraints
- machine-readable state file: current mode, streaks, and stop status
- untracked steering file: tactical direction that can change frequently
- append-only machine log: experiment history
- readable dashboard: current best result and recent decisions
- review notes: qualitative judgments that should not be mixed into machine logs
- worklog: narrative notes for larger ideas or paused branches

## Recommended repo-local files

- `autotune.md`: durable session brief
- `autotune.spec.json`: machine-readable optimize and guard spec for `eval_gate.py`
- `autotune.state.json`: machine-readable loop state
- `autotune.sh`: benchmark runner that prints metrics
- `autotune.checks.sh`: optional correctness gate
- `autotune.jsonl`: append-only machine log
- `autotune-dashboard.md`: human-readable status summary
- `autotune.ideas.md`: backlog for deferred ideas
- `experiments/worklog.md`: narrative log for larger threads
- `experiments/review-notes.md`: review notes for side-by-side baseline versus candidate checks
- `experiments/review-pack.json`: optional structured pack for rendering side-by-side review HTML with `scripts/render_review_pack.py`
- `.autotune-off`: pause sentinel

## When to use the scaffold

Use it when:

- the loop will span multiple turns or days
- the repo needs a resumable state model
- more than one operator will steer the loop
- the benchmark runner and checks should live beside the codebase
- the loop needs persistent review artifacts in addition to numeric metrics

Do not use it when a single short-lived session is enough.

## Safety rules

- Keep the benchmark protocol explicit in `autotune.md`.
- Keep formal optimize and guard thresholds in `autotune.spec.json` when the loop uses JSON-driven gates.
- Let `init_session_scaffold.py` create `autotune.jsonl` if it is missing; do not truncate that log on routine scaffold reruns.
- Keep tactical steering out of tracked files when it changes often.
- Keep machine logs append-only.
- Keep reviewer notes separate from the machine log so later analysis can distinguish hard metrics from human judgment.
- Keep mode, streak, and stop-condition state in `autotune.state.json` so the loop can resume or halt predictably.
- Do not auto-edit repository rules without user approval.
- Separate durable protocol from transient steering.

## A/B and comparative runs

For model or strategy comparisons:

- keep separate logs per run
- keep the same baseline and metric definitions
- compare only runs that share the same benchmark contract
- summarize results into a dashboard instead of mixing raw logs
