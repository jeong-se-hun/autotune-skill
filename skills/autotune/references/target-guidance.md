# Target-Specific Guidance

Read this when you need domain-specific advice for setting up a contract. Each section shows common patterns, good metrics, and a starter contract.

## Code

Common pattern: "테스트 유지하고 warning 줄여줘" or "번들 사이즈 줄여줘"

- Optimize: lint count, bundle size, latency, memory, warning count
- Guard: test pass rate, type check, public API unchanged
- Prefer one-file or one-module edits per iteration
- Lock a read-only boundary for config, fixtures, or the benchmark harness

```text
Target: src/utils.ts
Optimize: lint_warnings min
Guards: test_pass_rate >= 1.0, type_errors == 0
Verify: npm run lint && npm test
Budget: 3
```

## Documents and architecture docs

Common pattern: "이 문서 정확도 올려줘" or "아키텍처 문서 개선해줘"

- Optimize: Q&A accuracy on fixed questions, task completion rate, checklist coverage
- Guard: no contradictions, no stale commands, existing structure preserved
- Use task-grounded evaluation: "Can someone implement feature X using only this doc?"
- Prefer one representative task over many vague editorial judgments
- For non-code grading, use `scripts/graders/qa_grader.py` or spawn a grader subagent — see `agents/grader.md`

```text
Target: docs/architecture.md
Optimize: qa_accuracy max (5 fixed questions)
Guards: contradiction_count == 0, stale_command_count == 0
Verify: python3 scripts/graders/qa_grader.py qa_set.json docs/architecture.md
Budget: 3
```

## Ideas and proposals

Common pattern: "이 제안서 더 설득력 있게" or "기획안 반복 다듬기"

- Optimize: acceptance criteria coverage, specificity score, actionability
- Guard: scope boundaries intact, budget constraints preserved, no scope creep
- Eval with binary assertions: "Does each claim have supporting evidence?"
- Use `scripts/graders/assertion_runner.py` for executable assertion checklists

```text
Target: proposal.md
Optimize: criteria_coverage max (8 binary checks)
Guards: word_count <= 2000, scope_items unchanged
Verify: python3 scripts/graders/assertion_runner.py assertions.json proposal.md
Budget: 3
```

## Skills and prompts

Common pattern: "스킬 trigger 정확도 올려줘" or "프롬프트 정확도 개선"

- Optimize: task success rate, trigger precision, false positive rate
- Guard: false positive rate, token cost, response length
- Use a fixed benchmark set with at least one holdout case
- Include realistic prompts with context, and near-miss negatives

```text
Target: SKILL.md + references/*
Optimize: task_success_rate max
Guards: false_trigger_rate <= baseline, avg_tokens <= baseline * 1.05
Verify: run benchmark prompts and score outputs
Budget: 3
```

## Runbooks and policies

Common pattern: "이 runbook 정확도 올려줘" or "온콜 가이드 개선"

- Optimize: recovery success rate, step completeness, answer accuracy
- Guard: no missing prerequisites, no unsafe commands
- Test with: "Can someone recover from incident Y using only this runbook?"

```text
Target: runbooks/incident-response.md
Optimize: recovery_success_rate max
Guards: missing_prereq_count == 0, unsafe_command_count == 0
Verify: simulated incident recovery + fixed Q&A
Budget: 3
```
