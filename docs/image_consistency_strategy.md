# NB2 이미지 일관성 전략

> ⚠️ **LEGACY ARCHIVE** — 이 문서는 v4~v7 마커 시스템 시대의 전략을 기록합니다. 현재 파이프라인은 JSON 템플릿(§9-3)을 사용합니다. 참조 목적으로만 보관.

> 작성일: 2026-03-01
> 대상 모델: Gemini 3.1 Flash Image (Nano Banana 2)
> 목적: 멀티 레퍼런스 이미지 활용 시 캐릭터/스타일 일관성 확보

---

## 1. NB2 멀티 레퍼런스 — 공식 동작 원리

### 1-1. API 전달 구조

```
contents = [라벨1, 이미지1, 라벨2, 이미지2, ..., 텍스트_프롬프트]
```

- **이미지 먼저, 텍스트 마지막** — Google 공식 권장 순서
- 모든 이미지는 하나의 `contents` 블록에 배치
- 각 이미지 직전에 텍스트 라벨을 삽입하여 역할 명시

### 1-2. 수량 및 토큰 예산

| 항목 | 값 |
|------|-----|
| 하드 리밋 | 14장 |
| 이미지당 토큰 비용 | ~1,120 토큰 |
| 입력 토큰 한도 | 65,536 (Firebase) ~ 131,072 (Vertex AI) |
| **실질 품질 최적 구간** | **3~5장** |

- 장수 자체보다 **지시 충돌(conflicting instructions)** 이 품질 저하의 주요 원인
- 이미지가 많을수록 모델이 모든 조건을 동시에 만족시키려다 "평균화"된 결과 생성

### 1-3. 종횡비 결정 규칙

**마지막 이미지의 종횡비가 출력 종횡비에 영향을 준다.**

- `aspect_ratio: "16:9"` 설정으로 명시적 강제
- ~~style_ref 제거됨~~ (2026-03-09 — basic_charater_ref.png가 아트 스타일까지 커버)

### 1-4. 핵심 공식 원칙 (Google DeepMind)

| 원칙 | 설명 |
|------|------|
| **고유 이름 부여** | "assign a distinct name to each character or object" — 각 레퍼런스에 명확한 역할명 |
| **역할 계층(hierarchy) 명시** | 어떤 이미지가 identity / style / composition을 제어하는지 프롬프트에 서술 |
| **360도 캐릭터 시트** | 다각도(Front/3-4/Back) 레퍼런스가 일관성의 골드 스탠더드 |
| **Identity Header 반복** | 매 프롬프트 상단에 정체성 기술 + 하드 네거티브(금지 사항) 반복 |
| **변경은 한 번에 하나씩** | 한 Shot에서 여러 요소를 동시에 바꾸면 identity drift 발생 |

---

## 2. 현재 파이프라인 진단

### 2-1. 현재 API 전달 흐름 (generate_images.py)

```
[character_ref 라벨] → [character_ref 이미지]     ← 우선순위 1
[costume_ref 라벨]  → [costume_ref 이미지]        ← 우선순위 2
[prop_ref 라벨]     → [prop_ref 이미지]           ← 우선순위 3
[텍스트 프롬프트]                                  ← 맨 마지막
```

- 우선순위 정렬 + 이미지-라벨 쌍 구조는 **공식 권장과 일치**
- Phase 1 (레퍼런스 시트 생성)과 Phase 2 (씬 이미지 생성) 라벨을 분리한 것도 적절

### 2-2. IMAGE_LABELS (구현 후 — 2026-03-01)

| 카테고리 | 역할 태그 | 라벨 핵심 내용 | 우선순위 |
|----------|----------|---------------|---------|
| `character_ref` | `[IDENTITY SOURCE]` | 체형·비율 추출, 색상/배경/레이아웃 무시, ONE character, anti-refsheet | 1 |
| `costume_ref` | `[APPEARANCE SOURCE]` | 의상 디자인 + COLOR SWATCH 색상 추출, 체형은 IDENTITY에서 가져옴, ONE character, anti-refsheet | 2 |
| `prop_ref` | `[OBJECT SOURCE]` | 소품 형태·색상·디테일 복제 | 3 |
~~| `style_ref` | `[STYLE SOURCE]` | 선질·해칭 질감만 추출 | 5 |~~ ← 제거됨 (2026-03-09)

