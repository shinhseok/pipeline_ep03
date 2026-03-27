# DESIGN: 4개 태그 재설계 + generate_images.py 역할 축소 + SR 규칙 통합

**일자**: 2026-03-27
**유형**: 설계 개선 (SYSTEM_ref_images_pipeline_integrity.md의 후속)
**영향 범위**: shot-composer, visual-director, generate_images.py, prompt-auditor, pipeline-monitor

---

## 배경

SYSTEM_ref_images_pipeline_integrity.md에서 식별된 근본 문제 3가지의 구체적 개선안.

---

## 1. 4개 태그 역할·규칙 재설계

### 1.1 현행 문제

**`costume_refs`의 이중 역할이 혼란의 근원:**
- 원래 의미: "어떤 변장을 입고 있는가" (stephenson, monk 등)
- 추가된 의미: "변장 없어도 [main] 필수" — 사실상 "캐릭터 ref 식별자"

shot-composer 입장에서 `costume_refs: [main]`은 직관적이지 않음.
"변장이 없는데 왜 costume이 있지?" → 빈 배열로 출력 → 31/32건 위반.

**`has_human`과 `costume_refs`의 관계가 암묵적:**
- has_human = "화면에 사람 형태가 있는가?" (시각적 판단)
- costume_refs = "어떤 의상을 입었는가?" (에셋 참조)
- 변장 없는 기본 해빛은 "의상이 없는" 것이지 "main이라는 의상을 입은" 것이 아님

### 1.2 run003 실측 데이터

| has_human | 건수 | costume_refs 사용 | 위반 (빈 배열) |
|-----------|------|-------------------|---------------|
| main | 32 | **1건** (shot12: [stephenson]) | **31건 (96.9%)** |
| anonym | 18 | 0 | - (정상) |
| none | 41 | 0 | - (정상) |

costume_refs 값 분포:
- `[]` (빈 배열): 90건 (98.9%)
- `[stephenson]`: 1건 (1.1%)

### 1.3 개선안: 각 태그가 하나의 명확한 질문에만 답하도록

| 태그 | 질문 | 답 | 비고 |
|------|------|-----|------|
| `has_human` | 화면에 사람 형태가 있는가? | `main` / `anonym` / `none` | 변경 없음 |
| `costume_refs` | 메인 캐릭터가 어떤 변장인가? | `[]` = 기본 해빛 / `[stephenson]` 등 | **빈 배열 = 기본 해빛 (정상)** |
| `prop_refs` | 어떤 소품이 등장하는가? | ANCHOR 소품명 리스트 | 변경 없음 |
| `secondary_chars` | 보조 인물이 있는가? | `[]` / `[bean]` / `[crowd_shadow]` 등 | 변경 없음 |

**핵심 변경: `costume_refs: [main]` 컨벤션 폐기.**
- `has_human: main` + `costume_refs: []` = 기본 해빛 → `main_turnaround.jpeg` 참조
- `has_human: main` + `costume_refs: [stephenson]` = 변장 → `characters/{RUN_ID}/stephenson.jpeg` 참조
- 현재 run003의 31개 shot이 전부 정상이 됨

### 1.4 ref_images 매핑 규칙 (visual-director 책임)

| has_human | costume_refs | → ref_images에 포함할 캐릭터 ref |
|-----------|-------------|----------------------------------|
| main | `[]` (기본 해빛) | ANCHOR `main_turnaround` |
| main | `[stephenson]` | ANCHOR `stephenson` (characters/ 경로) |
| anonym | `[]` | ANCHOR `character_reference` |
| none | - | 캐릭터 ref 없음 |

### 1.5 추가 정리 사항

**`secondary_chars` "직접 등장" 정의 명확화:**
- creative_intent에 명시적으로 기술된 보조 인물만 기재
- 나레이션에만 언급되는 인물은 제외

**`prop_refs` 형식 통일:**
- STEP 04: 식별명 (ANCHOR에 등록된 이름)
- STEP 05 ref_images: 전체 경로 (ANCHOR ref_paths에서 매핑)
- 두 형식의 차이를 문서에 명시

---

## 2. generate_images.py 판단 로직 → 에이전트 이관

### 2.1 현행 11가지 판단 로직의 필요성 검토

