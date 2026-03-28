---
name: feedback-protocol
version: 1.0
description: >
  파이프라인 에이전트 간 역방향 통신 규약.
  하류 에이전트가 상류 산출물의 문제를 구조화된 문서로 보고하고,
  run-director가 MERGE 게이트에서 수집·분류하여 사용자에게 제시한다.
applies_to: all agents
---

# Feedback Protocol v1.0 — 파이프라인 역방향 통신 규약

## 1. 문제 정의

현재 파이프라인은 **단방향**이다:
```
content-planner → script-director → shot-composer → visual-director / audio-director → merge
```

하류 에이전트가 상류 산출물의 문제를 발견해도 보고 경로가 없다.
결과: 문제가 merge 이후 사용자 검토에서야 발견되거나, 하류 에이전트가 임의로 우회 처리한다.

## 2. 설계 원칙

| 원칙 | 내용 |
|------|------|
| **제로 추가 패스** | 피드백은 정상 실행 중 발생한다. 별도 검토 패스를 돌리지 않는다. |
| **파일 기반 통신** | 기존 파이프라인과 동일하게 .md 파일로 소통한다. 채팅/자연어 대화 없음. |
| **MERGE 게이트 수집** | run-director가 MERGE 직전에 피드백을 수집·분류한다. 자연스러운 체크포인트 활용. |
| **사람이 최종 결정** | 에이전트는 보고만 한다. 수정 여부와 재실행 범위는 사용자가 결정한다. |
| **최소 변경** | 기존 에이전트 프롬프트에 1개 섹션만 추가. 기존 로직은 건드리지 않는다. |

---

## 3. 피드백 문서 형식

### 3.1 저장 경로

```
projects/{PROJECT_CODE}/feedback/{RUN_ID}/{FROM_AGENT}_{SECTION}_{timestamp}.md
```

예시:
```
projects/EP03/feedback/run001/visual-director_SECTION02_20260327T1430.md
projects/EP03/feedback/run001/audio-director_ALL_20260327T1445.md
```

### 3.2 YAML 구조

```yaml
---
# 피드백 헤더
from: {에이전트 이름}            # visual-director, audio-director, prompt-auditor
to: {대상 에이전트 이름}          # shot-composer, script-director, content-planner
run_id: {RUN_ID}
section: {SECTION | ALL}
created: {ISO 8601}
feedback_count: {N}

# 피드백 항목 배열
items:
  - id: FB-001
    severity: BLOCK | FLAG | NOTE
    shot_id: {N | null}
    field: {문제가 있는 필드명}
    symptom: |
      {관찰 가능한 현상 — 무엇이 잘못되었는가}
    root_cause: |
      {추정 원인 — 왜 발생했는가}
    suggestion: |
      {구체적 수정 제안}
    workaround: |
      {현재 에이전트가 취한 임시 조치 — 있을 때만}

  - id: FB-002
    severity: FLAG
    shot_id: 24
    field: creative_intent
    symptom: |
      [공간] L3 등급인데 구조물 서술이 "배경 없음"으로만 되어 있음.
      image_prompt에서 L3에 맞는 배경 요소를 생성할 근거가 없음.
    root_cause: |
      shot-composer가 L3 등급을 지정했으나 [공간] 태그에 구조물 힌트를 누락한 것으로 추정.
    suggestion: |
      shot24의 [공간]에 L3에 맞는 구조물 힌트 추가 (예: "공장 내부 기둥과 천장 구조물").
    workaround: |
      image_prompt P2에서 emotion_tag(TENSION)과 narration_span 맥락을 참고하여
      "어두운 공장 내부의 높은 천장과 굵은 기둥이 희미하게 보이는" 배경을 자체 생성함.
---
```

### 3.3 심각도 정의

| 심각도 | 의미 | run-director 처리 | 예시 |
|--------|------|-------------------|------|
| **BLOCK** | 현재 에이전트가 정상 출력을 생성할 수 없음 | MERGE 전 사용자에게 즉시 보고. 해결 전 merge 불가. | has_human:main인데 costume_refs 완전 누락, narration_span이 비어있음 |
| **FLAG** | 출력은 생성했으나 품질 저하 가능. 워크어라운드 적용됨. | MERGE 전 사용자에게 보고. 사용자가 수정/무시 선택. | creative_intent 불충분하여 자체 보강, emotion_tag과 narration 톤 불일치 |
| **NOTE** | 참고용. 다음 에피소드에서 개선하면 좋을 패턴. | 누적 로그. MERGE 보고서에 요약만 포함. | 특정 scene_type이 과다, 유사 구도 반복 |

