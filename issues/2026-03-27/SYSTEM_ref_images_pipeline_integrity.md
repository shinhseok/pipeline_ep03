# SYSTEM ISSUE: ref_images 파이프라인 정합성 근본 문제

**일자**: 2026-03-27
**심각도**: CRITICAL (시스템 설계 결함)
**영향 범위**: 전체 파이프라인 (STEP 04 → 05 → generate_images.py)
**프로젝트**: CH03 run003 (분석 기준), 모든 프로젝트에 동일 적용

---

## 증상

이미지 생성 시 반복되는 문제:
- 메인 캐릭터가 기본 캐릭터로 표현
- 코 없는 캐릭터에 코가 표현
- 레퍼런스 이미지 참조 누락/불일치
- 동일 유형 버그가 shot 단위로 반복 발생, 개별 패치로 대응 중

---

## 근본 원인 A: generate_images.py가 너무 많은 판단을 함

### 현재 상태

generate_images.py가 "API 전달자" 역할을 넘어서 **11가지 자체 판단 로직**을 내장.
visual_direction 파일이 "최종 프롬프트"가 아니라 "중간 산출물"이 되어버림.

### 판단 로직 목록

| # | 판단 로직 | 행 | 유형 |
|---|-----------|-----|------|
| 1 | has_human:main → main_turnaround 자동 첨부 | 989 | ref 추가 |
| 2 | has_human:anonym → main_turnaround 제거 + character_reference 첨부 | 996 | ref 교체 |
| 3 | style_reference.png 무조건 첨부 | 1009 | ref 추가 |
| 4 | ref_images 비어있으면 ANCHOR 소품 자동 추가 | 1015 | ref 추가 |
| 5 | chain_mode: 이전 shot 이미지 자동 추가 | 1031 | ref 추가 |
| 6 | 3개 이상 ref 시 스타일 전이 방지 텍스트 삽입 | 435 | prompt 변조 |
| 7 | v2/v3 자동 감지 → 추출 방식 분기 | 309 | 파싱 분기 |
| 8 | 확장자 자동 보정 (.jpeg↔.png) | 352 | 경로 은폐 |
| 9 | character_ref → basic_charater_ref 폴백 | 359 | 경로 은폐 |
| 10 | 라벨 자동 분류 (경로 기반 _classify_ref_image) | 162 | 라벨 결정 |
| 11 | thinking_level Flash 미지원 → HIGH 폴백 | 457 | 설정 변조 |

### 결과

- **visual_direction 파일과 실제 API 전달 내용이 다름** → 오류 추적 불가능
- 스크립트의 자동 첨부 로직이 실패해도 visual_direction 파일에는 흔적 없음
- ref_images: [] 빈 배열의 Python falsy 문제 등 코드 버그가 프롬프트 품질에 영향
- 개별 방어 로직을 추가할수록 복잡도 증가 → 새로운 엣지 케이스 발생

---

## 근본 원인 B: shot_composition에서 태그 누락이 대규모로 발생

### 현재 상태

CH03 run003 기준 정합성 검사 결과:

**has_human:main + costume_refs:[] 위반: 31건 / 전체 32건 main shot 중 96.9%**

| Section | 위반 shot 수 | shot 목록 |
|---------|-------------|-----------|
| TITLECARD | 1 | shot00 |
| SECTION00_HOOK | 5 | shot01~04, shot06 |
| SECTION01 | 2 | shot19, shot23 |
| SECTION02 | 6 | shot49, 51~53, 56~57 |
| SECTION03 | 14 | shot59, 63~70, 72, 76, 80, 82~83 |
| SECTION04_OUTRO | 3 | shot86~87, 89 |

유일한 정상: **shot12** (`costume_refs: [stephenson]` — 변장이 있는 유일한 shot)

**has_human:none인데 신체 키워드 존재: 12건** (SR-2 위반 의심)

### 대규모 발생 원인

1. **규칙 모호성**: "해빛 직접 등장: costume_refs: [main]" 규칙에서 `[main]`이 변장명이 아니라 "기본 모습 식별자"라는 것이 직관적이지 않음. shot-composer가 "변장이 없으면 costume_refs가 비어야 한다"로 해석

2. **Self-Reflection 실효성 부재**: SR-1~SR-12까지 12개 체크 항목이 존재하지만 31/32건 위반 → 규칙이 있어도 에이전트가 실행하지 않음. 체크 항목이 많아 주의가 분산됨

3. **PHASE B 병렬 증폭**: 5개 섹션이 병렬 실행 → 1건의 오해가 5개 에이전트에서 동시 발생 → 31건으로 증폭. 병렬 실행은 효율적이지만 오류도 병렬로 증폭됨

4. **검증 시점 부재**: STEP 04 완료 → STEP 05 실행 사이에 자동화된 검증 단계 없음. pipeline-monitor는 수동 호출이라 실행되지 않음

