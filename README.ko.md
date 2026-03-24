# autotune

[English README](README.md)

**감으로 개선하지 마세요. 측정으로 개선하세요.**

`autotune`은 프롬프트, 스킬, 문서, 코드, 테스트를 대상으로 **측정 기반 keep-or-reject 개선 루프**를 실행하는 Agent Skill입니다. guard 메트릭, 롤백 안전장치, 명시적 stop rule을 갖추고 있습니다.

- **고정 benchmark**를 기준으로 한 측정된 개선
- **Guard 메트릭** — optimize가 개선돼도 guard가 실패하면 채택하지 않음
- **롤백 안전장치** — 후보가 실패하면 즉시 되돌림
- **명시적 stop rule** — bounded, threshold, continuous 모두 지원
- **하나의 워크플로우** — 프롬프트, 스킬, 문서, 코드 전부

---

## 실제 세션이 어떻게 생겼나

> 감으로 판단하지 않습니다. "왠지 더 좋아 보여"는 없습니다.
> 가설 하나, 변경 하나, 검증 한 단계씩.

```
Baseline:        lint_warnings=18, tests_failed=0
────────────────────────────────────────────────
Iter 1  unused import 제거              18 → 12   KEEP
Iter 2  불필요한 wrapper 인라인화       12 →  9   KEEP
Iter 3  과도한 인라인화 시도             9 →  9   REJECT  (변화 없음)
Iter 4  반복 표현 추출                   9 →  7   KEEP
────────────────────────────────────────────────
결과:  lint_warnings=7 (↓61%), tests_failed=0 (guard 유지)
종료:  budget 소진 (채택 3회 / 반려 1회)
```

`baseline → 제안 → 검증 → keep 또는 revert`

optimize 메트릭이 개선되더라도 guard가 실패하면 변경을 채택하지 않습니다.

---

## 가장 잘 맞는 세 가지

### 1. 프롬프트 및 스킬 튜닝
고정 eval 세트와 holdout split을 기준으로 trigger 정확도, 작업 성공률, 출력 품질을 튜닝합니다. benchmark 점수를 움직이지 않는 cosmetic 수정은 자동으로 반려됩니다.

### 2. 문서, runbook, 정책
고정 질문셋 기반 답변 정확도를 올리면서 contradiction 수와 stale command 수를 0으로 유지합니다. 각 후보는 baseline과 동일한 고정 질문으로 비교됩니다.

### 3. 코드 최적화
lint 경고, 번들 크기, latency, 메모리를 줄이면서 테스트와 타입 체크를 유지합니다. 한 번에 파일 하나씩, 스냅샷으로 안전하게 롤백합니다.

---

## 사용 예시

> **eval이 준비됐다 = 세 가지가 정해진 상태: 무엇을 개선할지(optimize), 무엇이 깨지면 안 되는지(guard), 어떻게 측정할지(verify command).** 셋이 모두 있으면 바로 루프 시작. 없으면 먼저 초안을 잡습니다.

### eval이 없어도 됩니다 — 목표를 말하면 autotune이 eval 초안을 먼저 만들어 줍니다

시작 전에 eval을 준비할 필요가 없습니다. 개선할 내용과 지켜야 할 조건을 말하면 됩니다:

> "이 프롬프트를 개선하고 싶어. eval은 없어. 엣지 케이스 처리가 더 잘 돼야 하고, 토큰 비용은 올라가면 안 돼."

autotune이 eval 초안을 만들어 줍니다 — 고정 질문셋, guard 조건, 검증 커맨드까지. supervised 모드에서는 초안을 제시하고 확인 후 루프를 시작합니다. high-autonomy 모드에서는 초안을 로그에 남기고 바로 진행합니다. eval 구성은 step 0이고, 따로 준비할 사전 조건이 아닙니다.

### bounded — 짧은 세션, 고정 budget (기본값)

> "`src/api.py`에서 lint 경고를 줄여줘. 3번 반복. 테스트는 유지해야 해."