---

## 4. 피드백 발생 지점 (WHO → WHOM)

### 4.1 visual-director → shot-composer

**발생 시점**: STEP 05 실행 중 (각 shot의 image_prompt 작성 시)
**검출 대상**:

| ID | 검출 항목 | 심각도 |
|----|----------|--------|
| VS-01 | `creative_intent [공간]` 밀도 등급과 실제 서술 불일치 | FLAG |
| VS-02 | `has_human` 판정 불가 — creative_intent에 캐릭터 관련 정보 모호 | FLAG |
| VS-03 | `costume_refs`/`prop_refs`에 ANCHOR에 없는 항목 참조 | BLOCK |
| VS-04 | `creative_intent [감정선]`이 너무 추상적이어서 결정적 순간 포착 불가 | FLAG |
| VS-05 | 인접 shot 간 시각 연속성 단절 (line_of_action 급변 + 카메라 거리 급변) | FLAG |
| VS-06 | `scene_type`이 narration_span 내용과 부적합 (예: 감정 코멘터리인데 Text-Motion) | FLAG |
| VS-07 | `emotion_nuance` 미지정 + emotion_tag만으로 장면 톤 결정 어려움 | NOTE |
| VS-08 | Counterpoint 위반 — narration과 creative_intent가 같은 내용 반복 | FLAG |
| VS-09 | image_prompt에 캐릭터 외형 묘사(체형·귀·꼬리 등)가 포함되어 ref 시트 충돌 위험. 표정은 허용 (ref 시트가 1표정이므로 프롬프트로 변화 필요) | FLAG |
| VS-10 | has_human:none + 소품 없음 (순백 PAUSE Shot) — 이미지 생성 불필요 또는 의미 없는 결과물 위험 | NOTE |
| VS-11 | 메인 캐릭터 의상 색(스카프 등)이 ref 시트와 다르게 채색됨 — NB2가 장면 포인트 색을 캐릭터에 적용하는 오류 | NOTE |
| VS-12 | 이미지 외곽에 사각 프레임/테두리 선 렌더링 — NB2가 "frame" 키워드 없이도 간혹 프레임 추가 | NOTE |
| VS-13 | iv_prompt에 Veo 정책 위반 가능 표현 (haze, smoke, explosion 등) → 영상 생성 거부 | FLAG |
| VS-14 | iv_prompt [ACTION] 과격한 동작 → Veo가 캐릭터 외형 변형 (springs, flailing, stretches 등) | FLAG |
| VS-15 | iv_prompt가 장면 변환/생성 지시 → Veo가 스케치 이탈, 3D 애니메이션으로 재구성 | BLOCK |
| VS-16 | 이미지에 텍스트(한글/숫자) 포함 → Veo I2V가 텍스트 왜곡·깨뜨림 | NOTE |
| VS-17 | iv_prompt 카메라 패닝 → 이미지 밖 영역 임의 생성 + 기존 요소 위치/상태 변경 | FLAG |
| VS-18 | iv_prompt에 VFX 표현 (pulse, glow, beam) → 스케치 스타일 이탈 디지털 이펙트 | FLAG |
| VS-19 | iv_prompt "paper-edge flutter" → Veo가 종이 프레임을 리터럴하게 렌더링 | FLAG |
| VS-20 | iv_prompt 실사 인체 동작 묘사 (fingers spread, presenting gesture) → 스케치가 실사 모델로 전환 | BLOCK |
| VS-21 | image_prompt에 광선/발광 표현 → 이미지 자체에 VFX 포함, iv_prompt 수정으로 해결 불가 | FLAG |
| VS-22 | iv_prompt "remains still" only → Veo가 자체 판단으로 엉뚱한 효과(종이 넘김 등) 추가 | FLAG |
| VS-23 | 카메라/동작이 캐릭터의 보이지 않는 면(뒷면·옆면)을 드러냄 → Veo가 상상으로 그려 외형 변형 (넥커치프→목도리, 체형 왜곡) | BLOCK |

