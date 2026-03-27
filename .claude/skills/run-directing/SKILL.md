---
name: run-directing
description: STEP 03~08 Claude 담당 구간 연속 실행 워크플로우. 대본 최종본(STEP 03) → Shot 구성(STEP 04) → 서브에이전트 병렬 실행(STEP 05+07) → 병합·렌더링. /run-directing 으로 실행.
disable-model-invocation: true
allowed-tools: Bash(python *)
---

# Workflow: run-directing
## 트리거: /run-directing
## 목적: STEP 03~08 Claude 담당 구간 연속 실행 (Shot Record 중심 파이프라인)
## 선행 조건: `02_planning_{topic}_v1.md` 존재 확인

---

## 컨텍스트 관리 (필수)

**SECTION 전환 시 `/clear` 실행** — Shot Record 컨텍스트 누적 방지:
- STEP 04 완료 → STEP 05+07 서브에이전트 실행 전 `/clear`
- 동일 Shot을 2회 이상 수정했으나 결과가 여전히 맞지 않으면 `/clear` + 프롬프트 재작성

**모델 전환**:
- STEP 03, 05: `/model claude-opus-4-6` (수동)
- STEP 05, 07: 서브에이전트 정의에 모델 포함 — 수동 전환 불필요

---

## Plan Mode 권장

STEP 04 시작 전 Plan Mode(`/plan`)로 전체 Shot 구성 전략을 먼저 수립하고 승인받으면 중간 수정 횟수를 줄인다.

---

## Steps

0. [STEP 0] 버전 초기화 (`/version-manager` 스킬 사용 — Claude 직접 처리)
   - `projects/{PROJECT_CODE}/version_manifest.yaml` 존재 확인
   - 없으면 init: `current_run: run001`, `runs: [{run_id: run001, sections: null, stages_done: []}]`
   - 신규 에피소드: new-run → `current_run` 증가 (run001 → run002)
   - 부분 수정: new-run with sections → `sections: [SECTION01]`
   - 생성된 `RUN_ID`를 이후 모든 경로에 사용 (예: `run001`)
   - ⚠️ 레거시 프로젝트(CH01 등)는 이 단계 건너뛰기 — 기존 `v1/`~`vN/` 방식 유지

1. `projects/{PROJECT_CODE}/02_planning/` 에서
   `02_planning_{topic}_v1.md` 파일 존재 여부를 확인한다.
   없으면 작업 중단 후 파일 경로 요청.

2. [STEP 03] `script-director` 에이전트 위임 / 모델: `claude-opus-4-6`
   - INPUT: `02_planning_{topic}_v1.md`
   - OUTPUT: `03_script_final/{topic}_draft_v1.md` (Phase A) → `{topic}_v1.md` (Phase B)
   - SAVE: `projects/{PROJECT_CODE}/03_script_final/`

   ```
   ✋ [STEP 03 검토 요청]
   최종: 03_script_final/{topic}_v1.md | 총 글자 수: {자} / 목표: 2,500~3,000자
   수정이 필요하면 말씀해 주세요. 진행하려면 "승인" 입력.
   ```

3. [STEP 04] `shot-composer` 에이전트 위임 / 모델: `claude-opus-4-6`
   - INPUT: `03_script_final/{topic}_v1.md`
   - **시작 전 FLOW_MODEL 선택**: NB-Pro vs NB2 1회 선택 → ANCHOR 헤더 `FLOW_MODEL:` 기록
   - OUTPUT: ANCHOR.md + Section별 Shot base 파일 (flow_prompt·el_narration placeholder 없음)
   - SAVE: `projects/{PROJECT_CODE}/04_shot_composition/{RUN_ID}/`
   - 완료 후: `/version-manager` 스킬로 `bump 04_shot_composition` 수행

   ```
   ✋ [STEP 04 검토 요청]
   파일: 04_shot_composition/{RUN_ID}/ANCHOR.md + Section별 Shot 파일
   총 Shot 수: {개} / 최소 기준: {ESTIMATED_DURATION ÷ 4}개
   수정이 필요하면 말씀해 주세요. 진행하려면 "승인" 입력.
   ```