3번 반복합니다. 각 후보는 `lint_warnings`를 줄이고 `tests_failed=0`을 유지해야 합니다. 편집 전 스냅샷을 찍고, 반려되거나 크래시가 나면 자동으로 복원됩니다.

### threshold — 목표 점수에 도달할 때까지 실행

> "이 runbook의 Q&A 정확도를 90% 이상으로 올려줘. contradiction_count가 0을 넘으면 멈춰."

`answer_accuracy >= 0.90`에 도달할 때까지 실행합니다. contradiction이 발생하면 정확도가 올라도 반려합니다. 시작 전에 명시적 목표값이 있어야 합니다.

### continuous — 명시적 stop rule이 있는 무인 루프

> "high-autonomy 모드로 이 스킬의 trigger precision을 튜닝해줘. 연속 3번 반려되거나 false_positive_rate가 0.05를 넘으면 멈춰. `.autotune-off` 파일로 언제든 중단 가능."

선언된 stop rule이 발동할 때까지 실행합니다. 매 반복마다 가설, 결정, 메트릭 값을 append-only 실험 로그에 기록합니다.

---

## 이 스킬을 쓰면 안 될 때

- 최적화가 아니라 피드백, 위험 발견, cross-review가 목적 → 리뷰 스킬을 쓰세요
- 현재 상태나 약점 파악만 하고 싶을 때 → baseline만 먼저 찍고 판단하세요
- "그냥 더 읽기 좋게"처럼 안정적인 pass/fail 신호가 없는 요청
- "적당히 좋아지면 멈춰"처럼 목표 점수나 stop rule이 없는 연속 루프 요청
- 아직 metric 정의 전, 원인 분석이나 디버깅이 먼저인 상황

---

## 설치

### skills.sh

```bash
npx skills add jeong-se-hun/autotune-skill --skill autotune
```

### Codex

`skills/autotune`을 Codex가 인식하는 Agent Skills 경로에 복사하거나 링크합니다:

- project: `.agents/skills/autotune`
- user: Codex 사용자 skills 디렉터리

### Claude Code, Gemini CLI, 그 외 skills 호환 도구

`skills/autotune` 폴더를 각 도구의 표준 skills 위치에 복사해서 사용합니다.

---

## 작동 방식

**루프 모드**

| 모드 | 사용 시점 |
|------|-----------|
| `bounded` | 짧은 세션, 고정 반복 횟수 (기본값) |
| `threshold` | 목표 점수에 도달할 때까지 실행 |
| `continuous` | 명시적 stop rule이 있는 무인 루프 |

**자율 수준**: `supervised` → `batched-review` → `high-autonomy`

모든 루프에 필요한 것: optimize 메트릭, 최소 한 개의 guard 메트릭, 검증 커맨드, threshold/continuous 모드일 경우 명시적 stop rule.

---

## 설계 방향

- Karpathy의 [`autoresearch`](https://github.com/karpathy/autoresearch) — baseline 규율, 작은 가설, 실험 엄격성. autoresearch는 GPU 연구 루프가 대상이고, autotune은 프롬프트/스킬/문서/코드를 eval guard와 롤백 안전장치로 다룹니다.
- Anthropic의 [`skill-creator`](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) — eval 우선 반복, trigger 품질, holdout 규율.

---

## 저장소 구조

```
repo-root/
├── README.md
├── README.ko.md
├── skills/
│   └── autotune/
│       ├── SKILL.md
│       ├── agents/
│       ├── scripts/       스크립트 20개 + grader 3개
│       ├── references/    레퍼런스 문서 14개
│       ├── assets/        템플릿 + fixture
│       └── evals/
└── .claude-plugin/        선택적 Claude marketplace wrapper
```

## 패키지 검증

스킬 소스 디렉터리에서:

```bash
python3 skills/autotune/scripts/self_check.py
python3 skills/autotune/scripts/self_test.py
```

export된 공개 repo 루트에서 (`export_public_repo.py` 실행 후):

```bash
python3 skills/autotune/scripts/public_release_check.py .
```
