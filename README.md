# ecowise-pipeline v0.4

> **해빛(Eco-Sage) YouTube 영상 제작 파이프라인**
> Claude Code 기반 다중 에이전트 오케스트레이션 시스템

---

## 목차

1. [개요](#1-개요)
2. [파이프라인 흐름도](#2-파이프라인-흐름도)
3. [에이전트 정의 및 모델 할당](#3-에이전트-정의-및-모델-할당)
4. [스킬 (워크플로우) 정의](#4-스킬-워크플로우-정의)
5. [스크립트 (비-LLM)](#5-스크립트-비-llm)
6. [단계별 상세](#6-단계별-상세)
7. [모델 스위칭 메커니즘](#7-모델-스위칭-메커니즘)
8. [버전 관리 (Run-Based)](#8-버전-관리-run-based)
9. [폴더 구조](#9-폴더-구조)
10. [Shot Record YAML 스키마](#10-shot-record-yaml-스키마)
11. [정합성 검토 결과](#11-정합성-검토-결과)
12. [비용 구조](#12-비용-구조)

---

## 1. 개요

이 파이프라인은 YouTube 교양 채널 "해빛"의 영상 제작 전 과정을 Claude Code 에이전트들로 자동화한다.

**핵심 설계 원칙:**
- **Shot Record 중심** — 모든 단계가 Shot 단위 파일(1 shot = 1 file)로 데이터를 주고받음
- **Delta 모델** — 각 STEP은 담당 필드만 별도 delta 파일로 출력, 최종 병합은 스크립트가 수행
- **병렬 서브에이전트** — STEP 05(Visual) + STEP 06(Audio)은 상호 의존 없이 병렬 실행
- **근원적 해결 원칙** — 이슈 발생 시 per-shot 패치가 아닌 시스템 레벨 구조 수정 우선

---

## 2. 파이프라인 흐름도

```
[수동] STEP 01  리서치 자료 수집
         │
         ▼
[Sonnet] STEP 02  content-planner     → 02_planning/
         │
         ▼
[Opus]  STEP 03  script-director     → 03_script_final/ (draft → final)
         │
         ▼
[Opus]  STEP 04A shot-composer       → narration_map + ANCHOR (승인 대기)
         │       (단일 에이전트)
         ▼
[NB2]   Phase 1  generate_images     → 09_assets/reference/ (비주얼 ANCHOR 이미지)
         │
         ▼
[Opus]  STEP 04B shot-composer ×5    → 04_shot_composition/{RUN_ID}/ (섹션별 병렬)
         │
         ▼  ← /clear (컨텍스트 리셋)
         │
    ┌────┴────┐
    │         │
[Opus]     [Haiku]
 STEP 05    STEP 06
 visual-    audio-
 director   director
    │         │
    │  delta  │  delta
    ▼         ▼
    └────┬────┘
         │
[Script] MERGE   merge_records.py   → 07_shot_records/{RUN_ID}/
         │
         ▼
[Script] RENDER  render_storyboard  → 08_storyboard/{RUN_ID}/
         │
         ▼
[수동]   STEP 08  이미지/영상 생성 + CapCut 편집
```

---

## 3. 에이전트 정의 및 모델 할당

### 3.1 주 에이전트 (LLM 호출)

| 에이전트 | 파일 | 모델 | 담당 STEP | 역할 | 도구 |
|----------|------|------|-----------|------|------|
| **run-director** | `.claude/agents/run-director.md` | `sonnet` | 오케스트레이터 | STEP 03~08 전체 조율, 스크립트 실행 | Read, Glob, Grep, Bash |
| **content-planner** | `.claude/agents/content-planner.md` | `sonnet` | STEP 02 | 리서치 → 10섹션 기획서 (핵심 메시지+앵커링+비주얼 전략) | Read, Write, Glob, Grep |
| **script-director** | `.claude/agents/script-director.md` | `opus` | STEP 03 | 기획서 → 해빛 대본 + Fact Check + LLM 폴리싱 | Read, Write, Glob, Grep |
| **shot-composer** | `.claude/agents/shot-composer.md` | `opus` | STEP 04 | 대본 → Shot 분해 + 창의적 연출 결정 | Read, Write, Glob, Grep |
| **visual-director** | `.claude/agents/visual-director.md` | `opus` | STEP 05 | creative_intent → 창의적 장면 연출 + flow_prompt 작성 | Read, Write, Glob, Grep |
| **audio-director** | `.claude/agents/audio-director.md` | `haiku` | STEP 06 | emotion_tag → ElevenLabs 나레이션 태그 + BGM | Read, Write, Glob, Grep |

### 3.2 QA / 감시 에이전트

| 에이전트 | 파일 | 모델 | 역할 | 호출 방식 |
|----------|------|------|------|-----------|
| **prompt-auditor** | `.claude/agents/prompt-auditor.md` | `sonnet` | STEP 05 flow_prompt 품질 검증 (A~D 체크리스트) | 수동 ("prompt-auditor로 검토해줘") |
| **pipeline-monitor** | `.claude/agents/pipeline-monitor.md` | `haiku` | 파이프라인 건강 검진 (누락/불일치 탐지) | 수동 (PRE_WORK / POST_WORK / FULL) |

### 3.3 절대 금지 경계

| 에이전트 | 하는 일 | **절대 하지 않는 일** |
|----------|---------|----------------------|
| content-planner | 기획서 작성 | STEP 03 이후 대본 작성 |
| script-director | 대본 작성 | 창의적 Shot 구성 결정 |
| shot-composer | Shot 분해, creative_intent | 프롬프트 엔지니어링, 나레이션 태깅 |
| visual-director | 창의적 장면 연출 + flow_prompt 작성 | ANCHOR 신규 생성 |
| audio-director | 매트릭스 기반 태깅 | 창의적 결정 (태깅만 수행) |

---

## 4. 스킬 (워크플로우) 정의

모든 스킬은 `disable-model-invocation: true` — LLM 직접 호출 없이 오케스트레이션만 수행.

| 스킬 | 트리거 | 역할 |
|------|--------|------|
| **run-directing** | `/run-directing` | STEP 03~08 연속 실행 마스터 워크플로우 |
| **run-planning** | `/run-planning` | NotebookLM MCP → STEP 02 기획 |
| **start-project** | `/start-project` | 프로젝트 초기화 + `_meta.md` 생성 |
| **check-status** | `/check-status` | 파이프라인 진행 상태 표시 |
| **version-manager** | `/version-manager` | `version_manifest.yaml` CRUD |
| **generate-images** | `/generate-images` | NB2 API 이미지 생성 (Phase 1 + 2) |
| **generate-videos** | `/generate-videos` | Veo 3 I2V 영상 생성 |
| **qa-images** | `/qa-images` | 이미지 검수 → 이슈 트래킹 → 수정 |
| **record-history** | `/record-history` | Git commit + push (자동) |

---

## 5. 스크립트 (비-LLM)

LLM 호출 없이 Python으로 실행되는 자동화 스크립트:

| 스크립트 | 위치 | 역할 | 실행 시점 |
|----------|------|------|-----------|
| `validate_flow_prompt.py` | `.claude/skills/run-directing/scripts/` | NB2 JSON 구조 검증 | MERGE 전 (의무) |
| `validate_shot_records.py` | 상동 | STEP 04 base 필드 완성도 검사 | STEP 05+06 전 |
| `merge_records.py` | 상동 | 04 base + 05 delta + 06 delta → 완성 Shot Record | MERGE 단계 |
| `render_storyboard.py` | 상동 | Shot Record → 마크다운 스토리보드 렌더링 | RENDER 단계 |
| `generate_images.py` | `.claude/skills/generate-images/scripts/` | NB2 API 이미지 생성 | STEP 08 |
| `generate_videos.py` | `.claude/skills/generate-videos/scripts/` | Veo 3 I2V 영상 생성 | STEP 08 |

실행 예시:
```bash
RD=".claude/skills/run-directing/scripts"
python $RD/merge_records.py --project CH02
python $RD/render_storyboard.py --project CH02
```

---

## 6. 단계별 상세

### STEP 01 — 리서치 (수동)
- 사용자가 직접 자료 수집 → `01_research/` 저장

### STEP 02 — 기획 (content-planner, Sonnet)
- **입력**: `01_research_{topic}_v1.md`
- **출력**: `02_planning_{topic}_v1.md` (10섹션 전략서)
- 핵심 메시지 설계(한 줄 메시지+3전달포인트), 메시지 앵커링 맵, 비주얼 스토리텔링 전략
- 5단계 내러티브 구조(훅-셋업-텐션-페이오프-아웃트로) + 감정 아크 통합

### STEP 03 — 대본 (script-director, Opus)
- **입력**: `02_planning_{topic}_v1.md`
- **출력**: `03_script_final/{topic}_v1.md` (2,500~3,000자)
- Phase A(초안) → Phase B(해빛 페르소나 풀 폴리시) → Fact Check → LLM 폴리싱
- `[VISUAL CUE]` 주석, `[PAUSE: N초]` 태그 4~6개 이상
- Fact Check & Reference: 출처 검증 (0건 필수)
- LLM 폴리싱: AI 특유 표현 7개 카테고리 제거 (LLM_POLISH_LOG 출력)

### STEP 04 — Shot 구성 (shot-composer, Opus)
- **입력**: `03_script_final_{topic}_v1.md`
- **출력**: `04_shot_composition/{RUN_ID}/` (ANCHOR + Shot base 파일들)
- Phase A: narration_map 생성 → 사용자 승인
- Phase 1: ANCHOR 이미지 자동 생성 (NB2 API)
- Phase B: 섹션별 5개 병렬 에이전트 → Shot base 파일
- **결정 사항**: Shot 경계, creative_intent, line_of_action, emotion_tag, scene_type

### STEP 05 — 비주얼 (visual-director, Opus) [서브에이전트]
- **입력**: `04_shot_composition/{RUN_ID}/` (ANCHOR + Shot files)
- **출력**: `05_visual_direction/{RUN_ID}/` (delta: ref_images + flow_prompt + iv_prompt + has_human + asset_path)
- creative_intent → 창의적 장면 연출 + NB2 flow_prompt 작성

### STEP 06 — 오디오 (audio-director, Haiku) [서브에이전트]
- **입력**: `04_shot_composition/{RUN_ID}/` (Shot files)
- **출력**: `06_audio_narration/{RUN_ID}/` (delta: el_narration + bgm + volume_mix)
- emotion_tag + scene_type → ElevenLabs 태그 매트릭스 매핑 (창의적 결정 금지)

> **STEP 05 + 06은 병렬 실행** — 둘 다 STEP 04만 읽으므로 상호 의존 없음.

### MERGE — 병합 (merge_records.py)
- 04 base + 05 delta + 06 delta → `07_shot_records/{RUN_ID}/` + `07_ALL.txt`

### RENDER — 스토리보드 (render_storyboard.py)
- Shot Record → `08_storyboard/{RUN_ID}/` 마크다운 렌더링 (LLM 미사용)

### STEP 08 — 에셋 생성 (수동 + 스크립트)
- Phase 1: Canonical Shot (ANCHOR 레퍼런스)
- Phase 2: 씬별 이미지 생성 → `09_assets/images/{RUN_ID}/`

---

## 7. 모델 스위칭 메커니즘

### 7.1 작동 방식

모델 전환은 **두 가지 메커니즘**이 혼합되어 작동한다:

| 단계 | 전환 방식 | 상세 |
|------|-----------|------|
| STEP 02~04 | **수동** (`/model claude-opus-4-6`) | 사용자/오케스트레이터가 세션에서 수동 전환 |
| STEP 05 | **자동** (에이전트 frontmatter) | `visual-director.md`의 `model: opus` 선언에 의해 서브에이전트 생성 시 자동 적용 |
| STEP 06 | **자동** (에이전트 frontmatter) | `audio-director.md`의 `model: haiku` 선언에 의해 서브에이전트 생성 시 자동 적용 |
| MERGE/RENDER | **해당 없음** | Python 스크립트 — LLM 미사용 |

### 7.2 에이전트 frontmatter 모델 선언 (검증 완료)

```yaml
# content-planner.md     → model: sonnet
# script-director.md     → model: opus
# shot-composer.md        → model: opus
# run-director.md         → model: sonnet
# visual-director.md      → model: opus
# audio-director.md       → model: haiku
# prompt-auditor.md       → model: sonnet
# pipeline-monitor.md     → model: haiku
```

모든 에이전트의 frontmatter `model:` 필드가 문서화된 할당과 **정확히 일치**함을 확인.

### 7.3 컨텍스트 관리

- STEP 04 완료 → **`/clear` 실행** → STEP 05+06 서브에이전트 실행
- 동일 Shot 2회 수정 후에도 결과 불일치 시 `/clear` + 프롬프트 재작성
- 무관한 작업으로 전환 시 `/clear`

---

## 8. 버전 관리 (Run-Based)

### 8.1 매니페스트 구조

`projects/{PROJECT_CODE}/version_manifest.yaml`:

```yaml
current_run: run003
runs:
  run001:
    created: 2026-03-10
    status: done
    sections:
      TITLECARD: run001
      SECTION00_HOOK: run001
      SECTION01: run001
      ...
  run002:
    created: 2026-03-10
    status: done
    note: "STEP 05 재작업"
    base_run: run001
```

### 8.2 부분 업데이트

```bash
# SECTION01만 수정 → 새 run 생성, 나머지는 이전 run 폴백
new-run --sections SECTION01
```

### 8.3 레거시 호환

매니페스트 없으면 기존 `v1/`~`vN/` 폴더 자동 탐색.

---

## 9. 폴더 구조

```
projects/{PROJECT_CODE}/
  _meta.md                                 ← 프로젝트 메타 + STATUS 테이블
  version_manifest.yaml                    ← Run-based 버전 관리
  01_research/                             ← 리서치 자료
  02_planning/                             ← 기획서
  03_script_final/                         ← 대본 (draft + final)
  04_shot_composition/
    └── {RUN_ID}/
        ├── ANCHOR.md                      ← 전역 사전 (단일 소스)
        ├── narration_map.md               ← 나레이션 배분 맵
        ├── TITLECARD/shot00.md
        ├── SECTION00_HOOK/shot01.md ...
        ├── SECTION01/shot{N}.md ...
        ├── SECTION02/shot{N}.md ...
        ├── SECTION03/shot{N}.md ...
        └── SECTION04_OUTRO/shot{N}.md
  05_visual_direction/
    └── {RUN_ID}/{SECTION}/shot{N}.md      ← delta (ref_images + flow_prompt + iv_prompt + has_human)
  06_audio_narration/
    └── {RUN_ID}/{SECTION}/shot{N}.md      ← delta (el_narration + bgm)
  07_shot_records/
    └── {RUN_ID}/
        ├── {SECTION}/shot{N}.md           ← 병합 완성본
        └── 07_ALL.txt                     ← ElevenLabs 통합본
  08_storyboard/
    └── {RUN_ID}/
        ├── {SECTION}/shot{N}.md           ← 렌더링된 스토리보드
        └── index.md
  09_assets/
    ├── images/{RUN_ID}/shot{N}.png        ← 씬 이미지
    ├── videos/                            ← I2V 영상
    └── reference/
        ├── basic_charector_ref.png        ← 해빛 기본 체형
        ├── costumes/{RUN_ID}/*.jpeg       ← 캐릭터 변장 레퍼런스
        └── props/{RUN_ID}/*.jpeg          ← 소품 레퍼런스
```

---

## 10. Shot Record YAML 스키마

### 필드별 담당 STEP

| 필드 | 담당 | 타입 | 설명 |
|------|------|------|------|
| `shot_id` | STEP 04 | int | 전역 순번 (0부터) |
| `section` | STEP 04 | enum | TITLECARD ~ SECTION04_OUTRO |
| `local_id` | STEP 04 | int | Section 내 순번 |
| `duration_est` | STEP 04 | string | `{N}s` 형식 |
| `emotion_tag` | STEP 04 | enum | HUMOR / REFLECTIVE / AWE / REVEAL / TENSION |
| `narration_span` | STEP 04 | text | 대본 발췌 |
| `scene_type` | STEP 04 | enum | Doodle-Illust / Doodle-Animation / Text-Motion / Doodle-Character / Doodle-Diagram / Whiteboard-Reveal |
| `creative_intent` | STEP 04 | text | 6-tag: [공간][소품][카메라][조명][감정선][이전샷] |
| `line_of_action` | STEP 04 | enum | 에너지 라인 |
| `costume_refs` | STEP 04 | list | ANCHOR 변장명 |
| `prop_refs` | STEP 04 | list | ANCHOR 소품명 |
| `secondary_chars` | STEP 04 | list | 보조 인물 |
| `has_human` | 04→05 | enum | main/anonym/none. 05에서 최종 확정 |
| `ref_images` | **STEP 05** | list | 참조 이미지 경로 배열 (v3) |
| `thinking_level` | **STEP 05** | enum | high (기본) / low (v3) |
| `flow_prompt` | **STEP 05** | text | v3: 순수 한국어 서술형 / v2: [SCENE]+[MUST] |
| `iv_prompt` | **STEP 05** | text | Veo 3 I2V 모션 프롬프트 |
| `scene_id` | **STEP 06** | int | 나레이션 Scene 그룹 |
| `el_narration` | **STEP 06** | text | ElevenLabs Audio Tag 포함 |
| `bgm` | **STEP 06** | string | BGM 프롬프트 |
| `volume_mix` | **STEP 06** | string | 볼륨 비율 |
| `asset_path` | STEP 04 | path | `09_assets/images/{RUN_ID}/shot{N}.png` |
| `status` | STEP 04 | emoji | ⏳ / ✅ |

---

## 11. 정합성 검토 결과

### 11.1 모델 할당 검증 — **ALL PASS**

| 에이전트 | 문서 기재 모델 | frontmatter 실제값 | 결과 |
|----------|----------------|-------------------|------|
| content-planner | sonnet | `model: sonnet` | PASS |
| script-director | opus | `model: opus` | PASS |
| shot-composer | opus | `model: opus` | PASS |
| run-director | sonnet | `model: sonnet` | PASS |
| visual-director | opus | `model: opus` | PASS |
| audio-director | haiku | `model: haiku` | PASS |
| prompt-auditor | sonnet | `model: sonnet` | PASS |
| pipeline-monitor | haiku | `model: haiku` | PASS |

### 11.2 모델 자동 스위칭 검증

| 구간 | 메커니즘 | 검증 결과 | 비고 |
|------|----------|-----------|------|
| STEP 02~04 (Opus) | 수동 `/model` 전환 | PASS | 오케스트레이터가 Opus 세션에서 실행 |
| STEP 05 (Opus) | 서브에이전트 frontmatter | PASS | `model: opus` 선언 → 자동 적용 |
| STEP 06 (Haiku) | 서브에이전트 frontmatter | PASS | `model: haiku` 선언 → 자동 적용 |
| MERGE/RENDER | Python 스크립트 | PASS | LLM 미사용 — 모델 전환 불필요 |

### 11.3 아키텍처 정합성 — **이상 없음**

- **Delta 원칙 준수**: 각 에이전트가 담당 필드만 출력, `merge_records.py`가 병합
- **병렬 실행 독립성**: STEP 05+06 모두 STEP 04만 읽음, 상호 참조 없음
- **도구 선언 일관성**: 모든 에이전트 Read/Write/Glob/Grep 기본, run-director만 Bash 추가
- **스킬 LLM 차단**: 전 스킬 `disable-model-invocation: true` 확인
- **파일 네이밍**: `{STEP}_{task}/{RUN_ID}/{SECTION}/shot{id:02d}.md` 패턴 전 단계 일관

---

## 12. 비용 구조

```
고비용     Opus x3회    STEP 03, 04, 05          (대본 + Shot 구성 + 비주얼 연출)
중비용     Sonnet x2회  STEP 02, 오케스트레이터   (기획 + 파이프라인 조율)
저비용     Haiku x1회   STEP 06                   (오디오 태깅)
무료       Script x2회  MERGE + RENDER            (Python 스크립트)
```

> Opus는 창의적 결정이 필수인 대본/Shot 구성/비주얼 연출에 집중 투입.
> 구조화된 추출(기획)과 절차 실행(오케스트레이션)은 Sonnet으로 다운그레이드하여 비용 절감.

---

## 라이선스

이 파이프라인은 개인 프로젝트용입니다.