4. [Phase 1 + STEP 05 + 07] **병렬 실행**

   Phase 1(ANCHOR 이미지)과 STEP 05+07(서브에이전트)을 **동시에 시작**한다.
   STEP 05은 ANCHOR 텍스트 묘사구만 참조하며 Phase 1 이미지 자체는 불필요하다.

   #### 4a. 사전 검증
   - `_meta.md`의 `VOICE_ID` 설정 여부 확인 → 미설정 시 audio-director 블록됨
   - STEP 04 출력 검증:
     ```bash
     python ${CLAUDE_SKILL_DIR}/scripts/validate_shot_records.py --project {PROJECT_CODE}
     ```
   - `/clear` 실행

   #### 4b. 병렬 실행 (3개 트랙 동시)

   ```
   ┌─ [Phase 1]  ANCHOR 이미지 생성 (NB2 API)
   │    - ANCHOR.md Layer 2 ⏳ 항목마다 Phase 1 NB2 생성 프롬프트 제공
   │    - API 자동 생성 → 09_assets/reference/ 저장
   │    - 사용자 검토 → 재생성 항목 선택 → ANCHOR Layer 2 ⏳→✅
   │    - ⚠️ Phase 1은 STEP 09(씬 이미지) 전 필수 완료
   │
   ├─ [STEP 05]  visual-director (Sonnet) 서브에이전트
   │    - 시작 프롬프트에 PROJECT_CODE, RUN_ID 명시
   │    - **섹션별 즉시 QA**: 각 Section 완료 즉시 prompt-auditor 실행
   │      → 위반 발견 시 해당 Section만 즉시 재수정 (전체 재실행 불필요)
   │
   └─ [STEP 06]  audio-director (Haiku) 서브에이전트
        - 시작 프롬프트에 PROJECT_CODE, RUN_ID 명시
   ```

   모델 전환 불필요 (서브에이전트 정의에 모델 포함).
   각 서브에이전트는 `04_shot_composition/{RUN_ID}/`만 읽음 (상호 의존성 없음).

   #### 4c. STEP 05 섹션별 즉시 QA

   ```
   [06 TITLECARD 완료] → prompt-auditor QA → ✅ or 즉시 수정
   [06 SECTION00 완료] → prompt-auditor QA → ✅ or 즉시 수정
   ... (Section마다 반복)
   ```

   #### 4d. 검토 요청

   ```
   ✋ [STEP 05+07 + Phase 1 검토 요청]
   파일:
     05_visual_direction/{RUN_ID}/{SECTION}/shot{N}.md      ← delta (flow_prompt + has_human) [QA 완료]
     06_audio_narration/{RUN_ID}/{SECTION}/shot{N}.md       ← delta (el_narration + audio)
     09_assets/reference/                                    ← Phase 1 ANCHOR 이미지
   수정이 필요하면 말씀해 주세요. 진행하려면 "승인" 입력.
   ```

5. [MERGE + RENDER] 통합 스크립트 실행
   ```bash
   python ${CLAUDE_SKILL_DIR}/scripts/merge_records.py --project {PROJECT_CODE} --render
   ```
   - **MERGE**: 04 base + 05 delta + 06 delta → `07_shot_records/{RUN_ID}/` + `07_ALL.txt`
   - **RENDER**: 자동 체이닝 → `08_storyboard/{RUN_ID}/` 마크다운 렌더링 (LLM 불필요)
   - 매니페스트 모드: 자동 bump (07_shot_records + 08_storyboard)

8. `_meta.md` 업데이트:
   - STEP 03~08 PIPELINE STATUS → ✅ DONE
   - FILE REGISTRY: 생성된 모든 파일명·버전 기록
   - SECTION VERSION TRACKER: 모든 버전 셀 채우기
   - SHOT MAPPING TABLE: 08_storyboard_index의 매핑 테이블 복사

---

## 완료 안내

```
🎬 run-directing 완료

생성 파일:
  03_script_final/{topic}_v1.md                          [Opus]
  04_shot_composition/{RUN_ID}/ (ANCHOR + Shot base)     [Opus]
  05_visual_direction/{RUN_ID}/ (delta: flow_prompt)     [Sonnet]
  06_audio_narration/{RUN_ID}/ (delta: el_narration)     [Haiku]
  07_shot_records/{RUN_ID}/ + 07_ALL.txt                 [merge script]
  08_storyboard/{RUN_ID}/ + index.md                     [render script]

다음 작업:
  1. ElevenLabs → 07_ALL 파일 → 나레이션 생성
  2. /generate-images --phase 1 → ANCHOR 이미지
  3. /generate-images → 씬 이미지
  4. CapCut 편집
```