### 4.2 audio-director → shot-composer

**발생 시점**: STEP 06 실행 중 (각 shot의 el_narration 태깅 시)
**검출 대상**:

| ID | 검출 항목 | 심각도 |
|----|----------|--------|
| AS-01 | `narration_span` 비어있음 (no-narration shot 아닌데) | BLOCK |
| AS-02 | `emotion_tag`과 `narration_span` 톤 불일치 (HUMOR인데 심각한 내용) | FLAG |
| AS-03 | `narration_span`에 [PAUSE] 태그 형식 오류 | FLAG |
| AS-04 | 단일 shot의 narration_span이 80자 초과 — EL 태깅 시 호흡 문제 | NOTE |
| AS-05 | HUMOR shot인데 narration_span이 1문장 — tension-build 불가 | NOTE |

### 4.3 audio-director → script-director

**발생 시점**: STEP 06 실행 중
**검출 대상**:

| ID | 검출 항목 | 심각도 |
|----|----------|--------|
| AX-01 | 나레이션 리듬이 섹션 전체적으로 단조 — 어미 반복 패턴 | NOTE |
| AX-02 | Song Hook 가사와 [BRIDGE] 연결 부자연스러움 | FLAG |

### 4.4 shot-composer → script-director

**발생 시점**: STEP 04 실행 중 (narration_map 작성 시)
**검출 대상**:

| ID | 검출 항목 | 심각도 |
|----|----------|--------|
| SC-01 | 특정 섹션의 나레이션 밀도가 과도하여 4초/shot 밀도 달성 불가 | FLAG |
| SC-02 | 섹션 전환점에서 나레이션이 끊기지 않아 shot 경계 결정 어려움 | FLAG |
| SC-03 | 비주얼 모티프가 대본에서 SEC03 이후 소멸 (4-16 위반 추정) | NOTE |

### 4.5 shot-composer → content-planner

**발생 시점**: STEP 04 실행 중
**검출 대상**:

| ID | 검출 항목 | 심각도 |
|----|----------|--------|
| SP-01 | 02_planning의 비주얼 전략에서 제안한 키 비주얼 Shot이 대본에서 구현 불가 | NOTE |
| SP-02 | 기획의 감정 아크와 실제 shot별 emotion_tag 분포 불일치 | NOTE |

---

## 5. 피드백 생성 규칙

### 5.1 에이전트별 피드백 생성 절차

각 에이전트는 **정상 실행의 일부로** 피드백을 수집한다. 별도 패스가 아니다.

```
1. Shot 처리 중 이상 감지 → 메모리에 피드백 항목 누적
2. 워크어라운드가 가능하면 적용하고 workaround 필드에 기록
3. 워크어라운드 불가(BLOCK)이면 해당 shot 출력을 건너뛰고 피드백에 기록
4. 섹션 완료 후 누적된 피드백을 feedback/ 디렉토리에 저장
5. 기존 Section Completion Report에 피드백 요약 1줄 추가
```

### 5.2 피드백 없을 때

피드백 항목이 0건이면 **피드백 파일을 생성하지 않는다**.
Section Completion Report에만 기록:

```
✅ Upstream feedback: 0건 — 이상 없음
```

### 5.3 피드백 품질 기준

| 기준 | 설명 |
|------|------|
| **구체적 shot_id** | "전반적으로 문제" 금지. 반드시 특정 shot_id를 지목. |
| **현상과 원인 분리** | symptom(관찰 사실)과 root_cause(추정)를 명확히 분리. 추정이면 "추정:" 명시. |
| **실행 가능한 suggestion** | "개선 필요" 금지. "shot24의 [공간] L3에 맞는 구조물 힌트 추가" 수준. |
| **workaround 투명성** | 자체 보강한 내용을 정확히 기록. 사용자가 품질을 판단할 수 있도록. |

---

## 6. run-director 피드백 수집 프로세스

### 6.1 수집 시점

기존 MERGE 흐름에 **STEP 0.5**로 삽입:

