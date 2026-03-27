---
name: agent-patches-for-feedback
version: 1.0
description: >
  기존 에이전트 프롬프트에 추가할 피드백 출력 섹션.
  각 에이전트 .md 파일의 지정된 위치에 해당 섹션을 삽입한다.
  기존 로직은 일절 수정하지 않는다 — 순수 추가만.
---

# Agent Patches — 피드백 루프 통합

## 적용 방법

각 에이전트 .md 파일에서:
1. `## Self-Reflection` 섹션 **바로 위**에 `## Upstream Feedback` 섹션을 삽입
2. `## Section Completion Report` (또는 `## Completion Report`)에 피드백 요약 1줄 추가
3. `## Prohibitions`에 피드백 관련 금지 항목 1~2개 추가

---

## PATCH 1: visual-director.md

### 삽입 위치: `## Self-Reflection` 바로 위

```markdown
## Upstream Feedback (상류 피드백 — STEP 04 shot-composer 대상)

### 피드백 수집 절차

flow_prompt 작성 중 아래 조건을 감지하면 메모리에 피드백 항목을 누적한다.
**정상 출력 생성을 우선** — 워크어라운드가 가능하면 적용 후 기록한다.

### 감지 항목

| ID | 조건 | 심각도 | 워크어라운드 |
|----|------|--------|------------|
| VS-01 | `[공간]` 밀도 등급 ≥ L2인데 구조물 서술 없음 | FLAG | narration_span + emotion_tag 맥락으로 배경 자체 생성 |
| VS-02 | creative_intent에서 has_human 판정 불가 (캐릭터 관련 정보 모호) | FLAG | 보수적으로 `none` 판정 후 기록 |
| VS-03 | costume_refs/prop_refs가 ANCHOR에 없는 항목 참조 | BLOCK | 출력 불가 — 해당 shot 건너뜀 |
| VS-04 | `[감정선]`이 "슬픈 분위기" 수준으로 추상적 — 결정적 순간 포착 불가 | FLAG | narration_span에서 감정 단서를 추출하여 보강 |
| VS-05 | 인접 shot 간 line_of_action + 카메라 거리 동시 급변 (시각 단절) | FLAG | 중간 톤으로 부드럽게 전환 처리 |
| VS-06 | scene_type이 narration_span 내용과 부적합 | FLAG | scene_type에 최대한 맞추되 피드백 기록 |
| VS-07 | emotion_nuance 미지정 + tag만으로 톤 결정이 모호 | NOTE | 기본 뉘앙스 적용 |
| VS-08 | Counterpoint 위반 — narration과 creative_intent가 동어 반복 | FLAG | flow_prompt에서 체감/감각 방향으로 재해석 |

### 피드백 출력

섹션 완료 시 피드백 항목이 1건 이상이면:
→ `feedback/{RUN_ID}/visual-director_{SECTION}_{timestamp}.md` 저장

피드백 항목이 0건이면:
→ 파일 생성 안 함. Completion Report에 "Upstream feedback: 0건" 기록.

### 피드백 파일 형식

feedback-protocol.md §3.2 YAML 형식을 따른다.
```

### Section Completion Report 수정

기존:
```
[{SECTION} 비주얼 디렉팅 완료]
저장: 05_visual_direction/{RUN_ID}/{SECTION}/ — {N}개 파일 (delta, v3)
Shot 수: {N}개 | FLOW_MODEL: {NB-Pro | NB2}
```

변경 (1줄 추가):
```
[{SECTION} 비주얼 디렉팅 완료]
저장: 05_visual_direction/{RUN_ID}/{SECTION}/ — {N}개 파일 (delta, v3)
Shot 수: {N}개 | FLOW_MODEL: {NB-Pro | NB2}
Upstream feedback: {N}건 (BLOCK {N} / FLAG {N} / NOTE {N}) → feedback/{RUN_ID}/ 기록
```

### Prohibitions 추가 항목

```
- ❌ 피드백을 근거로 STEP 04 파일을 직접 수정 (보고만 — 수정은 run-director 경유)
- ❌ BLOCK 피드백 해당 shot을 워크어라운드로 우회 출력 (건너뛰고 피드백에 기록)
```

---

## PATCH 2: audio-director.md

### 삽입 위치: `## Self-Reflection` 바로 위