| # | 판단 로직 | 행 | 필요? | 처리 |
|---|-----------|-----|-------|------|
| 1 | has_human:main → main_turnaround 자동 첨부 | 989 | 필요 | → visual-director 이관 (ref_images에 명시) |
| 2 | has_human:anonym → character_reference 자동 첨부 | 996 | 필요 | → visual-director 이관 (ref_images에 명시) |
| 3 | style_reference.png 무조건 첨부 | 1009 | 필요 | → visual-director 이관 (ref_images에 명시) |
| 4 | ref_images 비어있으면 ANCHOR 소품 자동 추가 | 1015 | 불필요 | 삭제 |
| 5 | chain_mode: 이전 shot 이미지 자동 추가 | 1031 | 필요 | 유지 (스크립트 고유 — 순차 실행 시 물리적 파일 전달) |
| 6 | 3개 이상 ref 시 스타일 전이 방지 텍스트 삽입 | 435 | 필요 | → visual-director 이관 (flow_prompt P1에 포함) |
| 7 | v2/v3 자동 감지 | 309 | 불필요 | 삭제 — v3 전용으로 확정. v2 레거시 파싱 코드 전체 제거 |
| 8 | 확장자 자동 보정 (.jpeg↔.png) | 352 | 불필요 | 삭제 — visual-director가 정확한 경로 기재 |
| 9 | character_ref → basic_charater_ref 폴백 | 359 | 불필요 | 삭제 — 레거시 호환 제거 |
| 10 | 라벨 자동 분류 (_classify_ref_image) | 162 | 검토 | 경로 기반 단순 규칙으로 축소, 또는 ref_labels 필드로 이관 |
| 11 | thinking_level Flash 미지원 폴백 | 457 | 필요 | 유지 (API 제약 대응) |

### 2.2 이관 후 generate_images.py 역할

**변경 전**: 중간 판단자 (11가지 판단 + API 호출)
**변경 후**: 단순 전달자 (API 호출 + 에러 처리)

```
1. visual_direction 파일에서 ref_images, flow_prompt, thinking_level 읽기 (v3 전용)
2. ref_images 경로 → 디스크에서 이미지 로드 (없으면 ERROR + 스킵)
3. 라벨 부여 (경로 기반 단순 규칙)
4. API 호출 + 에러 처리 (재시도, rate limit, 타임아웃)
5. 결과 이미지 저장
6. chain_mode 시 이전 이미지 전달
```

### 2.3 visual-director 변경 사항

**ref_images가 완전한 최종 목록이 되도록:**

```yaml
# 변경 전 (현행)
ref_images: []

# 변경 후 (모든 참조 명시)
ref_images:
  - assets/reference/style/style_reference.png
  - assets/reference/style/main_turnaround.jpeg
  - 09_assets/reference/props/run003/rocket_locomotive.jpeg
```

- style_ref: 모든 shot에 포함 (visual-director가 P1에서 "THIS style" 참조하므로 당연)
- main_turnaround / character_reference: has_human 값에 따라 포함
- costume ref / prop ref: ANCHOR ref_paths에서 조회하여 포함

### 2.4 라벨 처리 방안

**Option A: 경로 기반 단순 규칙 유지 (최소 변경)**
- `style_reference` → THIS style 라벨
- `main_turnaround` / `characters/` → THIS {name} 캐릭터 라벨
- `character_reference` → THIS {name} 기본 체형 라벨
- `props/` → THIS {name} 소품 라벨
- generate_images.py에서 파일명 stem 기반으로 자동 분류 (현행 축소판)

**Option B: ref_labels 필드 도입 (완전 명시)**
```yaml
ref_images:
  - assets/reference/style/style_reference.png
  - assets/reference/style/main_turnaround.jpeg
ref_labels:
  style_reference: "THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:"
  main_turnaround: "THIS main — 이 캐릭터의 체형과 비율을 따라 그려줘:"
```

Option A가 변경 범위가 작고, 현행 라벨 시스템과 호환됨. 우선 A로 진행 권장.

---

## 3. SR 규칙 통합 — 12개 → 3그룹

### 3.1 현행 SR-1~SR-12 분석

| SR | 내용 | 위반율 (추정) | 중요도 |
|----|------|-------------|--------|
| SR-1 | costume_refs ↔ has_human 교차 검증 | 96.9% | 최고 |
| SR-2 | has_human ↔ creative_intent 교차 검증 | ~13% | 높음 |
| SR-3 | 복수 캐릭터/포즈 수량 명시 | 낮음 | 중간 |
| SR-4 | 이전 Shot 시각 연속성 | 낮음 | 중간 |
| SR-5 | 물리적 방향 명확성 | 낮음 | 중간 |
| SR-6 | narration_map 동일성 | 낮음 | 높음 |
| SR-7 | 02_planning 호응 | 낮음 | 낮음 |
| SR-8 | 비주얼 모티프 순환 | 낮음 | 낮음 |
| SR-9 | 키 비주얼 정교성 | 낮음 | 낮음 |
| SR-10 | NB2 금지어 없음 | 중간 | 높음 |
| SR-11 | 변환/인과 → 공간 배치 기법 | 낮음 | 낮음 |
| SR-12 | [감정선] 표정 묘사 포함 | 낮음 | 중간 |