```
기존:
  STEP 1. validate_image_prompt.py
  STEP 2. validate_shot_records.py
  STEP 3. merge_records.py

변경:
  STEP 0.5. 피드백 수집 + 사용자 보고     ← 신규
  STEP 1.   validate_image_prompt.py
  STEP 2.   validate_shot_records.py
  STEP 3.   merge_records.py
```

### 6.2 수집 절차

```
1. Glob: feedback/{RUN_ID}/*.md
2. 파일이 없으면 → "✅ 피드백 0건" 보고 후 기존 MERGE 진행
3. 파일이 있으면 → 전체 읽기 → 심각도별 분류 → 아래 형식으로 보고
4. BLOCK 항목이 있으면 → MERGE 진행 불가. 사용자 결정 대기.
5. FLAG 항목만 있으면 → 사용자에게 보고 후 "진행/수정" 선택 요청.
6. NOTE만 있으면 → 보고 후 자동 진행.
```

### 6.3 사용자 보고 형식

```markdown
## 📋 FEEDBACK REPORT — {PROJECT_CODE} / {RUN_ID}
수집 일시: {YYYY-MM-DD HH:mm}
피드백 파일: {N}개 / 총 항목: {N}건

### 🔴 BLOCK ({N}건) — merge 전 해결 필수
| # | FROM | TO | Shot | 현상 요약 | 제안 |
|---|------|----|------|----------|------|
| FB-001 | visual-director | shot-composer | shot12 | ANCHOR에 없는 prop 참조 | ANCHOR에 {prop} 추가 |

### 🟡 FLAG ({N}건) — 워크어라운드 적용됨, 검토 권장
| # | FROM | TO | Shot | 현상 요약 | 워크어라운드 | 제안 |
|---|------|----|------|----------|------------|------|
| FB-003 | visual-director | shot-composer | shot24 | L3인데 구조물 서술 없음 | 자체 배경 생성 | [공간]에 힌트 추가 |

### 🔵 NOTE ({N}건) — 참고용 (다음 에피소드 개선)
| # | FROM | TO | 내용 요약 |
|---|------|----|----------|
| FB-005 | audio-director | script-director | SEC02 어미 반복 패턴 |

---
### 조치 옵션

**BLOCK이 있는 경우:**
> 🚫 MERGE 진행 불가. 아래 중 선택해 주세요:
> 1. 해당 shot 수정 후 재실행 (영향 범위: {에이전트} × {섹션})
> 2. 수동으로 직접 수정
> 3. 이슈 무시하고 강제 진행 (품질 저하 감수)

**FLAG만 있는 경우:**
> ⚠️ 워크어라운드가 적용되어 있습니다. 선택해 주세요:
> 1. 워크어라운드 수용하고 MERGE 진행
> 2. 상류 수정 후 하류 재실행
> 3. 개별 항목별로 수용/수정 결정

**NOTE만 있는 경우:**
> ℹ️ 참고 사항이 기록되었습니다. MERGE를 진행합니다.
```

---

## 7. 피드백 기반 재실행 범위 (Blast Radius)

사용자가 "수정 후 재실행"을 선택했을 때, 영향 범위를 최소화한다.

| 수정 대상 | 재실행 범위 | 이유 |
|----------|-----------|------|
| shot-composer의 특정 shot 1개 | 해당 shot의 05 + 06 delta만 재생성 | 다른 shot에 영향 없음 |
| shot-composer의 ANCHOR | 해당 ANCHOR 참조 shot 전체의 05 delta 재생성 | ANCHOR 변경은 image_prompt에 영향 |
| script-director의 특정 섹션 | 해당 섹션의 04 + 05 + 06 전체 재실행 | narration_span 변경은 연쇄 영향 |
| content-planner | 전체 재실행 (STEP 03부터) | 기획 변경은 전체 영향 |

run-director는 사용자에게 이 범위를 명시한 후 확인을 받는다:

```
🔄 재실행 범위:
- 수정: shot-composer → shot24 [공간] 태그
- 재생성: visual-director → SECTION02/shot24.md (05 delta)
- 유지: audio-director 산출물 (영향 없음)
- 유지: 다른 섹션 전체 (영향 없음)

진행하시겠습니까? [승인]
```