```markdown
## Upstream Feedback (상류 피드백 — STEP 04 shot-composer / STEP 03 script-director 대상)

### 피드백 수집 절차

el_narration 태깅 중 아래 조건을 감지하면 메모리에 피드백 항목을 누적한다.
**정상 출력 생성을 우선** — 워크어라운드가 가능하면 적용 후 기록한다.

### 감지 항목 (→ shot-composer)

| ID | 조건 | 심각도 | 워크어라운드 |
|----|------|--------|------------|
| AS-01 | narration_span 비어있음 (no-narration shot 아닌데) | BLOCK | 출력 불가 — el_narration: (오류) 기재 |
| AS-02 | emotion_tag과 narration_span 톤 불일치 (HUMOR인데 심각한 내용) | FLAG | emotion_tag 기준으로 EL 태그 적용, 불일치 기록 |
| AS-03 | narration_span의 [PAUSE] 형식 오류 (변환 불가) | FLAG | 가장 가까운 형식으로 추정 변환 |
| AS-04 | 단일 shot narration_span 80자 초과 | NOTE | 그대로 처리 (정보용) |
| AS-05 | HUMOR shot narration_span 1문장 — tension-build 패턴 적용 불가 | NOTE | [SERIOUS TONE] 단일 태그 적용 |

### 감지 항목 (→ script-director)

| ID | 조건 | 심각도 | 워크어라운드 |
|----|------|--------|------------|
| AX-01 | 섹션 전체 어미 반복 패턴 (귀로 듣기 단조) | NOTE | 그대로 처리 (정보용) |
| AX-02 | Song Hook → [BRIDGE] 전환 부자연스러움 | FLAG | 크로스페이드 설정으로 보완 |

### 피드백 출력

전체 섹션 완료 시 피드백 항목이 1건 이상이면:
→ `feedback/{RUN_ID}/audio-director_ALL_{timestamp}.md` 저장

to 필드를 항목별로 구분하여, shot-composer 대상과 script-director 대상을 같은 파일에 기록한다.

### 피드백 파일 형식

feedback-protocol.md §3.2 YAML 형식을 따른다.
```

### Section Completion Report 수정

기존:
```
✋ [{SECTION} 오디오-나레이션 완료]
저장: 06_audio_narration/{RUN_ID}/{SECTION}/ — {N}개 파일 (delta)
Shot 수: {N}개
```

변경 (1줄 추가):
```
✋ [{SECTION} 오디오-나레이션 완료]
저장: 06_audio_narration/{RUN_ID}/{SECTION}/ — {N}개 파일 (delta)
Shot 수: {N}개
Upstream feedback: {N}건 (BLOCK {N} / FLAG {N} / NOTE {N}) → feedback/{RUN_ID}/ 기록
```

### Prohibitions 추가 항목

```
- ❌ 피드백을 근거로 STEP 04/03 파일을 직접 수정 (보고만)
- ❌ AS-01(BLOCK) 해당 shot을 빈 el_narration으로 출력 (오류 표시 후 피드백 기록)
```

---

## PATCH 3: run-director.md

### 삽입 위치: `### MERGE` 섹션의 기존 STEP 1 바로 위

