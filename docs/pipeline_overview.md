# Pipeline Overview — 해빛 YouTube 제작 파이프라인

## 시스템 개요

AI 기반 유튜브 영상 제작 자동화 파이프라인.
Google Antigravity IDE 환경에서 Gemini + Claude + 수동 작업을 조합하여
리서치부터 스토리보드까지 10단계를 체계적으로 관리한다.

---

## 전체 파이프라인 구조

```
[MANUAL]         [GEMINI 3.1 PRO]        [CLAUDE]              [MANUAL]
    │                    │                    │                     │
01_research  →  02_planning  →  03_script  →  04~07_directing  →  09_assets  →  10_edit
    │                    │           │              │                     │
NotebookLM          AI Studio    AI Studio    Antigravity           Kling/Flow
                                                                     CapCut
```

| 단계 | 작업명 | 담당 | 모델 | 산출 파일 |
|------|--------|------|------|-----------|
| 01 | 자료수집 | 수동 (NotebookLM) | — | `01_research_{topic}_v1.md` |
| 02 | 분석 및 기획 | Gemini | gemini-3.1-pro | `02_planning_{topic}_v1.md` |
| 03~04 | 대본 작성 | Claude | claude-opus-4-6 | `04_script_final/{topic}_draft_v1.md` → `04_script_final/{topic}_v1.md` |
| 05 | Shot 구성 | Claude | claude-opus-4-6 | `05_shot_composition/v1/ANCHOR.md` + `{SECTION}/shot{N}.md` |
| 06 | 비주얼 디렉팅 | Claude | claude-opus-4-6 | `06_visual_direction/v1/{SECTION}/shot{N}.md` (Shot별 개별 파일) |
| 07 | Shot Record Build | Claude | claude-haiku-4-5 | `07_shot_records/v1/{SECTION}/shot{N}.md` + `07_ALL.txt` |
| 09 | 에셋 생성 | 수동/API (Flow/Gemini) | — | `09_assets/images/`, `09_assets/audio/` |
| 10 | 편집 | 수동 (CapCut) | — | — |

---

## 워크플로우 트리거 명령어

| 명령어 | 목적 | 선행 조건 |
|--------|------|-----------|
| `/start-project` | 프로젝트 폴더 구조 초기화 | 없음 |
| `/run-planning` | STEP 01~03 자동 실행 | NotebookLM MCP 연결 (실패 시 파일 직접 입력 모드 폴백) |
| `/run-directing` | STEP 04~MERGE 자동 실행 | `02_planning` 파일 존재 |
| `/check-status` | 파이프라인 진행 상태 확인 | `_meta.md` 존재 |

---

## 폴더 구조

```
{WORKSPACE_ROOT}/
├── .agent/
│   ├── rules/
│   │   ├── pipeline_rules.md          ← 항상 적용되는 행동 규칙
│   │   └── pipeline_reference.md     ← 구조·스키마·경로 레퍼런스
│   ├── workflows/
│   │   ├── start-project.md           ← /start-project
│   │   ├── run-planning.md            ← /run-planning (NotebookLM MCP)
│   │   ├── run-directing.md           ← /run-directing (Claude)
│   │   └── check-status.md            ← /check-status
│   └── skills/
│       ├── planner/SKILL.md           ← Gemini: STEP 02~03
│       ├── script-director/SKILL.md   ← Claude Opus: STEP 04
│       ├── shot-composer/SKILL.md     ← Claude Opus: STEP 05
│       ├── visual-director/SKILL.md   ← Claude Opus: STEP 06
│       └── shot-record-builder/SKILL.md ← Claude Haiku: STEP 07
├── docs/
│   ├── pipeline_overview.md           ← 이 파일
│   └── agent_skill_mapping.md         ← 상세 매핑 및 모델 배정
└── projects/
    └── {PROJECT_CODE}/
        ├── _meta.md
        ├── 01_research/
        ├── 02_planning/
        ├── 04_script_final/
        ├── 05_shot_composition/
        ├── 06_visual_direction/          ← v1/{SECTION}/shot{N}.md
        ├── 07_shot_records/              ← STEP 07 통합 출력
        └── 09_assets/
            ├── images/
            ├── videos/
            ├── audio/
            └── reference/
```

---

## 해빛 채널 크리에이티브 원칙

| 원칙 | 내용 |
|------|------|
| 페르소나 | AI 미디어 생태학자, 기술 철학자, 따뜻한 지식 스토리텔러 |
| 철학적 뿌리 | 매클루언 · 포스트먼 · 일리치 · 러시코프 (현대 AI 맥락 재해석) |
| 인지 여정 | Hook → 환경적 맥락 → 개념 시각화 → 실행 제언 (4단계 필수) |
| 비주얼 아이덴티티 | 미니멀 핸드드로잉 연필 낙서 (두들) 스타일 |
| 캐릭터 | 강낭콩 실루엣, 얼굴 없음, 숯색 |
| 오디오 철학 | 언더스코어링 — BGM은 나레이션을 압도하지 않는다 |
| 금지 원칙 | 차가운 기술 결정론, 사실적 사진 B-roll, 이미지 내 텍스트 |

---

## 파일 네이밍 규칙

```
{단계번호}_{작업명}_{topic}_{버전}.md
예: 04_script_final_AI기술전망_v1.md
    04_script_final/AI기술전망_draft_v1.md
```

---

## 외부 도구 연동

| 도구 | 역할 | 연동 단계 |
|------|------|-----------|
| NotebookLM | 리서치 자료 추출 (MCP) | STEP 01 |
| ElevenLabs Eleven v3 | 나레이션 음성 생성 | STEP 07 산출물 사용 |
| Google Flow (Veo) | AI 영상·이미지 에셋 생성 | STEP 08 프롬프트 사용 |
| CapCut | 최종 편집 | STEP 10 |