---

## 8. 피드백 누적 분석 (에피소드 간)

### 8.1 누적 로그

매 에피소드 완료 후, 피드백을 프로젝트 레벨로 누적한다:

```
projects/{PROJECT_CODE}/feedback/cumulative_log.md
```

### 8.2 누적 로그 형식

```yaml
---
project: {PROJECT_CODE}
last_updated: {date}
episodes_analyzed: {N}

patterns:
  - pattern_id: P-001
    frequency: {N}회 / {N} 에피소드
    from: visual-director
    to: shot-composer
    description: "L2+ 밀도 등급 shot에서 [공간] 구조물 서술 부족"
    affected_runs: [run001, run003, run005]
    recommendation: |
      shot-composer 프롬프트의 creative_intent 규칙에 다음 추가 권장:
      "L2 이상 밀도 등급 지정 시, [공간] 태그에 반드시 구조물 힌트 1개 이상 명시"

  - pattern_id: P-002
    frequency: {N}회 / {N} 에피소드
    from: audio-director
    to: shot-composer
    description: "HUMOR shot의 narration_span이 1문장이어서 tension-build 불가"
    affected_runs: [run002, run004]
    recommendation: |
      shot-composer의 narration_map 단계에서 HUMOR 태그 shot은
      최소 2문장 이상의 narration_span을 배정하도록 규칙 추가 권장
---
```

### 8.3 누적 분석 시점

- 매 에피소드 COMPLETE 후 run-director가 자동으로 해당 RUN의 피드백을 누적 로그에 추가
- 3회 이상 반복된 패턴은 `## 🔁 반복 패턴 경고`로 사용자에게 제시
- 사용자가 패턴을 확인하고 에이전트 프롬프트 수정을 결정

---

## 9. 기존 QA 에이전트와의 관계

| 에이전트 | 기존 역할 | 피드백 시스템과의 관계 |
|---------|----------|---------------------|
| **prompt-auditor** | 05 산출물의 패턴 위반 검출 → 보고서 출력 | **변경 없음**. 기존 보고서가 이미 피드백 역할. run-director가 MERGE 시 prompt-auditor 보고서도 함께 수집. |
| **pipeline-monitor** | 전 단계 파일 존재·필드 검증 → 이슈 파일 기록 | **변경 없음**. 기존 이슈 파일이 이미 피드백 역할. run-director가 MERGE 시 issues/ 디렉토리도 함께 수집. |

→ 신규 피드백 시스템은 이 두 에이전트가 **이미 커버하지 못하는 영역** — 즉, "하류 에이전트가 실행 중 발견한 상류 산출물 품질 문제"를 채운다.

---

## 10. 구현 우선순위

| 순서 | 작업 | 난이도 | 임팩트 |
|------|------|--------|--------|
| 1 | visual-director에 피드백 출력 섹션 추가 | 낮음 | 높음 (가장 많은 이슈 발생 지점) |
| 2 | audio-director에 피드백 출력 섹션 추가 | 낮음 | 중간 |
| 3 | run-director MERGE에 피드백 수집 스텝 추가 | 중간 | 높음 (사용자 가시성) |
| 4 | shot-composer에 피드백 출력 섹션 추가 | 낮음 | 낮음 (STEP 04→03 피드백은 빈도 낮음) |
| 5 | 누적 분석 로직 추가 | 중간 | 중간 (3+ 에피소드 후 효과) |

---

## 11. 금지 사항

- ❌ 피드백을 근거로 상류 파일을 직접 수정 (보고만 — 수정은 사용자 또는 해당 에이전트)
- ❌ BLOCK 피드백을 무시하고 merge 진행 (사용자 명시적 강제 진행만 허용)
- ❌ 피드백 항목에 shot_id 없이 "전반적으로 문제" 기술
- ❌ 동일 이슈를 피드백과 Self-Reflection에 이중 기재 (피드백 = 상류 이슈, Self-Reflection = 자기 검증)
- ❌ 피드백이 0건일 때 빈 피드백 파일 생성
- ❌ NOTE를 BLOCK으로 과대 보고 (에이전트가 정상 출력을 생성할 수 있으면 BLOCK이 아님)
