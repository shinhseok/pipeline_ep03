---
name: feedback-walkthrough
version: 1.0
description: >
  피드백 루프의 실제 작동 예시.
  하나의 에피소드(EP03/run001)에서 피드백이 발생하고 해결되는 전 과정을 시뮬레이션한다.
---

# Feedback Loop Walkthrough — 실제 작동 예시

## 시나리오

- PROJECT_CODE: EP03
- RUN_ID: run001
- 주제: 산업혁명과 AI
- 현재 단계: STEP 05 + 06 병렬 실행 완료 → MERGE 진입

---

## 1단계: visual-director가 SECTION02 처리 중 이슈 감지

visual-director가 shot24를 처리하면서 두 가지 문제를 발견한다.

**문제 A**: shot24의 `[공간]`에 L3 밀도 등급이 지정되어 있지만, 구조물 서술이 없다.

```yaml
# 04_shot_composition/run001/SECTION02/shot24.md (shot-composer 산출물)
creative_intent: |
  [공간] L3. 실내.
  [소품] 커다란 톱니바퀴가 천장에서 내려온다.
  [카메라] VAST. XWS, 로우앵글. 캐릭터 8%. 발견경로: 하강.
  [조명] 역광, 차가운 색온도.
  [감정선] 기계에 압도되는 순간.
  [이전샷] Scale Shock — 앞 shot(캐릭터 클로즈업) → 이번 shot(거대 기계).
```

→ visual-director의 판단: L3인데 "실내"만 있고 구조물(기둥, 벽, 천장 구조 등)이 없다.
→ 워크어라운드: narration_span("공장의 기계가 쉬지 않고 돌아갑니다")과 emotion_tag(TENSION)을 참고하여 flow_prompt P2에 "어두운 공장 내부, 높은 천장의 철골 구조물이 희미하게 보이는" 배경을 자체 생성.

**문제 B**: shot27의 creative_intent에 "그림자 실루엣"이 언급되지만 has_human 필드가 없다.

→ visual-director의 판단: anonym으로 판정해야 하는데, creative_intent만으로는 "소품의 그림자"인지 "사람의 실루엣"인지 모호하다.
→ 워크어라운드: narration_span("아이들이 공장으로 걸어갑니다")을 참고하여 has_human: anonym 판정.

### 피드백 파일 생성

```yaml
# feedback/run001/visual-director_SECTION02_20260327T1430.md

---
from: visual-director
to: shot-composer
run_id: run001
section: SECTION02
created: 2026-03-27T14:30:00+09:00
feedback_count: 2

items:
  - id: FB-001
    severity: FLAG
    shot_id: 24
    field: creative_intent
    symptom: |
      [공간] L3 등급이 지정되었으나 구조물 서술이 "실내"만 존재.
      flow_prompt P2에서 L3에 맞는 배경 요소를 작성할 근거 부족.
    root_cause: |
      추정: shot-composer가 밀도 등급을 L3으로 지정할 때
      [공간] 태그에 구조물 힌트를 구체적으로 기술하지 않은 것으로 보임.
    suggestion: |
      shot24의 [공간]을 다음과 같이 보강:
      "[공간] L3. 실내 — 높은 천장의 공장 내부. 철골 기둥과 들보가 상단에 보이되,
      캐릭터 선보다 연하고 가늘게. 구조물 외의 빈 공간은 순백."
    workaround: |
      narration_span("공장의 기계가 쉬지 않고 돌아갑니다")과 emotion_tag(TENSION)을
      참고하여 flow_prompt P2에 "어두운 공장 내부, 높은 천장의 철골 구조물이 희미하게
      보이는" 배경을 자체 생성. 채색은 원래 계획대로 소품(톱니바퀴)에만 적용.

  - id: FB-002
    severity: FLAG
    shot_id: 27
    field: creative_intent
    symptom: |
      "그림자 실루엣"이 creative_intent에 언급되나, has_human 판정 근거 모호.
      소품의 그림자인지 사람의 실루엣인지 구분 불가.
    root_cause: |
      추정: creative_intent [감정선]에 "실루엣이 늘어난다"로만 기술되어 있어
      인물 여부를 명확히 판단할 수 없음.
    suggestion: |
      shot27의 [감정선]에 주체를 명시:
      "아이들의 실루엣이 공장 벽에 길게 늘어진다" 또는
      "기계의 그림자가 바닥에 길게 드리워진다".
    workaround: |
      narration_span("아이들이 공장으로 걸어갑니다")을 참고하여
      has_human: anonym으로 판정. ref_images에 character_reference.jpeg 포함.
---
```