### 2-3. 발견된 문제점

| # | 문제 | 심각도 | 설명 | 해결 상태 |
|---|------|--------|------|----------|
| **P1** | 역할 계층(hierarchy) 미명시 | **높음** | 라벨에 계층 지시가 없음 | ✅ 전략 1로 해결 — `[IDENTITY/APPEARANCE/OBJECT/STYLE SOURCE]` 태그 |
| **P2** | 의상 Shot에서 character_ref 누락 | **높음** | CH01에서 2장만 사용, 체형 신호 상실 | ✅ 전략 2+5로 해결 — §6-1 조합 표준 테이블 |
| **P3** | 지시 충돌 가능성 | **높음** | 보일러플레이트에 상충 규칙 공존 | ✅ 전략 3+6으로 해결 — 3계층 역할 분리 |
| **P4** | 배경색 불일치 | 중간 | CH01 전 Shot #F7F2E8 사용 | ⚠️ 규칙 수정 완료, CH01 재생성 필요 |
| **P5** | 템플릿 마커 미사용 | 중간 | 4개 마커 정의만 되고 0회 사용 | ✅ 전략 4로 해결 — 6개 마커, NB2 필수 사용 |
| **P6** | SANDWICH 표정 금지 불일치 | 중간 | 일부 Shot에 1회만 배치 | ✅ 전략 4로 해결 — `{{FACE_END}}` 마커로 자동 적용 |
| **P7** | scene_ref 미사용 | 낮음 | First Rendered Shot Lock 미구현 | — 프로토콜 정의 완료 (§6-5), 실행은 첫 승인 후 |

---

## 3. 개선 전략

### 전략 0: 기본 원칙

> **"더 많은 규칙"이 아니라 "더 명확한 소수의 규칙"으로 일관성을 확보한다.**
>
> - 규칙이 추가될수록 지시 충돌 확률이 높아진다
> - 모든 개선은 "추가"가 아닌 "교체" 또는 "단순화" 방향으로

---

### 전략 1: IMAGE_LABELS에 역할 계층(Hierarchy) 명시

**문제**: 현재 라벨은 "이 이미지가 무엇인지" 설명하지만 "이 이미지에서 무엇을 가져가라"는 계층 지시가 없다.

**개선 방향**: 각 라벨에 역할 계층을 명시적으로 추가

```
역할 계층:
  character_ref → IDENTITY 제어 (체형, 실루엣, 비율, 아트 스타일 포함)
  costume_ref   → APPEARANCE 제어 (의상, 색상, 텍스처)
  prop_ref      → OBJECT 제어 (소품 형태)
```

**라벨 개선안 예시** (character_ref):

```
현재:
"Character body shape reference — this image shows ONE character from
multiple angles for design consistency. Use ONLY for body proportions
and silhouette shape. Generate exactly ONE character in the scene, not
multiple copies. Do NOT reproduce reference sheet layout, panels,
tables, or any multi-view elements. The scene background must be pure
white (#FFFFFF) regardless of this reference:"

개선안:
"[IDENTITY SOURCE] This reference controls the character's body shape,
proportions, and silhouette. Extract ONLY body structure from this
image — ignore colors, background, and layout. Generate exactly ONE
character. Do NOT reproduce the reference sheet format:"
```

