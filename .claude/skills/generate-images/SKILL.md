---
name: generate-images
description: "Generate images via NB2 API. Phase 1 = ANCHOR reference images; Phase 2 = scene images from image_prompt. Run /generate-images."
disable-model-invocation: true
allowed-tools: Bash(python *)
---

# Workflow: generate-images
## 트리거: /generate-images
## 목적: NB2 API로 Phase 1 ANCHOR 이미지 또는 Phase 2 씬 이미지 생성

---

## 사전 조건

- `.env` 파일에 `VERTEX_PROJECT` 설정 + `gcloud auth application-default login` 완료 필요
- `version_manifest.yaml` 존재 (current_run 자동 해상도)
- Phase 1: `04_shot_composition/{RUN_ID}/ANCHOR.md` 존재
- Phase 2: `05_visual_direction/{RUN_ID}/{SECTION}/` 존재

---

## 실행 명령

### Phase 0 — Video Hook 이미지 우선 생성 (HOOK_MEDIA: video일 때)
```bash
python ${CLAUDE_SKILL_DIR}/scripts/generate_images.py --phase 0 --project {PROJECT_CODE}
```
- `hook_media_type: video`인 SECTION00_HOOK Shot만 대상
- `image_prompt[start]` → `shot{N}_start.png` 생성
- `image_prompt[end]` (null이 아닌 경우) → `shot{N}_end.png` 생성
- 저장: `09_assets/images/{RUN_ID}/shot{N}_start.png`, `shot{N}_end.png`
- **Phase 1보다 먼저 실행** — Video Hook 이미지가 영상 생성의 입력

> ⚠️ HOOK_MEDIA: image인 경우 Phase 0 스킵 (해당 Shot 없음)

### Phase 1 — ANCHOR 레퍼런스 이미지 생성
```bash
python ${CLAUDE_SKILL_DIR}/scripts/generate_images.py --phase 1 --project {PROJECT_CODE}
```
- ANCHOR Layer 2 ⏳ 항목마다 이미지 생성
- 저장: `09_assets/reference/props/v{N}/{파일명}.jpeg`

### Phase 2 — 씬 이미지 생성 (Section별)
```bash
# 특정 Section
python ${CLAUDE_SKILL_DIR}/scripts/generate_images.py --project {PROJECT_CODE} --section SECTION01

# 전체 재생성 (기존 덮어쓰기)
python ${CLAUDE_SKILL_DIR}/scripts/generate_images.py --project {PROJECT_CODE} --section SECTION01 --overwrite
```
- `05_visual_direction/{RUN_ID}/{SECTION}/` image_prompt 기반 이미지 생성
- 저장: `09_assets/images/{RUN_ID}/shot{N}.png`

---

## 자동 처리 규칙

- **확장자 폴백**: refer-to에 잘못된 확장자 → 자동 재시도 (`.png` ↔ `.jpeg`)

---

## 완료 후 확인

```
✅ 이미지 생성 완료
저장 경로: 09_assets/images/{RUN_ID}/
생성 수: {N}개

다음:
  - 이미지 품질 이슈 발생 시 → prompt-auditor 에이전트 호출
  - ANCHOR Layer 2 테이블 ⏳→✅ 업데이트
  - _meta.md SHOT MAPPING TABLE 업데이트
```
