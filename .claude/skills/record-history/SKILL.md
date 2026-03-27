---
name: record-history
description: "Append a dated work log entry to history/{YYYY-MM-DD}.md with task summary, changed files, dependency review, and self-reflection. Then commit and push to remote. Run /record-history."
disable-model-invocation: true
allowed-tools: Bash(git *)
---

# Workflow: record-history
## 트리거: /record-history
## 목적: 작업 지시·완료 내용·변경 파일을 날짜별 파일로 누적 기록 + self-reflection 수행

---

## 기록 담당

**Claude (메인 대화)** 가 직접 작성한다.
- 이유: 작업 컨텍스트(무엇을, 왜, 어떻게 변경했는지)가 메인 대화에만 존재하므로
  별도 에이전트에 위임하면 컨텍스트 손실 발생.
- 시점: 각 작업 세션 완료 직전, 또는 독립 완결 단위 작업 완료 후 즉시.

---

## Steps

1. **날짜 파일 결정**
   - 오늘 날짜 `YYYY-MM-DD` 형식으로 `history/{YYYY-MM-DD}.md` 경로 결정
   - 파일이 이미 존재하면 **맨 아래에 추가(append)**, 없으면 새로 생성

2. **기록 블록 작성** (아래 포맷 준수)

```markdown
## {N}. [{HH:MM}] {핵심 동사 + 대상} (10자 이내)

### 작업 지시
{사용자 지시 내용을 정리해 2~5줄로 요약}

### 완료 내용
{실제로 수행한 작업을 bullet으로 기술}

### 변경 파일
| 파일 | 변경 유형 | 변경 내용 요약 |
|------|-----------|----------------|
| {경로} | 수정/생성/삭제 | {한 줄 요약} |

### 의존성 검토
{변경된 파일이 영향을 주는 다운스트림 파일/단계 목록}
{영향 없으면 "없음"}

### Self-Reflection
{완료된 작업을 되돌아보며 개선 가능한 점, 놓친 부분, 더 좋은 방법이 있었는지 서술}
{없으면 "이상 없음"}

---
```

3. **의존성 추적 원칙**
   - 변경된 파일의 다운스트림 의존성을 명시한다
   - 스크립트 변경 → 의존 .md 파일 열거
   - 에이전트 .md 변경 → 해당 STEP 출력물(폴더 경로) 명시
   - 경로/필드 변경 → 해당 필드를 읽는 모든 스크립트 명시

4. **Git 커밋 & 푸시** (history 파일 저장 직후 자동 실행)
   ```bash
   git add history/{YYYY-MM-DD}.md
   git commit -m "history: {YYYY-MM-DD} 작업 기록"
   git push origin master
   ```
   - 리모트: `https://github.com/shinhseok/claude_workflow`
   - 브랜치: `master`
   - 커밋 실패 시 오류를 출력하고 사용자에게 보고한다.

5. **Self-Reflection 체크리스트** (기록 후 사용자에게 개선사항 보고)
   - [ ] 변경된 파일 중 누락된 의존성 파일이 있는가?
   - [ ] 이번 작업으로 다른 규칙/문서와 충돌이 생겼는가?
   - [ ] 더 단순한 방법이 있었는가?
   - [ ] 다음 작업자가 이 기록만 보고도 재현할 수 있는가?

---

## 포맷 규칙

- 파일 경로: 워크스페이스 루트 기준 상대경로
- 변경 유형: `수정` / `생성` / `삭제` / `이동`
- 작업 제목: 핵심 동사 + 대상, **10자 이내** (예: `레거시 마커 제거`, `폴더 재번호`, `history 시스템 생성`)
- 넘버링: 날짜 파일 내에서 1부터 순차 증가 (1, 2, 3 ...)
- 시간: KST 기준 HH:MM

---

## 예시 파일명

```
history/2026-03-09.md
history/2026-03-10.md
```