핵심 변경:
- `[IDENTITY SOURCE]` 태그로 역할 계층을 선두에 명시
- "controls X" / "Extract ONLY Y" 구문으로 가져갈 것과 무시할 것을 이분화
- 중복/부수적 지시(배경 #FFFFFF 등)를 라벨에서 제거하여 충돌 경감

---

### 전략 2: 의상 Shot에 character_ref 복원

**문제**: 의상 캐릭터 Shot이 `costume_ref`만 사용 → 체형이 costume_ref에만 의존 → 체형 불일치

**개선 방향**: 의상 Shot의 레퍼런스 조합을 2장으로 표준화

```
의상 Shot 표준 조합:
  1. character_ref.jpeg  (우선순위 1) → 체형/실루엣/아트 스타일
  2. costume_ref_X.jpeg  (우선순위 2) → 의상/색상

API 전달 순서:
  [IDENTITY SOURCE] character_ref → [APPEARANCE SOURCE] costume_ref → 텍스트
```

**주의**: 3장이 실질 최적 구간의 하한이므로 추가 이미지(prop_ref 등) 투입은 신중하게

---

### 전략 3: 지시 충돌 감사(Audit) 및 프롬프트 단순화

**문제**: flow_prompt 보일러플레이트가 10~15줄이며 서로 상충 가능한 지시가 공존

**감사 기준**: 아래 패턴이 동일 프롬프트에 공존하면 충돌 위험

| 충돌 패턴 | 예시 |
|-----------|------|
| 색상 지정 vs 레퍼런스 참조 | "charcoal gray #2D2D20" + "replicate colors from costume_ref" |
| 디테일 금지 vs 디테일 요구 | "featureless face" + "expressive pose" |
| 채우기 vs 아웃라인 | "pencil-hatched texture" + "FILLED with solid" |
| 중복 배경 지시 | 라벨의 #FFFFFF + 프롬프트의 #FFFFFF + 마커의 #FFFFFF |

**개선 방향**:
- 보일러플레이트를 **라벨 영역**과 **프롬프트 영역**으로 명확히 분리
- 라벨이 이미 처리하는 지시는 프롬프트에서 제거 (중복 제거)
- 프롬프트는 **해당 Shot만의 고유 연출**에만 집중

```
라벨이 담당하는 것 (generate_images.py):
  - anti-duplication (ONE character)
  - anti-refsheet (레이아웃 복제 금지)
  - 배경색 강제 (#FFFFFF)
  - 역할 계층 (identity / appearance / style)

프롬프트가 담당하는 것 (flow_prompt):
  - 씬 묘사 (동작, 구도, 소품 배치)
  - 캐릭터 고유 특성 (표정 금지, 체색)
  - 감정/분위기
  - 레퍼런스 참조 지시 (refer-to)
```

---

### 전략 4: 템플릿 마커 활성화

**문제**: `{{CHAR_BODY}}`, `{{BG_WHITE}}`, `{{MARGIN_STYLE}}`, `{{NO_REFSHEET}}` 가 정의만 되고 미사용

**개선 방향**: visual-director가 생성하는 flow_prompt에서 마커를 적극 사용하도록 SKILL.md 강화

**기대 효과**:
- 보일러플레이트 텍스트가 **단일 소스**(generate_images.py)에서만 관리됨
- SKILL.md나 ANCHOR 수정 시 보일러플레이트까지 일일이 바꿀 필요 없음
- 프롬프트 길이 감소 → 지시 충돌 확률 감소

**마커 개편 제안**: 전략 1(역할 계층)과 전략 3(충돌 감사) 결과를 반영하여 마커 내용을 재정의

---

### 전략 5: Shot 유형별 레퍼런스 조합 표준화

현재 Shot 유형과 레퍼런스 조합을 명확히 표준화:

| Shot 유형 | 이미지 조합 | 장수 |
|-----------|------------|------|
| **Doodle (캐릭터 없음)** | 레퍼런스 없음 (텍스트 프롬프트만) | 0 |
| **기본 캐릭터** | character_ref | 1 |
| **기본 캐릭터 + 소품** | character_ref + prop_ref | 2 |
| **의상 캐릭터** | character_ref + costume_ref | 2 |
| **의상 캐릭터 + 소품** | character_ref + costume_ref | 2 (prop는 텍스트 묘사) |
| **AI 로봇** | character_ref + ai_robot_ref | 2 |

**핵심 규칙**:
- 캐릭터가 등장하면 **항상** `character_ref` 포함 (체형 앵커)
- **최대 3장**을 표준으로 유지 (NB2 최적 구간)
- 4장 이상이 필요한 경우(의상+소품) → 소품은 텍스트 묘사로 대체하여 3장 유지

---

### 전략 6: 라벨-프롬프트 역할 분리 원칙

라벨과 프롬프트가 각각 담당하는 영역을 명확히 분리:

```
┌─────────────────────────────────────────────────────┐
│  IMAGE_LABELS (generate_images.py에서 자동 삽입)     │
│                                                      │
│  담당: 역할 계층, anti-duplication, anti-refsheet,   │
│        배경색 강제                                    │
│  특성: 모든 Shot에 동일하게 적용되는 시스템 규칙      │
│        Shot마다 달라지지 않음                         │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  TEMPLATE MARKERS (generate_images.py에서 치환)      │
│                                                      │
│  담당: 캐릭터 체색/표정, 마진, 스타일                │
│  특성: Shot 유형에 따라 선택적 적용                   │
│        기본 캐릭터용 / 의상 캐릭터용 분기             │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  flow_prompt 본문 (visual-director가 작성)           │
│                                                      │
│  담당: 씬 고유 연출 (동작, 구도, 소품 배치,          │
│        감정/분위기, refer-to 지시)                    │
│  특성: 매 Shot마다 완전히 다름                        │
│        보일러플레이트 없음 — 순수 연출 내용만          │
└─────────────────────────────────────────────────────┘
```

---

## 4. 구현 결과 (2026-03-01)

> 전 전략 구현 완료. 아래는 실제 변경된 파일과 내역.

| 전략 | 상태 | 변경 파일 | 핵심 변경 |
|------|------|----------|----------|
| **전략 1** | ✅ 완료 | `scripts/generate_images.py` | IMAGE_LABELS에 `[IDENTITY SOURCE]`, `[APPEARANCE SOURCE]`, `[OBJECT SOURCE]`, `[STYLE SOURCE]` 태그 추가. costume_ref의 체형 충돌 지시 제거. character_ref의 중복 배경색 제거. |
| **전략 2** | ✅ 완료 (전략 5와 통합) | `visual-director/SKILL.md` §6-1 | 의상 Shot refer-to에 character_ref 필수 포함 표준화 |
| **전략 3** | ✅ 완료 (전략 6으로 해결) | `visual-director/SKILL.md` §6-6 | 3계층 역할 분리로 충돌 근본 제거. Labels가 처리하는 지시는 flow_prompt에서 제거 원칙 명시 |
| **전략 4** | ✅ 완료 | `generate_images.py` + `SKILL.md` §9, §9-2 | `{{CHAR_BODY_COSTUME}}`, `{{FACE_END}}` 마커 추가. NB2 템플릿 3종 마커 기반으로 재작성. 사용 규칙을 "선택 사용"→"NB2 필수 사용"으로 격상 |
| **전략 5** | ✅ 완료 | `visual-director/SKILL.md` §6-1 | 8종 Shot 유형별 이미지 조합 + refer-to 패턴 표준 테이블. 최대 3장 원칙. |
| **전략 6** | ✅ 완료 | `visual-director/SKILL.md` §6-6 | IMAGE_LABELS(시스템) → TEMPLATE_MARKERS(유형별) → flow_prompt 본문(씬 고유) 3계층 분리 |

### 추가 변경 사항
- `SKILL.md` §11 출력 형식 예시: 마커 기반 + 새 refer-to 패턴(`for body shape`)으로 업데이트
- `generate_images.py` PHASE1_LABELS: 동일한 역할 계층 태그 적용
- `generate_images.py` TEMPLATE_BLOCKS: 총 6개 마커 (`{{CHAR_BODY}}`, `{{CHAR_BODY_COSTUME}}`, `{{BG_WHITE}}`, `{{MARGIN_STYLE}}`, `{{NO_REFSHEET}}`, `{{FACE_END}}`)

### 전략 7~10 (2026-03-03)

| 전략 | 상태 | 변경 파일 | 핵심 변경 |
|------|------|----------|----------|
| **전략 7** | ✅ 완료 | `visual-director/SKILL.md` §9-0-c | SUBJECT LOCK 블록 — costume_refs 있는 Shot 최상단에 인물 정체성 앵커. `{{NO_REFSHEET}}` 직후, 카메라 선언 전 배치. |
| **전략 8** | ✅ 완료 | `visual-director/SKILL.md` §9-0-b | 3계층 CONTEXT/ACTION/CONSTRAINTS — 배치 순서 표에 "계층" 열 추가 + 3계층 원리 노트. |
| **전략 9** | ✅ 완료 | `visual-director/SKILL.md` §9 템플릿 + §11 예시 | 'THIS' 키워드 — `costumes/v1/{인물명}.jpeg — THIS is {인물명}'s costume reference` |
| **전략 10** | ✅ 완료 | `visual-director/SKILL.md` §6-7 | CHARACTERS 블록 — secondary_chars 직접 등장 시 구조화 블록으로 Attribute Bleeding 방지. |

---

## 5. 검증 방법

각 전략 적용 후 아래 체크리스트로 검증:

### 5-1. 단일 Shot 검증

- [ ] 캐릭터 체형이 character_ref와 일치하는가 (빈 모양 실루엣)
- [ ] 표정이 없는 빈 얼굴인가 (눈, 코, 입 없음)
- [ ] 체색이 차콜 그레이(#2D2D20)로 균일한가
- [ ] 배경이 순수 흰색(#FFFFFF)인가
- [ ] 의상 색상이 costume_ref와 일치하는가
- [ ] 레퍼런스 시트 레이아웃이 출력에 나타나지 않는가
- [ ] 캐릭터가 1명만 등장하는가

### 5-2. 크로스 Shot 일관성 검증

- [ ] 동일 캐릭터의 체형이 Shot 간 일관되는가
- [ ] 동일 의상의 색상이 Shot 간 일관되는가
- [ ] 아트 스타일(선질, 해칭)이 Shot 간 일관되는가
- [ ] 소품 외형이 Shot 간 일관되는가

### 5-3. A/B 테스트 방법

1. 동일 Shot 3개를 선택 (기본 캐릭터 / 의상 캐릭터 / 소품 포함)
2. 현재 방식으로 생성 → 결과 A
3. 개선 방식으로 생성 → 결과 B
4. 체크리스트 기준으로 A vs B 비교

---

## 7. 신규 일관성 전략 (2026-03-03)

> 사용자 제공 NB2 일관성 연구 자료를 바탕으로, 기존 전략(§3)에 누락된 4가지 핵심 패턴을 추가.
> 구현 파일: `visual-director/SKILL.md`

---

### 전략 7: SUBJECT LOCK — 피사체 정체성 앵커

NB2는 프롬프트 최상단에서 인물 이름과 핵심 식별자를 읽으면, 이후 모든 씬 묘사에서 해당 이름을 정체성 고정값으로 사용한다.

**적용 조건**: `costume_refs`가 있는 Shot 전체
**생략 조건**: 기본 캐릭터 Shot (character_ref [IDENTITY SOURCE] 라벨로 충분)

**형식:**
```
SUBJECT: {인물명} — compact dark charcoal bean-shaped figure, {의상 핵심 실루엣 1~2가지만}.
Body shape from [IDENTITY SOURCE]. Costume from [APPEARANCE SOURCE].
```

**배치 위치**: `{{NO_REFSHEET}}` 직후, 카메라 선언(⓪) 이전 — [A] CONTEXT 최상단

> SUBJECT LOCK ≠ COSTUME 블록: SUBJECT는 "누구인가"만, 의상 상세는 COSTUME 블록에서 처리.
> 파이프라인 구현: `visual-director/SKILL.md §9-0-c`

---

### 전략 8: 위계적 3계층 (CONTEXT → ACTION → CONSTRAINTS)

NB2는 프롬프트 후반부 제약 조건을 무시하는 경향이 있다 → 제약 조건은 항상 마지막에.

| 계층 | 포함 요소 | 원리 |
|------|----------|------|
| **[A] CONTEXT** | `[thinking:]` + `{{NO_REFSHEET}}` + SUBJECT LOCK + ⓪ 카메라 + `{{ART_STYLE}}` | NB2 첫 파싱 — 씬 정체성 확립 |
| **[B] ACTION** | ①배경 + ②동작 + ②.5`{{FACING_*}}` + ③캐릭터/COSTUME + ③.5소품동작 + ④소품 | 실제 씬 구성 |
| **[C] CONSTRAINTS** | `{{BG_WHITE}}` + `{{MARGIN}}` + `{{FACE_END}}` + refer-to | 최종 필터링 — **반드시 마지막** |

> 파이프라인 구현: `visual-director/SKILL.md §9-0-b` 계층 열 + 3계층 원리 노트

---

### 전략 9: 'THIS' 키워드 — refer-to 의미적 잠금

레퍼런스 이미지가 어느 개체에 적용되는지 명시하여 속성 혼선을 방지한다.

```
costume_ref: costumes/v1/{인물명}.jpeg — THIS is {인물명}'s costume reference
prop_ref:    props/v1/{소품명}.jpeg — THIS prop's appearance reference
```

> `character_ref`는 변경 불필요 (단일 개체 참조이므로).
> 파이프라인 구현: `visual-director/SKILL.md §9` NB2 의상 템플릿 + §11 예시

---

### 전략 10: CHARACTERS 블록 — 속성 혼선(Attribute Bleeding) 방지

2명 이상 직접 등장 시 자유 텍스트 → 구조화 블록으로 전환하여 NB2가 각 캐릭터를 독립 객체로 파싱하도록 유도한다.

**적용 조건**: `secondary_chars`에 직접 등장 캐릭터가 있는 Shot
**제외**: 그림자·실루엣 전용(`[shadow]`, `[crowd_shadow]`) — 기존 텍스트 묘사 유지

```
CHARACTERS:
  SECONDARY ({secondary_chars 값}): "{bean-shaped 명시 묘사}"
  PRIMARY ({costume_refs 인물명}): "{중심 캐릭터 1줄 식별자}"
Exactly {N}({N}) characters appear in this scene.
```

**배치 위치**: ② 동작 슬롯 내 — 씬 묘사 후, COSTUME 블록 직전
> 파이프라인 구현: `visual-director/SKILL.md §6-7`

---

### 전략 11: JSON 구조화 프롬프팅 — 속성 혼선 근본 해결 (2026-03-05)

텍스트 마커(`{{CHAR_BODY}}` 등)를 JSON 템플릿으로 전환하여 프롬프트 속성 충돌을 구조적으로 방지한다.

**해결하는 문제:**
- `expand_templates()` / `TEMPLATE_BLOCKS`가 `generate_images.py`에 미존재 → 마커가 리터럴 텍스트로 NB2에 전달되어 무의미한 토큰
- 텍스트 스태킹 ⓪~⑤에서 속성 경계가 모호 → NB2가 캐릭터와 소품 속성을 혼동

**JSON 구조의 장점:**
- 모든 값이 인라인 — 마커 확장 불필요, 값 누락 불가
- JSON 키가 속성 경계를 명시적으로 분리 (`subject.appearance` ↔ `props.description`)
- `constraints` 배열이 항상 마지막 → 3계층 [C] CONSTRAINTS 위치 자동 강제
- `[SOURCE REFERENCES]` 헤더와 JSON `identifier` 필드의 `costume_label`로 이미지↔캐릭터 매칭 명시

**4종 Variant:** A(의상 캐릭터), B(비캐릭터), C(다중 캐릭터), D(TITLECARD)
> 구현: `visual-director/SKILL.md §9-3`

---

### 미적용 전략 (파이프라인 비적용 이유)

| 전략 | 이유 |
|------|------|
| 문화적 전형 (Wes Anderson 색감 등) | 채널 자체 아트 스타일이 이미 정의됨 |
| 카메라/광학 사양 (Sony A7III, 85mm 등) | 두들 일러스트 — 실사 촬영 아님 |
| 미세 질감 (모공·peach fuzz) | 두들 스타일과 충돌 |
| Thought Signatures (멀티 턴 사고 보존) | 레퍼런스 이미지가 동일 역할 수행 |

---

## 6. 참고 소스

- [Gemini API Image Generation docs](https://ai.google.dev/gemini-api/docs/image-generation)
- [Gemini image generation best practices - Vertex AI](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/gemini-image-generation-best-practices)
- [How to create effective image prompts with Nano Banana - Google DeepMind](https://deepmind.google/models/gemini-image/prompt-guide/)
- [How to Write Gemini Prompts That Keep Subject Identity Consistent - Sider.ai](https://sider.ai/blog/ai-tools/how-to-write-gemini-prompts-that-keep-subject-identity-consistent-across-edits)
- [Generating Consistent Imagery with Gemini - Towards Data Science](https://towardsdatascience.com/generating-consistent-imagery-with-gemini/)
- [Nano Banana 2 announcement - Google Blog](https://blog.google/innovation-and-ai/technology/ai/nano-banana-2/)
- [Nano Banana 2 Input Size Limit Guide](https://blog.wentuo.ai/en/nano-banana-2-input-size-token-limit-specs-guide-en.html)