**문제**: 12개를 순서대로 체크하라고 하면 에이전트가 앞 3개쯤에서 주의가 분산되고 나머지는 형식적으로 통과시킴. SR-1이 96.9% 위반인 것이 증거.

### 3.2 개선안: 3그룹 재편

**그룹 A: 필수 정합성 (위반 시 저장 불가) — 3개**

```
☐ A-1: has_human 값이 creative_intent와 일치하는가
        - 캐릭터 등장 언급 → main 또는 anonym
        - 신체 키워드(실루엣/군중/손) → anonym (none 금지)
        - 소품/환경만 → none
☐ A-2: narration_span이 narration_map과 동일한가 (변경 금지)
☐ A-3: NB2 금지어 없음 (faint, ghost, afterimage, 4k, masterpiece)
```

> 그룹 A는 3개뿐. 위반 시 파일 저장 불가. 에이전트가 집중할 수 있는 분량.

**그룹 B: 연출 품질 (위반 시 경고) — 4개**

```
☐ B-1: 이전 Shot과 시각 연속성 명시 ([이전샷] 태그)
☐ B-2: 동일 카메라/구도/emotion 3연속 아님
☐ B-3: [감정선]에 구체적 표정 묘사 포함
☐ B-4: 변환/인과 관계 → 공간 배치 기법 사용
```

> 그룹 B는 위반해도 진행 가능. 품질 향상용.

**그룹 C: 전체 밸런스 (섹션 완료 후 1회) — 4개**

```
☐ C-1: 02_planning 내러티브 구조와 emotion_tag 분포 호응
☐ C-2: 비주얼 모티프 변형·순환
☐ C-3: 키 비주얼 Shot 정교성
☐ C-4: 복수 캐릭터 수량 명시
```

> 그룹 C는 shot 단위가 아니라 섹션 완료 후 1회만 실행. 개별 shot에서 매번 체크하지 않음.

### 3.3 SR-1 (costume_refs 교차 검증) 처리

**문제 1의 태그 재설계에 의해 SR-1은 불필요해짐:**
- `costume_refs: []` = 기본 해빛 (정상)
- `has_human: main` + `costume_refs: []`는 위반이 아님
- 대신 A-1 (has_human ↔ creative_intent)이 핵심 검증을 담당

---

## 3가지 문제의 상호 관계

```
문제 1 (태그 재설계)
  → costume_refs: [] = 기본 해빛 (정상)
  → has_human이 ref_images 결정의 유일한 키
  → SR-1 불필요 → 문제 3의 그룹 A에서 제외

문제 2 (스크립트 → 에이전트 이관)
  → visual-director가 ref_images를 완전히 구성 (style_ref 포함)
  → generate_images.py는 단순 전달자
  → visual_direction 파일 = 최종 프롬프트 → 오류 추적 가능

문제 3 (SR 규칙 통합)
  → 그룹 A 3개만 필수 (저장 불가)
  → 에이전트 집중도 향상
  → 그룹 C는 섹션 완료 후 1회 → shot 단위 부담 감소
```

---

## 수정 대상 파일 (예상)

| 파일 | 변경 내용 |
|------|-----------|
| `pipeline_reference.md §14` | costume_refs 설명 변경: "빈 배열 = 기본 해빛" |
| `CLAUDE.md` | costume_refs: [main] 컨벤션 제거, ref_images 완전 명시 원칙 추가 |
| `shot-composer/execution-flow.md` | ⑧항 costume_refs 규칙 변경 + SR 3그룹 재편 |
| `shot-composer.md` | 금지 목록에서 "has_human:main + costume_refs:[]" 제거 |
| `visual-director.md` | ref_images 완전 구성 책임 명시 (style_ref, 캐릭터 ref 포함) |
| `visual-director/field-rules.md` | has_human → ref_images 매핑 테이블 업데이트 |
| `visual-director/self-check-per-shot.md` | ref_images 완전성 체크 강화 |
| `generate_images.py` | 자동 첨부 로직 제거 (1~4, 6, 8~9), 단순 전달자로 축소 |
| `prompt-auditor.md` | A2-B 검증 기준 변경 (costume_refs:[] 정상 처리) |
| `pipeline-monitor.md` | STEP 04 교차 검증 기준 변경 |

---

## 우선순위

| 순서 | 작업 | 효과 |
|------|------|------|
| 1 | 태그 재설계 (costume_refs:[] 정상화) | 31건 위반 즉시 해소, 규칙 직관성 |
| 2 | SR 3그룹 재편 | 에이전트 집중도 향상, 필수 검증 보장 |
| 3 | visual-director ref_images 완전 명시 | 최종 프롬프트 = visual_direction 파일 |
| 4 | generate_images.py 역할 축소 | 오류 추적 가능, 복잡도 감소 |