### Section Completion Report

```
[SECTION02 비주얼 디렉팅 완료]
저장: 05_visual_direction/run001/SECTION02/ — 13개 파일 (delta, v3)
Shot 수: 13개 | FLOW_MODEL: NB2
Upstream feedback: 2건 (BLOCK 0 / FLAG 2 / NOTE 0) → feedback/run001/ 기록
```

---

## 2단계: audio-director가 전체 처리 중 이슈 감지

audio-director가 SECTION01의 shot15를 처리하면서 한 가지 문제를 발견한다.

**문제**: shot15의 emotion_tag이 HUMOR인데 narration_span이 1문장이다.
HUMOR tension-build 규칙(§3)에 의하면 2문장 이상이어야 setup→punch 구조가 가능하다.

→ 워크어라운드: 1문장이므로 [SERIOUS TONE] 단일 태그를 적용 (규칙대로).
   하지만 원래 의도한 유머 효과가 감소할 수 있으므로 NOTE로 기록.

```yaml
# feedback/run001/audio-director_ALL_20260327T1445.md

---
from: audio-director
to: shot-composer
run_id: run001
section: ALL
created: 2026-03-27T14:45:00+09:00
feedback_count: 1

items:
  - id: FB-003
    severity: NOTE
    shot_id: 15
    field: narration_span
    symptom: |
      emotion_tag: HUMOR인데 narration_span이 1문장.
      HUMOR tension-build 패턴(setup → punch) 적용 불가.
    root_cause: |
      추정: shot-composer의 narration_map 단계에서 HUMOR 태그 shot의
      최소 문장 수를 검증하지 않은 것으로 보임.
    suggestion: |
      향후 narration_map 작성 시 HUMOR 태그 지정 shot은
      최소 2문장 이상의 narration_span을 배정하도록 검토.
    workaround: |
      [SERIOUS TONE] 단일 태그 적용 (§3 규칙 준수).
      비주얼(Doodle-Character) + Soft-Pop SFX가 유머를 보완.
---
```

---

## 3단계: run-director가 MERGE 게이트에서 피드백 수집

run-director가 MERGE STEP 0.5를 실행한다.

```bash
ls projects/EP03/feedback/run001/*.md
# → visual-director_SECTION02_20260327T1430.md
# → audio-director_ALL_20260327T1445.md
```

2개 파일, 총 3건의 피드백을 수집. 분류 결과:
- BLOCK: 0건
- FLAG: 2건 (FB-001, FB-002)
- NOTE: 1건 (FB-003)

### 사용자에게 보고

```markdown
## 📋 FEEDBACK REPORT — EP03 / run001
수집 일시: 2026-03-27 14:50
피드백 파일: 2개 / 총 항목: 3건

### 🟡 FLAG (2건) — 워크어라운드 적용됨, 검토 권장

| # | FROM | TO | Shot | 현상 요약 | 워크어라운드 | 제안 |
|---|------|----|------|----------|------------|------|
| FB-001 | visual-director | shot-composer | 24 | L3인데 [공간] 구조물 서술 없음 | 맥락 기반 배경 자체 생성 | [공간]에 구조물 힌트 추가 |
| FB-002 | visual-director | shot-composer | 27 | 실루엣 주체 모호 (사람/소품) | narration 참고 anonym 판정 | [감정선]에 주체 명시 |

### 🔵 NOTE (1건)

| # | FROM | TO | 내용 요약 |
|---|------|----|----------|
| FB-003 | audio-director | shot-composer | shot15: HUMOR 1문장 — tension-build 불가 |

---
⚠️ BLOCK 없음. 워크어라운드가 적용되어 있습니다. 선택해 주세요:
1. 워크어라운드 수용하고 MERGE 진행
2. shot24, shot27 수정 후 SECTION02 visual-director 재실행
3. 개별 항목별로 수용/수정 결정
```

---

## 4단계: 사용자 결정

