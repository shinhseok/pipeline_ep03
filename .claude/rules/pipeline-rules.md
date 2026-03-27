# Pipeline Rules — YouTube Production Workflow

## 0. 근원적 해결 원칙 (최우선)

**이슈 발생 시 반드시 근원적 해결책을 먼저 고민한다.**

- 특정 shot/파일에 개별 패치(per-shot constraint 추가 등)를 먼저 적용하지 않는다
- 반복되는 이슈는 반드시 시스템 레벨(템플릿, 스크립트, 에이전트 가이드)에서 원인을 찾는다
- "왜 이 이슈가 발생했는가?"를 먼저 규명한 뒤, 동일 이슈가 다른 shot에도 재발하지 않도록 구조적으로 수정한다
- 임시방편 패치는 근원 수정이 불가능한 경우에만 최후 수단으로 사용한다

---

## 1. 적용 범위
이 규칙은 모든 YouTube 영상 제작 프로젝트에 항상 적용된다.
예외 없이 모든 Agent와 모든 단계에서 준수한다.

---

## 2. 프로젝트 초기화 규칙

### 신규 프로젝트 시작 시 Claude는 반드시 아래 순서로 행동한다:
1. 워크스페이스 전체 폴더 구조를 먼저 출력한다
2. `projects/{PROJECT_CODE}/_meta.md` 초안을 생성한다
3. 현재 완료된 단계(보유 파일)를 확인한다
4. 다음 실행할 단계를 제안하고 사용자 승인을 받는다

### PROJECT_CODE 규칙:
- 형식: `CH{2자리 시퀀스}` (예: CH01, CH02)
- 동일 주제 재작업 시 코드 유지, run 버전만 증가

---

## 5. 산출물 출력 형식

응답 첫 줄은 반드시 현재 단계 표기:
`[STEP {번호} | {작업명}]`

---

## 6. 단계 간 연결 규칙

- 이전 단계 파일이 없으면 작업을 시작하지 않고 즉시 요청한다
- 단계 완료 후 다음 단계 핵심 인풋을 3~5줄로 요약한다

---

## 7. Agent별 역할 경계

| Agent | 담당 단계 | 절대 금지 |
|-------|-----------|-----------|
| content-planner (sonnet) | STEP 02 | STEP 03 이후 대본 작성 |
| script-director (opus) | STEP 03 | 창의적 Shot 구성 결정 |
| shot-composer (opus) | STEP 04 | 프롬프트 엔지니어링; 나레이션 태깅 |
| visual-director (opus) | STEP 05 → delta | 캐릭터/소품 일관성 유지 범위 내에서 창의적 장면 연출 + flow_prompt 작성 |
| audio-director (haiku) | STEP 06 → delta | 창의적 결정; 매트릭스 기반 태깅만 |
| merge_records.py | MERGE | 04 base + 05 delta + 06 delta → Shot Record |
| render_storyboard.py | RENDER | 코드 렌더링 (LLM 불필요) |
| youtube-publisher (sonnet) | STEP 11 | 기획안 메타데이터 최종화만; 대본·Shot Record 수정 금지 |
| 수동 | STEP 01, 09, 10 | AI 자동화 불가 |

> STEP 05 + 06은 병렬 실행 가능 (상호 의존성 없음 — 둘 다 04만 읽음).

---

## 8. _meta.md 업데이트 규칙

단계 완료 시마다 `_meta.md`의 STATUS 테이블을 업데이트한다.

상태값:
- `⏳ PENDING` : 미시작
- `🔄 IN PROGRESS` : 진행 중
- `✅ DONE` : 완료
- `🔁 REVISION` : 수정 중
- `🚫 BLOCKED` : 선행 단계 미완료로 대기

---

## 9. 응답 스타일 규칙

- 불필요한 서론 없이 즉시 작업 시작
- 선택지는 번호 옵션으로 제시, 결정 후 진행
- 단계 완료 후 반드시 한 줄 next step prompt로 마무리
- 한국어로 응답 (프롬프트 및 기술 태그는 영어 유지)
- 진행 중 모호한 인풋 발생 시 작업 중단 후 즉시 질문

---

## 11. 모델 버전 고정 규칙

| Agent | 모델 alias | 적용 단계 |
|-------|-----------|-----------|
| content-planner | `sonnet` | STEP 02 |
| script-director | `opus` | STEP 03 |
| shot-composer | `opus` | STEP 04 |
| run-director | `sonnet` | 오케스트레이터 |
| visual-director | `opus` | STEP 05 (서브에이전트) |
| audio-director | `haiku` | STEP 06 (서브에이전트) |
| prompt-auditor | `sonnet` | STEP 05 QA (품질 검토) |
| youtube-publisher | `sonnet` | STEP 11 (YouTube 메타데이터) |
| 스크립트 | — | MERGE, RENDER |

비용 구조: opus 3회 (고비용) → sonnet 3회 (중비용) → haiku 1회 (저비용) → 스크립트 2회 (무료)

---

## 12. 수정 후 의존성 전파 규칙 (Propagation Check)

**에이전트·스킬·규칙 파일을 수정할 때마다** 아래 체크리스트를 반드시 실행한다:

1. **하류 에이전트 전파**: 수정된 출력을 입력으로 사용하는 다음 단계 에이전트에 반영 필요한지 확인
2. **Self-Reflection 업데이트**: 변경된 규칙이 관련 에이전트의 자체 검토 체크리스트에 반영되었는지 확인
3. **pipeline-monitor 업데이트**: 새로운 필수 필드·섹션이 감시 대상(STEP 1~3)에 추가되었는지 확인
4. **run-director 업데이트**: 사전 검증(prerequisite) + 완료 검증(completion verification)에 반영 확인
5. **규칙 파일 동기화**: pipeline-rules.md · pipeline_reference.md 내 모델 alias·섹션 수·필드 목록이 실제 에이전트와 일치하는지 확인
6. **문서 동기화**: CLAUDE.md · README.md 해당 부분 갱신

> ⚠️ 이 체크를 건너뛰면 단계 간 정합성이 깨져 런타임 오류 또는 품질 저하가 발생한다.

---

## 13. 자체 검토 원칙 (Self-Review Rule)

### 시작 전 검토
1. 인풋 파일이 모두 존재하는가
2. 이전 단계 결과물과 설계 충돌이 없는가
3. 파일명·버전·경로 규칙에 맞는가

### 완료 후 검토
1. 산출물 항목이 누락 없이 생성되었는가
2. 다음 단계가 이 파일을 올바르게 사용할 수 있는가
3. _meta.md 업데이트가 필요한가
