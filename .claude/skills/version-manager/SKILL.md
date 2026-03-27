---
name: version-manager
description: "Manage version_manifest.yaml for run-based pipeline versioning. Python script handles all CRUD. Run /version-manager."
disable-model-invocation: true
---

# Workflow: version-manager

## Purpose

`version_manifest.yaml`을 Python 스크립트로 관리한다. LLM 불필요 — 결정적 YAML CRUD.

## Script

```bash
VM="${CLAUDE_SKILL_DIR}/scripts/version_manager.py"
python $VM --project {PROJECT_CODE} init [--description "Full run"]
python $VM --project {PROJECT_CODE} new-run [--sections SECTION01] [--description "SEC01 fix"]
python $VM --project {PROJECT_CODE} bump 07_shot_records
python $VM --project {PROJECT_CODE} status
```

---

## manifest 구조

```yaml
project: CH02
current_run: run002
runs:
  - run_id: run001
    description: "Full run"
    created: "2026-03-09"
    sections: null          # null = 전체 섹션
    stages_done: [04_shot_composition, 05_visual_direction, 06_audio_narration, 07_shot_records]
  - run_id: run002
    description: "SEC01 수정"
    created: "2026-03-10"
    sections: [SECTION01]   # 부분 업데이트
    stages_done: [04_shot_composition]
```

---

## 명령어

### init — 프로젝트 초기화
```bash
python $VM --project CH02 init --description "Full run"
```

### new-run — 새 run 생성
```bash
python $VM --project CH02 new-run                            # 전체
python $VM --project CH02 new-run --sections SECTION01       # 부분
```

### bump — 단계 완료 표시
```bash
python $VM --project CH02 bump 07_shot_records
```

### status — 현재 상태 출력
```bash
python $VM --project CH02 status
```

출력 형식:
```
📦 {PROJECT_CODE} 버전 현황

current_run: run002

run001 (2026-03-09) — 전체
  ✅ 04_shot_composition
  ✅ 05_visual_direction
  ✅ 06_audio_narration
  ✅ 07_shot_records

run002 (2026-03-10) — SECTION01
  ✅ 04_shot_composition
  ⏳ 05_visual_direction
```

---

## 경로 규칙

스크립트에 `--version` 없이 실행 시 `version_manifest.yaml`의 `current_run`을 자동 사용.
부분 업데이트 run은 `sections`가 지정된 섹션만 해당 run 폴더 사용.

---

## 위치

`projects/{PROJECT_CODE}/version_manifest.yaml`
