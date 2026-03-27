# Claude Code 워크플로우 가이드 (2025-2026 최신)

> 작성일: 2026-03-03
> 출처: Anthropic 공식 문서, Claude Code 릴리즈 노트, 커뮤니티 연구 자료 종합
> 목적: ecowise-pipeline 작업 효율 향상을 위한 실용 가이드

---

## 1. 핵심 원칙 — 컨텍스트 윈도우 관리

컨텍스트 윈도우는 가장 희소한 자원이다.
컨텍스트가 채워질수록 Claude의 성능이 저하되므로 전략적으로 관리해야 한다.

### 1-1. 즉각 적용 가능한 기법

| 기법 | 명령 / 방법 | 효과 |
|------|------------|------|
| **사용량 모니터링** | `/cost` | 현재 세션 토큰 소비량 확인 |
| **무관 작업 전환 시 초기화** | `/clear` | 관련 없는 두 작업 사이 컨텍스트 리셋 |
| **선택적 압축** | `/compact "X에 집중"` | 핵심 정보만 요약 보존 |
| **상태 표시줄** | `/status-line` 설정 | 실시간 토큰 사용량 표시 |

### 1-2. CLAUDE.md 관리 원칙

> **목표: 500줄 이하** — 초과하면 Claude가 지시의 절반을 무시한다.

**포함해야 하는 것:**
- Claude가 코드에서 추론 불가능한 특수 커맨드 / 실행 방법
- 프로젝트 고유 코드 스타일 규칙
- 테스트 실행 방법, PR 컨벤션
- 아키텍처 결정 배경

**제외해야 하는 것:**
- Claude가 코드 읽기만 해도 알 수 있는 정보
- 언어 표준 컨벤션 (자명한 것들)
- 자주 바뀌는 상세 정보
- Skill 파일에서 처리 가능한 도메인 지식

**Rule**: "이 줄을 지워도 Claude가 실수하지 않는가?" → Yes면 지운다.

---

## 2. 표준 4단계 워크플로우

복잡한 다단계 작업의 권장 구조:

```
Phase 1 — EXPLORE (Plan Mode)
  → Claude가 파일을 읽고 분석만, 변경 없음
  → 명령: "read /src/X and understand Y"

Phase 2 — PLAN
  → 상세 구현 계획 요청
  → "Create a detailed plan. What files change? What's the flow?"
  → Ctrl+G로 계획을 에디터에서 직접 편집 가능

Phase 3 — IMPLEMENT (Normal Mode)
  → 계획 기반 실행 + 검증 기준 제시
  → "implement from the plan. Run tests, fix failures."

Phase 4 — COMMIT
  → "commit with descriptive message and open PR"
```

**건너뛸 수 있는 때:** 1문장으로 설명 가능한 소규모 변경 (타이포 수정, 로그 추가, 변수 리네임)

---

## 3. 검증(Verification) — 가장 고효율 전략

Claude에게 **스스로 검증하는 방법**을 제공하면 외부 피드백 루프 없이도 품질이 향상된다.

| 방식 | 나쁜 예 | 좋은 예 |
|------|--------|--------|
| **테스트 기반** | "이메일 유효성 검사 구현" | "validateEmail 구현. 테스트 케이스: user@example.com→true, invalid→false. 작성 후 반드시 실행" |
| **스크린샷 비교** | "대시보드 개선" | "[스크린샷 첨부] 이 디자인 구현. 스크린샷 찍어 비교하고 차이점 목록화 후 수정" |
| **빌드 검증** | "빌드 실패 수정" | "[에러 메시지] 근본 원인 수정 후 빌드 성공 확인" |

검증 없이는 개발자가 유일한 피드백 루프가 된다. 모든 실수가 개발자의 검토를 요구하게 된다.

---

## 4. 서브에이전트(Subagent) 패턴

### 4-1. 언제 사용하는가

- 독립적으로 병렬 실행 가능한 작업들
- 컨텍스트 격리가 필요한 전문 작업 (코드 리뷰, 보안 감사)
- 대량 파일 탐색 (탐색 비용을 서브에이전트에 격리)

### 4-2. 설정 방법 (`.claude/agents/{이름}.md`)

```markdown
---
name: shot-quality-reviewer
description: Shot Record의 flow_prompt 품질을 검토하고 NB2 패턴 오류를 찾는다
tools: Read, Glob, Grep
model: haiku
---
NB2 flow_prompt 품질 검토 전문 에이전트.
다음을 체크한다:
- SUBJECT LOCK 누락 (costume_refs 있는 Shot)
- THIS 키워드 누락 (refer-to의 costume_ref)
- CHARACTERS 블록 사용 여부 (직접 등장 secondary_chars)
- 3계층 배치 준수 (CONTEXT→ACTION→CONSTRAINTS)
- 품질 접미사 오용 (4k, masterpiece, HD)
위반 Shot 목록과 구체적 수정 지시를 반환한다.
```

### 4-3. 비용 특성

서브에이전트는 독립 컨텍스트 윈도우에서 실행된다.
서브에이전트의 verbose 출력은 서브에이전트 컨텍스트에만 남고,
**요약만 메인 대화로 반환**된다 → 메인 컨텍스트 보호.

---

## 5. 모델 선택 기준 (2026)

| 모델 | 적합한 작업 | 비용 수준 |
|------|-----------|---------|
| **Claude Opus 4.6** | 복잡한 아키텍처 결정, 다단계 추론, 창의적 판단 | 높음 |
| **Claude Sonnet 4.6** | 대부분의 프로덕션 작업, 스트리밍, 서브에이전트 | 중간 |
| **Claude Haiku 4.5** | 단순 서브에이전트 작업, 배치 처리, 검증 | 낮음 |