```markdown
### MERGE

**STEP 0.5 — 피드백 수집 및 사용자 보고 (feedback-protocol 연동)**

```bash
# 피드백 파일 존재 확인
ls projects/{PROJECT_CODE}/feedback/{RUN_ID}/*.md 2>/dev/null
```

피드백 파일이 없으면:
→ `✅ Upstream feedback: 0건 — MERGE 진행` 출력 후 기존 STEP 1로 진행.

피드백 파일이 있으면:
1. 전체 피드백 파일 읽기
2. 심각도별 분류: BLOCK / FLAG / NOTE
3. 아래 형식으로 사용자에게 보고:

```
## 📋 FEEDBACK REPORT — {PROJECT_CODE} / {RUN_ID}
수집 일시: {YYYY-MM-DD HH:mm}
피드백 파일: {N}개 / 총 항목: {N}건

### 🔴 BLOCK ({N}건) — merge 전 해결 필수
| # | FROM | TO | Shot | 현상 요약 | 제안 |
|---|------|----|------|----------|------|
| {id} | {from} | {to} | {shot_id} | {symptom 1줄 요약} | {suggestion 1줄 요약} |

### 🟡 FLAG ({N}건) — 워크어라운드 적용됨, 검토 권장
| # | FROM | TO | Shot | 현상 요약 | 워크어라운드 | 제안 |
|---|------|----|------|----------|------------|------|
| {id} | {from} | {to} | {shot_id} | {symptom} | {workaround} | {suggestion} |

### 🔵 NOTE ({N}건)
{요약만}
```

4. 사용자 응답에 따라:
   - **BLOCK 있음** → 사용자 결정 대기 (merge 진행 불가)
     - "수정 후 재실행" 선택 시 → blast radius 계산 후 재실행 범위 제시
     - "강제 진행" 선택 시 → 경고 후 merge 진행
   - **FLAG만** → "워크어라운드 수용하고 진행" 또는 "수정 후 재실행" 선택 요청
   - **NOTE만** → 자동 진행 (보고만)

5. prompt-auditor 보고서가 있으면 함께 수집:
```bash
ls projects/{PROJECT_CODE}/05_visual_direction/{RUN_ID}/audit_report*.md 2>/dev/null
```

6. pipeline-monitor 이슈가 있으면 함께 수집:
```bash
ls issues/{날짜}/{PROJECT_CODE}_{RUN_ID}_*.md 2>/dev/null
```

7. 모든 보고를 통합하여 단일 보고서로 제시.
```

### COMPLETE 섹션에 누적 로그 업데이트 추가

기존 COMPLETE 블록 뒤에 추가:

```markdown
### POST-COMPLETE — 피드백 누적 로그

에피소드 완료 후, 이번 RUN의 피드백을 누적 로그에 추가한다:

```bash
# 누적 로그 존재 확인
cat projects/{PROJECT_CODE}/feedback/cumulative_log.md 2>/dev/null
```

피드백이 있었으면:
→ `feedback/cumulative_log.md`에 이번 RUN의 패턴을 추가
→ 3회 이상 반복 패턴이 있으면 사용자에게 `🔁 반복 패턴 경고` 보고:

```
🔁 반복 패턴 경고 — 아래 이슈가 {N}회 반복되었습니다:
| 패턴 | 빈도 | FROM → TO | 제안 |
|------|------|-----------|------|
| {description} | {N}/{total_episodes} | {from} → {to} | {recommendation} |

에이전트 프롬프트 수정을 검토하시겠습니까?
```
```

### Prohibitions 추가 항목

```
- ❌ BLOCK 피드백을 사용자 확인 없이 무시하고 merge 진행
- ❌ 피드백 대상 에이전트의 파일을 run-director가 직접 수정 (재위임으로 처리)
- ❌ 피드백 파일 자체를 삭제 또는 수정 (감사 추적용 보존)
```

### Self-Reflection 추가 항목

```
- [ ] MERGE 전 feedback/{RUN_ID}/ 디렉토리를 확인했는가
- [ ] BLOCK 피드백이 있으면 사용자에게 보고하고 결정을 받았는가
- [ ] 에피소드 완료 후 cumulative_log.md를 업데이트했는가
- [ ] 3회+ 반복 패턴이 있으면 사용자에게 경고했는가
```

---

## PATCH 4: shot-composer.md (우선순위 낮음 — Phase 2에서 적용 가능)

### 삽입 위치: `## Self-Reflection` 바로 위

```markdown
## Upstream Feedback (상류 피드백 — STEP 03 script-director / STEP 02 content-planner 대상)

### 피드백 수집 절차

narration_map 작성 및 Shot 설계 중 아래 조건을 감지하면 피드백 항목을 누적한다.

### 감지 항목 (→ script-director)

| ID | 조건 | 심각도 | 워크어라운드 |
|----|------|--------|------------|
| SC-01 | 특정 섹션 나레이션 밀도 과도 — 4초/shot 밀도 달성 불가 | FLAG | 최선의 shot 경계로 분할하되, 일부 shot 5~6초 허용 |
| SC-02 | 섹션 전환점에 나레이션 경계 없음 — shot 경계 결정 어려움 | FLAG | 의미 단위로 가장 가까운 지점에서 분리 |
| SC-03 | 비주얼 모티프가 SEC03 이후 소멸 (4-16 위반 추정) | NOTE | shot-composer는 대본 수정 불가 — 정보용 |

### 감지 항목 (→ content-planner)

| ID | 조건 | 심각도 | 워크어라운드 |
|----|------|--------|------------|
| SP-01 | 02_planning 키 비주얼 Shot이 대본에서 구현 불가 | NOTE | 대체 키 비주얼 자체 설계 |
| SP-02 | 기획 감정 아크와 실제 emotion_tag 분포 불일치 | NOTE | 대본 기준으로 emotion_tag 배정 |

### 피드백 출력

PHASE B 완료 시 (전체 shot 파일 저장 후):
→ `feedback/{RUN_ID}/shot-composer_ALL_{timestamp}.md` 저장

### 피드백 파일 형식

feedback-protocol.md §3.2 YAML 형식을 따른다.
```

---

## 패치 적용 체크리스트

| # | 에이전트 | 패치 | 적용 완료 |
|---|---------|------|----------|
| 1 | visual-director.md | Upstream Feedback 섹션 + Completion Report 수정 + Prohibitions 추가 | ☐ |
| 2 | audio-director.md | Upstream Feedback 섹션 + Completion Report 수정 + Prohibitions 추가 | ☐ |
| 3 | run-director.md | MERGE STEP 0.5 + POST-COMPLETE + Prohibitions + Self-Reflection 추가 | ☐ |
| 4 | shot-composer.md | Upstream Feedback 섹션 (우선순위 낮음) | ☐ |

> **적용 순서**: 1 → 2 → 3 → (에피소드 3회 후) → 4
> Patch 1~3만 적용해도 핵심 피드백 루프가 작동한다.
