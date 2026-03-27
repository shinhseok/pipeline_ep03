---
name: generate-videos
description: "Generate I2V video clips via Veo 3 API from iv_prompt + asset image. Run /generate-videos."
disable-model-invocation: true
allowed-tools: Bash(python *)
---

# Workflow: generate-videos

## 트리거: /generate-videos
## 목적: `05_visual_direction/{RUN_ID}/{SECTION}/` iv_prompt + asset_path 기반 Veo 3 I2V 영상 생성

---

## 사전 조건

- `.env` 파일에 `VERTEX_PROJECT` 설정 + `gcloud auth application-default login` 완료 필요
- `version_manifest.yaml` 존재 (current_run 자동 해상도)
- STEP 04 visual 완료: `05_visual_direction/{RUN_ID}/{SECTION}/` 에 `iv_prompt` 필드 존재
- Phase 2 이미지 생성 완료: `08_assets/images/{RUN_ID}/shot{N}.png` 존재

---

## 실행 명령

### Video Hook 영상 생성 (HOOK_MEDIA: video일 때 — Phase 0 이미지 생성 후)
```bash
python ${CLAUDE_SKILL_DIR}/scripts/generate_videos.py --project {PROJECT_CODE} --hook
```
- `hook_media_type: video`인 SECTION00_HOOK Shot만 대상
- 입력: `shot{N}_start.png` (+ `shot{N}_end.png` if exists) + `video_prompt`
- 엔진: `video_engine` 필드값 (기본 `veo3`)
- 길이: `video_duration` 필드값
- 저장: `09_assets/videos/{RUN_ID}/shot{N}_hook.mp4`

### Section별 생성
```bash
python ${CLAUDE_SKILL_DIR}/scripts/generate_videos.py --project {PROJECT_CODE} --section SECTION01
```

### 특정 Shot만 생성
```bash
python ${CLAUDE_SKILL_DIR}/scripts/generate_videos.py --project {PROJECT_CODE} --shots 01 02 03
```

### 전체 재생성 (기존 덮어쓰기)
```bash
python ${CLAUDE_SKILL_DIR}/scripts/generate_videos.py --project {PROJECT_CODE} --section SECTION01 --overwrite
```

---

## 자동 처리 규칙

- **모델**: `veo-3.0-generate-001`, `generate_audio=True`
- **기본 길이**: 4초 (변경: `--duration 8`)
- **[thinking: ...] 제거**: iv_prompt 전처리 시 자동 제거
- **저장 경로**: `08_assets/videos/{RUN_ID}/shot{N}.mp4`

---

## 완료 후 확인

```
✅ 영상 생성 완료
저장 경로: 08_assets/videos/{RUN_ID}/
생성 수: {N}개

다음:
  - 영상 품질 확인 후 CapCut 편집 시작
  - _meta.md SHOT MAPPING TABLE 업데이트
```
