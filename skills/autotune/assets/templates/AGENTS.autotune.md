<!-- autotune:start -->
## Autotune session rules
When `autotune.md` exists at the repository root and `.autotune-off` does not exist there:
- Read `autotune.md`, `autotune.jsonl`, `autotune-dashboard.md`, `autotune.ideas.md`, `experiments/worklog.md`, and `experiments/review-notes.md` if present before proposing the next experiment.
- If `Baseline:` or `Current best:` are missing in `autotune.md`, establish or refresh them before candidate edits.
- If `autotune.state.json` exists, read it before proposing the next experiment.
- Treat new user messages as steering for the next experiment unless the user explicitly asks to pause or stop.
- Finish logging the current experiment before changing direction.
- Update the machine log, dashboard, state file, and review notes after each candidate decision.
- Keep the benchmark contract stable unless the user explicitly asks to improve the eval itself.
- Prefer one candidate hypothesis at a time unless the user explicitly asks for a wider batch.
- If `Loop mode:` is `continuous` or `threshold`, do not ask whether to continue after each candidate. Stop only when the declared stop rules fire, `.autotune-off` exists, or the user redirects the session.

When `.autotune-off` exists at the repository root:
- Do not resume autotune automatically.
<!-- autotune:end -->