**시나리오 A — 수용하고 진행**:
사용자: "1번. 워크어라운드 수용."
→ run-director: 기존 MERGE STEP 1~3 진행.

**시나리오 B — 수정 후 재실행**:
사용자: "2번. shot24, 27 수정해줘."

run-director 응답:
```
🔄 재실행 범위:
- 수정: shot-composer → shot24 [공간] + shot27 [감정선]
- 재생성: visual-director → SECTION02/shot24.md, shot27.md (05 delta 2개만)
- 유지: audio-director 산출물 전체 (narration_span 변경 없음)
- 유지: 다른 섹션 전체

예상 추가 시간: visual-director SECTION02 부분 재실행 (~2분)
진행하시겠습니까? [승인]
```

사용자: "승인"
→ run-director: shot-composer에게 shot24, 27 수정 위임 → visual-director SECTION02 재실행 → MERGE 재진입

**시나리오 C — 개별 결정**:
사용자: "FB-001은 수정, FB-002는 수용."
→ run-director: shot24만 수정 위임 → 해당 shot만 visual-director 재실행

---

## 5단계: 에피소드 완료 후 누적 로그 업데이트

EP03 완료 후, run-director가 cumulative_log.md를 업데이트:

```yaml
# feedback/cumulative_log.md (EP01~EP03 누적)

---
project: EP_SERIES
last_updated: 2026-03-27
episodes_analyzed: 3

patterns:
  - pattern_id: P-001
    frequency: 2회 / 3 에피소드
    from: visual-director
    to: shot-composer
    description: "L2+ 밀도 등급 shot에서 [공간] 구조물 서술 부족"
    affected_runs: [EP01/run001, EP03/run001]
    recommendation: |
      shot-composer 프롬프트의 creative_intent 규칙에 다음 추가 권장:
      "밀도 등급 L2 이상 지정 시, [공간] 태그에 반드시 구조물 키워드 1개 이상 포함.
      예: L2='나무 한 그루와 언덕', L3='공장 기둥과 천장 구조', L4='도시 거리 건물군'"

  - pattern_id: P-002
    frequency: 2회 / 3 에피소드
    from: audio-director
    to: shot-composer
    description: "HUMOR shot narration_span 1문장 — tension-build 패턴 적용 불가"
    affected_runs: [EP02/run001, EP03/run001]
    recommendation: |
      shot-composer의 narration_map 작성 규칙에 다음 추가 권장:
      "emotion_tag: HUMOR 지정 시 narration_span은 최소 2문장 배정.
      1문장만 가능하면 emotion_tag를 HUMOR 대신 REVEAL 또는 REFLECTIVE로 재고."
---
```

→ 아직 3회 미만(2회)이므로 `🔁 반복 패턴 경고`는 미발생.
→ EP04에서 동일 패턴 재발 시 경고 발생 → 사용자가 프롬프트 수정 결정.

---

## 디렉토리 구조 변화

```
projects/EP03/
  ├── feedback/                          ← 신규
  │   ├── run001/
  │   │   ├── visual-director_SECTION02_20260327T1430.md
  │   │   └── audio-director_ALL_20260327T1445.md
  │   └── cumulative_log.md             ← 에피소드 간 누적
  ├── 04_shot_composition/run001/
  ├── 05_visual_direction/run001/
  ├── 06_audio_narration/run001/
  ├── 07_shot_records/run001/
  └── ...
```

---

## 핵심 포인트 정리

| 항목 | 설명 |
|------|------|
| **추가 토큰 비용** | 거의 없음. 에이전트가 이미 Self-Reflection을 하면서 문제를 감지하고 있음. 차이는 그것을 파일로 기록하느냐 마느냐뿐. |
| **추가 실행 시간** | 0. 피드백 생성은 정상 실행의 일부. MERGE 게이트에서 파일 읽기 + 분류 = 수 초. |
| **사용자 부담** | BLOCK이 없으면 "1번(수용)" 한 번으로 끝. 대부분의 에피소드에서 FLAG 몇 건 + NOTE = 30초 검토. |
| **시스템 개선 경로** | 누적 로그 → 반복 패턴 식별 → 프롬프트 수정 → 근본 원인 제거. 에피소드를 돌릴수록 이슈가 줄어드는 자기 개선 루프. |