**비용 최적화 원칙:**
- Sonnet을 기본으로 사용
- Opus는 복잡한 추론이 필요한 경우만 (STEP 04, 05)
- Haiku는 단순 반복 작업 (STEP 07 shot-record-builder)
- `/model` 명령으로 세션 중간에 전환 가능

---

## 6. Prompt Caching (프롬프트 캐싱)

API를 직접 호출하는 파이프라인(`generate_images.py` 등)에서 유효한 최적화.

- 반복 사용되는 긴 컨텍스트(ANCHOR.md, SKILL.md 전체 등)를 캐시
- **비용 절감**: 캐시된 입력 토큰 → 90% 비용 감소 (Opus: $0.30/1M → $0.03/1M)
- **지연 감소**: 85% 레이턴시 감소
- TTL: 기본 5분, 최대 1시간
- 최소 1,024 토큰 이상의 청크에서만 유효
- 요청당 최대 4개의 캐시 포인트

---

## 7. 도구(Tool) 전략

### 7-1. MCP vs CLI 도구

| 방식 | 컨텍스트 비용 | 권장 상황 |
|------|------------|---------|
| **MCP 서버** | 모든 도구 정의가 컨텍스트 소비 | 전용 기능이 꼭 필요한 경우 |
| **CLI 도구 (gh, aws, gcloud)** | 컨텍스트 소비 없음 | 대부분의 경우 선호 |
| **코드 실행 방식** | 중간 | 복잡한 제어 흐름 필요 시 |

**원칙**: 동일 기능이면 MCP보다 CLI 도구를 선호한다. Claude가 `gh pr create`를 직접 실행하는 것이 GitHub MCP 서버보다 컨텍스트 효율적이다.

### 7-2. Tool Search (on-demand 도구 로딩)

도구가 많을 때 유용한 패턴 — 사용되지 않는 도구 정의를 컨텍스트에서 제거:

```
--enable-tool-search auto:5
```

도구 설명이 컨텍스트의 5% 초과 시 자동으로 on-demand 로딩으로 전환.

---

## 8. 배치(Batch) 처리 패턴

대량의 Shot을 처리하는 경우 (STEP 06 비주얼 디렉팅 등):

```bash
# 섹션별 배치 실행 예시
for section in SECTION01 SECTION02 SECTION03; do
  claude -p "Run STEP 06 visual-director on $section using ANCHOR.md" \
    --allowedTools "Read,Write,Bash(python:*)" \
    --output-format json
done
```

**전략:**
1. 첫 2~3개 Shot으로 프롬프트 검증
2. 검증 완료 후 전체 Section으로 확장
3. `--output-format json`으로 프로그래밍 방식 처리 가능

---

## 9. 회피해야 할 안티패턴

| 안티패턴 | 증상 | 해결책 |
|---------|------|--------|
| **혼합 세션 (Kitchen Sink)** | 무관한 작업 A→B→A 전환 | `/clear`로 작업 간 컨텍스트 리셋 |
| **반복 수정** | 같은 실수를 3번 이상 수정 요청 | 2회 수정 후 `/clear` + 프롬프트 재작성 |
| **비대해진 CLAUDE.md** | Claude가 지시 절반을 무시 | 500줄 이하로 정리; 도메인 지식은 Skill로 이동 |
| **검증 없는 신뢰** | 그럴듯해 보이지만 엣지 케이스 미처리 | 항상 검증 기준 제공 (테스트, 스크린샷, 스크립트) |
| **무제한 탐색** | Claude가 수백 개 파일 읽기, 컨텍스트 포화 | 범위 좁히기 or 서브에이전트에 위임 |
| **막연한 프롬프트** | "코드 개선" 등 | "auth.ts login 함수에 입력 유효성 검사 추가" |

---

## 10. ecowise-pipeline 전용 적용 권장 사항

### 10-1. 즉시 적용 가능

| 상황 | 권장 조치 |
|------|---------|
| SECTION 간 전환 시 | `/clear` 실행 — Shot Record 컨텍스트 축적 방지 |
| STEP 06 실행 전 | Plan Mode로 섹션 전체 전략 수립 → Normal Mode 실행 |
| NB2 flow_prompt 품질 검토 | 서브에이전트 `shot-quality-reviewer` 생성 |
| STEP 04-08 전체 실행 | 단계별 모델 적절 분배 (Opus→STEP04/05, Haiku→07) |

### 10-2. 서브에이전트 추천 구성

```
.claude/agents/
  ├── shot-quality-reviewer.md   # NB2 패턴 오류 탐지 (Haiku)
  ├── anchor-validator.md        # ANCHOR.md 구조 검증 (Haiku)
  └── prompt-optimizer.md        # flow_prompt 최적화 제안 (Sonnet)
```

### 10-3. Skill vs CLAUDE.md 분리 전략

현재 CLAUDE.md에 파이프라인 전체 규칙이 있다면:
- **CLAUDE.md**: 파이프라인 구조 개요 + 기본 실행 방법만
- **SKILL.md**: 단계별 세부 규칙 (현재 방식 유지 ✅)
- **서브에이전트**: 반복되는 검증/리뷰 작업

---

## 참고 소스

- [Claude Code Best Practices](https://code.claude.com/docs/en/best-practices.md)
- [Claude Code Common Workflows](https://code.claude.com/docs/en/common-workflows.md)
- [Claude Code Cost Management](https://code.claude.com/docs/en/costs.md)
- [Claude Code Subagents Guide](https://code.claude.com/docs/en/sub-agents.md)
- [Anthropic Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use)
- [Anthropic Prompt Caching](https://www.anthropic.com/news/prompt-caching)
- [Anthropic Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
