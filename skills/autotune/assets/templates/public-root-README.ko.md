# autotune

[English README](README.md)

`autotune`는 코드, 프롬프트, 문서, 스킬, 테스트처럼 **측정 가능한 대상**을 고정된 평가 기준으로 반복 개선하기 위한 공개 Agent Skill입니다.

이 스킬의 목적은 단순한 “한 번 수정”이 아니라, 아래 같은 상황에서 일관된 개선 루프를 실행하도록 돕는 것입니다.

- 고정 benchmark 점수를 올려야 할 때
- 질문셋 기반 문서 정확도를 개선해야 할 때
- 경고 수를 줄이되 테스트와 guard를 깨면 안 될 때
- 스킬이나 프롬프트를 holdout 포함 eval 세트로 튜닝해야 할 때
- threshold 또는 continuous loop를 쓰되, stop rule과 상태 기록을 엄격하게 관리해야 할 때

## 왜 이 스킬이 있나

대부분의 자동 개선 요청은 다음 둘 중 하나에서 실패합니다.

- 평가 기준이 불안정해서 “좋아진 것처럼 보이는” 변경만 누적됨
- baseline, guard, holdout, stop rule 없이 루프만 돌다가 과적합되거나 회귀가 생김

`autotune`는 이 문제를 막기 위해 만들어졌습니다.  
핵심 철학은 다음과 같습니다.

- eval을 먼저 고정한다
- baseline을 반드시 남긴다
- 작은 가설 하나씩 검증한다
- improve-or-reject를 명확히 기록한다
- stop rule이 없으면 고자율 루프를 시작하지 않는다

## 무엇에 특화돼 있나

`autotune`는 특히 아래 유형에 강합니다.

- benchmark가 이미 있는 코드 최적화
- fixed Q&A나 assertion 세트가 있는 문서/정책/runbook 개선
- holdout이 있는 프롬프트/스킬 라우팅 튜닝
- warning cleanup, token guard, contradiction guard 같은 명시적 guard가 있는 정리 작업
- review pack, scorecard, blind comparison이 필요한 반복 개선 작업

반대로 아래는 기본 대상이 아닙니다.

- 그냥 더 읽기 좋게 다듬기
- debugging/원인 분석이 먼저인 작업
- metric discovery만 하고 끝나는 작업
- baseline만 찍고 약점만 정리하는 작업
- stop rule 없이 “계속 돌려보자” 하는 continuous 요청

## 설계 방향

이 저장소의 공개 버전은 두 가지 영향을 강하게 받았습니다.

- Anthropic의 [`skill-creator`](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
  - 평가, 비교, 반복 개선, trigger 품질 측정을 중시하는 방향
- Karpathy의 [`autoresearch`](https://github.com/karpathy/autoresearch)
  - baseline, 실험 규율, 작은 가설, 로그 중심 루프를 중시하는 방향

`autotune`는 이 둘을 그대로 복제하려는 것이 아니라, **측정 가능한 개선 루프**에 맞게 더 좁고 엄격한 패턴으로 정리한 스킬입니다.

## 주요 특징

- bounded, threshold, continuous loop를 모두 지원
- optimize metric, guard metric, holdout, stop rule을 명시적으로 요구
- append-only log와 session scaffold 제공
- scorecard, blind comparison, analyzer/grader/comparator 흐름 지원
- Codex 기준 live trigger benchmark와 공개용 self-check 포함
- 공개 배포를 위한 portable repo 구조 지원

## 설치

### skills.sh

```bash
npx skills add __REPO_SLUG__ --skill autotune
```

### Codex

`skills/autotune` 디렉터리를 Codex가 읽는 skills 경로에 배치하면 됩니다.

- project: `.agents/skills/autotune`
- user: Codex가 인식하는 사용자 skills 디렉터리

### Claude Code, Gemini CLI, 그 외 skills 호환 도구

`skills/autotune` 폴더를 각 도구의 표준 skills 위치에 복사해서 사용하면 됩니다.

## 저장소 구조

```text
repo-root/
├── README.md
├── README.ko.md
├── .gitignore
├── LICENSE
├── skills/
│   └── autotune/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       ├── scripts/
│       ├── references/
│       ├── assets/
│       └── evals/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
```

## 검증

공개 repo 루트에서:

```bash
python3 skills/autotune/scripts/public_release_check.py .
```

스킬 품질 검증에는 다음이 포함됩니다.

- self-check
- fixture test
- routing contract 검사
- Codex live trigger benchmark
- quality score 계산

## 공개용 참고

- portable skill 본체는 `skills/autotune/` 아래에 있습니다
- `.claude-plugin/`은 선택적 Claude Code wrapper입니다
- skills.sh 사용자는 `.claude-plugin/`을 신경 쓸 필요가 없습니다
