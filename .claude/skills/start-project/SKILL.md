---
name: start-project
description: "Initialize new project folder structure and _meta.md. Run /start-project."
disable-model-invocation: true
---

# Workflow: start-project
## 트리거: /start-project
## 목적: 신규 프로젝트 폴더 구조 초기화 및 _meta.md 생성

## Steps

1. 사용자에게 아래 정보를 요청한다:
   - PROJECT_CODE (없으면 자동 생성: YT{연도}_{시퀀스})
   - topic (영상 주제, 한 줄)
   - VOICE_ID (ElevenLabs Voice ID — 없으면 "미정"으로 기재 후 STEP 05 전 설정 안내)
   - ASSET_GENERATION (MANUAL 또는 API — 기본값 MANUAL)
   - HOOK_TYPE (standard | song — 기본값 standard)
   - HOOK_MEDIA (image | video — 기본값 image)
   - 현재 완료된 단계 및 보유 파일 목록

2. 아래 폴더 구조를 생성한다:
   `projects/{PROJECT_CODE}/` 하위: `_meta.md`, `01_research/`, `02_planning/`, `03_script_final/`, `04_shot_composition/`, `05_visual_direction/`, `06_audio_narration/`, `07_shot_records/`, `08_storyboard/`, `09_assets/{images,videos,audio,reference}/`

   > 상세 구조: `pipeline_reference.md §4` 참조.
   > ⚠️ `assets/reference/style/character_reference.jpeg` (프로젝트 상위) 없으면 STEP 05 전 생성 필요.

3. `projects/{PROJECT_CODE}/_meta.md`를 _meta_template.md 기준으로 생성한다:
   - `PROJECT_CODE`, `TOPIC`, `CREATED`, `LAST_UPDATED` 실제 값으로 교체
   - `CHANNEL_SETTINGS`의 `VOICE_ID`, `ASSET_GENERATION`, `HOOK_TYPE`, `HOOK_MEDIA` 실제 값으로 교체
   - `SECTION VERSION TRACKER` 모든 버전 셀을 `—` (미생성) 상태로 초기화
   - `SHOT MAPPING TABLE` 빈 상태 유지 (STEP 08 완료 후 채움)
   - `FILE REGISTRY` 빈 상태 유지

4. 완료 후 다음 명령을 안내한다:

```
✅ 프로젝트 {PROJECT_CODE} 초기화 완료

폴더: projects/{PROJECT_CODE}/
메타: projects/{PROJECT_CODE}/_meta.md

확인 사항:
  □ assets/reference/style/character_reference.jpeg 확인 (해빛 캐릭터 전용, 프로젝트 상위)
  □ VOICE_ID 설정 확인 (_meta.md → CHANNEL_SETTINGS)
  □ 워크스페이스 최상위 `.env` 파일 내 `VERTEX_PROJECT` 설정 + `gcloud auth application-default login` 완료 확인

다음 단계:
  - NotebookLM 자료 준비 완료 → /run-planning 실행
  - 02_planning 파일 준비 완료 → /run-directing 실행
  - 진행 상태 확인 → /check-status 실행
```