---

## 현재 대응 (임시 — 이 이슈로 인해 추가된 패치들)

### 이번 세션에서 추가된 패치

| 파일 | 변경 | 유형 |
|------|------|------|
| execution-flow.md ⑧항 | "변장 없는 해빛도 costume_refs: [main] 필수" 경고 추가 | 규칙 강화 |
| execution-flow.md SR-1 | "has_human:main이면 costume_refs ≥ 1" 교차 검증 | SR 강화 |
| shot-composer.md 금지 목록 | "has_human:main인데 costume_refs 비어있음" 명시 | 규칙 강화 |
| visual-director/field-rules.md | has_human 기반 ref_images 필수 포함 규칙 | 방어 로직 |
| visual-director.md 실행 절차 | costume_refs:[main] → main_turnaround 매핑 | 방어 로직 |
| visual-director.md Self-Reflection | ref_images 비어있지 않음 체크 | SR 강화 |
| generate_images.py 934행 | ref_images:[] falsy 버그 수정 (is not None) | 코드 버그 |
| generate_images.py 라벨 | main_turnaround, character_reference 전용 라벨 추가 | 방어 로직 |
| prompt-auditor.md A2-B | has_human↔ref_images 교차 검증 | 감사 강화 |
| pipeline-monitor.md STEP 3 | STEP 04/05 교차 검증 CRITICAL | 감사 강화 |

### 문제

이 패치들은 증상 완화일 뿐, 근본 구조를 바꾸지 않음.
- generate_images.py의 판단 로직은 그대로 유지
- SR 규칙을 아무리 추가해도 에이전트가 실행하지 않으면 무의미
- 다음 프로젝트에서 동일 유형 버그 재발 예상

---

## 제안: 구조 개선 방향

### 원칙

> **visual_direction 파일 = 최종 프롬프트. generate_images.py = 단순 전달자.**

### A. generate_images.py 역할 축소

**변경 후 역할**: 최종 프롬프트와 레퍼런스 이미지를 전달받아 API로 전달하고 결과값을 받아옴. 에러 처리 구현.

**제거 대상** (판단 로직 11개):
- ref_images 자동 첨부/교체/제거 전체 (항목 1~5)
- prompt 텍스트 자동 삽입 (항목 6)
- 경로 폴백/보정 (항목 8~9)
- 라벨 자동 분류 (항목 10)

**유지 대상**:
- v3 YAML 파싱 (visual_direction 파일 읽기)
- API 호출 + 에러 처리 (재시도, 타임아웃, rate limit)
- 파일 저장
- 병렬 처리 (workers)

### B. visual_direction이 완전한 최종 프롬프트가 되도록

**ref_images에 모든 참조 이미지를 명시적으로 포함**:
```yaml
ref_images:
  - assets/reference/style/style_reference.png       # style ref
  - assets/reference/style/main_turnaround.jpeg      # 메인 캐릭터
  - 09_assets/reference/props/run003/rocket_locomotive.jpeg  # 소품
```

**라벨도 visual_direction 파일에 기록** (또는 라벨 규칙을 단순화):
```yaml
ref_labels:
  style_reference: "THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:"
  main_turnaround: "THIS main — 이 캐릭터의 체형과 비율을 따라 그려줘:"
  rocket_locomotive: "THIS rocket_locomotive — 이 대상의 형태만 따라 그려줘:"
```

**visual-director가 ANCHOR ref_paths를 읽어 완전한 ref_images 배열을 구성**:
- has_human 분기, style_ref 첨부 등 모든 판단을 visual-director 단계에서 수행
- 결과가 05 파일에 완전히 기록됨 → 오류 추적 가능

### C. shot_composition 정합성 자동 검증

**STEP 04 완료 시 자동 실행되는 검증 스크립트**:
```bash
python scripts/validate_shot_composition.py --project CH03
```

**핵심 교차 검증 규칙**:
- has_human:main → costume_refs ≥ 1
- has_human:anonym → costume_refs = []
- costume_refs의 모든 항목이 ANCHOR에 존재
- prop_refs의 모든 항목이 ANCHOR에 존재
- creative_intent 신체 키워드 → has_human ≠ none

**위반 시 STEP 05 진행 차단** (run-director에서 prerequisite check)

---

## 우선순위

| 순서 | 작업 | 효과 |
|------|------|------|
| 1 | generate_images.py 역할 축소 | 오류 추적 가능, 복잡도 감소 |
| 2 | visual_direction 파일을 완전한 최종 프롬프트로 | 선언과 실행 일치 |
| 3 | validate_shot_composition.py 자동 검증 | STEP 04 품질 보장 |
| 4 | run-director prerequisite에 검증 통합 | 오류 전파 차단 |
