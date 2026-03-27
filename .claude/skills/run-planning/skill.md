---
name: run-planning
description: "Workflow: NotebookLM MCP → source selection → STEP 02 planning doc → STEP 03 script draft. Run /run-planning."
disable-model-invocation: true
---

# Workflow: run-planning
## 트리거: /run-planning
## 목적: NotebookLM MCP → 자료 선택 → STEP 02 기획 → STEP 03 대본 초안
## MCP 의존성: notebooklm-mcp (Python notebooklm_mcp 패키지 — Google API 직접 호출)
## 사용 모델: Claude Opus (STEP 02~03 — content-planner / script-director 에이전트 위임)

### MCP 서버 구성 정보
- **서버**: Python `notebooklm_mcp` v0.1.15 (Google API 직접 호출)
- **실행 파일**: `C:\Users\shinh\AppData\Local\Programs\Python\Python312\Scripts\notebooklm-mcp.exe`
- **인증 캐시**: `~/.notebooklm-mcp/auth.json` (쿠키 기반, 유효기간 약 1주)
- **주의**: Node.js `npx notebooklm-mcp`와 다름 — Node.js는 로컬 DB 방식으로 항상 빈 목록 반환

---

## PHASE 0 — MCP 연결 확인 (자동 인증 복구)

1. `notebook_list` 호출 → 성공(notebooks 배열 반환) 시 PHASE 1 진행
2. 오류/빈 목록 → `refresh_auth` 호출 후 `notebook_list` 재시도
3. 재시도 후 계속 실패 → **자동 복구 시도**:
   - Bash로 `notebooklm-mcp-auth` 실행 (브라우저 프로필 기반 헤드리스 인증)
   - 성공 시 `refresh_auth` → `notebook_list` 재시도
4. 자동 복구도 실패 → 폴백 옵션 제시:
   - **[A]** 사용자에게 `! notebooklm-mcp-auth` 직접 실행 요청 (브라우저 로그인 필요)
   - **[B]** 파일 직접 입력 모드 — `01_research/` 의 `src_*.md` 파일을 스캔하여
     PHASE 2로 진행, `notebook_query` 대신 파일 내용 직접 병합

---

## PHASE 1 — 노트북 목록 조회

1. `notebook_list` 결과를 테이블로 출력한다:

   `번호 | 노트북 이름 | 소스 수 | 소유`

2. 사용자에게 질문한다: "이번 영상에 사용할 노트북 번호를 입력하세요."

---

## PHASE 2 — 소스 목록 조회 및 핵심 자료 선택

1. `notebook_get` → `sources` 배열 추출 → `번호 | 소스 제목 | 유형` 테이블 출력
2. "핵심 자료(PRIMARY) 번호를 입력하세요 (복수 선택, 쉼표 구분)" 요청
3. 선택된 소스 목록을 확인 출력한다.

---

## PHASE 3 — 보조 자료 선택

1. 남은 소스 목록 출력 → "보조 자료(SECONDARY) 번호를 입력하세요 (없으면 Enter)" 요청
2. 최종 구성 요약 출력:
   ```
   🔴 PRIMARY: {선택 소스 목록}
   🔵 SECONDARY: {선택 소스 목록}
   이 구성으로 기획을 시작할까요? [Y / 다시 선택]
   ```

---

## PHASE 4 — NotebookLM에서 자료 추출

사용자 승인 후 선택된 소스에 대해 순차적으로 쿼리한다.

1. PRIMARY 소스 쿼리:
   ```
   TOOL: notebook_query
   PARAMS: { "notebook_id": "{notebook_id}",
     "query": "핵심 주장, 주요 데이터, 인용 가능한 팩트를 요약. 출처·수치 포함.",
     "source_ids": ["{primary_source_ids}"] }
   ```

2. SECONDARY 소스 쿼리:
   ```
   TOOL: notebook_query
   PARAMS: { "notebook_id": "{notebook_id}",
     "query": "보조 데이터, 사례, 배경 맥락 추출.",
     "source_ids": ["{secondary_source_ids}"] }
   ```

3. 추출 내용을 병합하여 research 파일 생성:
   SAVE: `projects/{PROJECT_CODE}/01_research/01_research_{topic}_v1.md`
   ```
   # 01_research_{topic}_v1.md
   GENERATED / PROJECT_CODE / NOTEBOOK
   ## PRIMARY SOURCES — {소스별 query 응답}
   ## SECONDARY SOURCES — {소스별 query 응답}
   ```

4. `_meta.md` STEP 01 상태를 ✅ DONE으로 업데이트한다.

---

## PHASE 5 — STEP 02 기획 실행 (content-planner 에이전트)

**`content-planner` 에이전트를 위임하여 실행한다.**

- INPUT: `01_research_{topic}_v1.md`
- OUTPUT: `projects/{PROJECT_CODE}/02_planning/02_planning_{topic}_v1.md`

```
✋ [STEP 02 검토 요청] 02_planning_{topic}_v1.md 를 확인해 주세요.
수정 시 v2 생성. 진행 시 "승인" 입력.
```
→ 사용자 승인 후 PHASE 6 진행.

---

## PHASE 6 — STEP 03 대본 초안 실행 (script-director 에이전트)

**`script-director` 에이전트를 위임하여 실행한다.**

- INPUT: 승인된 `02_planning_{topic}_v1.md`
- OUTPUT: `projects/{PROJECT_CODE}/03_script_final/{topic}_draft_v1.md`

```
✋ [STEP 03 검토 요청] 03_script_final/{topic}_draft_v1.md 를 확인해 주세요.
총 글자 수: {자} / 목표: 2,500~3,000자
수정 시 v2 생성. 진행 시 "승인" 입력.
```
→ 사용자 승인 후 `_meta.md` STEP 02, 03 상태를 ✅ DONE으로 업데이트한다.

---

## 완료 안내

```
run-planning 완료 — {노트북 이름} {선택 소스 수}개 활용
생성: 01_research_{topic}_v1.md / 02_planning_{topic}_v1.md / {topic}_draft_v1.md
다음: 대본 검토 후 /run-directing 실행
```
