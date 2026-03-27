---
name: check-status
description: "Display current pipeline progress, file registry, and MCP connection status for a project. Run /check-status."
---

# Workflow: check-status
## 트리거: /check-status
## 목적: 현재 프로젝트의 파이프라인 진행 상태 및 MCP 연결 상태를 즉시 출력

## Script

```bash
CS="${CLAUDE_SKILL_DIR}/scripts/check_status.py"
python $CS                          # 프로젝트 목록
python $CS --project {PROJECT_CODE} # 특정 프로젝트 상태
```

## Steps

1. Python 스크립트가 있으면 실행하여 기본 상태를 출력한다:
   ```bash
   python ${CLAUDE_SKILL_DIR}/scripts/check_status.py --project {PROJECT_CODE}
   ```
   스크립트가 없으면 `projects/{PROJECT_CODE}/_meta.md`를 읽어 직접 출력한다.
   PROJECT_CODE가 여러 개면 목록을 보여주고 선택하게 한다.

2. MCP 연결 상태를 추가로 확인한다 (스크립트 출력 이후):
   ```
   TOOL: notebooklm.list_notebooks
   PARAMS: {}
   ```
   - 연결됨: `🔌 MCP: ✅ 연결됨`
   - 실패: `🔌 MCP: ❌ 연결 안 됨 → /run-planning 전 MCP 재연결 필요`

3. 아래 형식으로 현재 상태를 출력한다:

```
## 📋 PROJECT STATUS: {PROJECT_CODE}
TOPIC: {topic}
LAST UPDATED: {날짜}

## 🔌 MCP 연결 상태
- notebooklm-mcp: ✅ 연결됨 / ❌ 연결 안 됨
(연결 안 됨 상태일 경우)
→ /run-planning 실행 전 MCP 재연결 필요
   또는 파일 직접 입력 모드 사용 가능

## 🤖 모델 버전
> pipeline-rules.md §11 참조

## 📊 파이프라인 현황
| STEP | 작업명 | 파일 | 상태 |
|------|--------|------|------|
| 01 | 자료수집 | {파일명 또는 —} | {상태} |
| 02 | 분석·기획 | {파일명 또는 —} | {상태} |
| 03 | 대본 초안 | {파일명 또는 —} | {상태} |
| 04 | 대본 각색 | {파일명 또는 —} | {상태} |
| 05 | Shot 구성 | {파일명 또는 —} | {상태} |
| 06 | 비주얼 디렉팅 | {파일명 또는 —} | {상태} |
| 07 | Shot Record Build | {파일명 또는 —} | {상태} |
| 08 | 스토리보드 | {파일명 또는 —} | {상태} |
| 09 | 에셋 생성 | {파일명 또는 —} | {상태} |
| 10 | 편집 | — | {상태} |

## 🔜 다음 액션
{현재 상태 기반으로 권장 다음 명령어 1~2개 제안}
```

4. BLOCKED 상태 항목이 있으면 원인(선행 파일 누락)을 명시한다.

5. 전체 완료 시 아래 메시지를 출력한다:
   `🎬 모든 단계 완료. CapCut 편집 후 업로드하세요.`
