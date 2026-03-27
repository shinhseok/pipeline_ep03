# NB2 (Nano Banana 2) 프롬프트 작성 경험 — 인사이트 정리

> ⚠️ **LEGACY ARCHIVE** — 이 문서는 마커 시스템(`{{CHAR_BODY}}` 등) 기반 경험을 기록합니다. 현재 파이프라인은 JSON 템플릿(§9-3)을 사용합니다. 참조 목적으로만 보관.

> 대상 모델: Gemini 3.1 Flash Image (NB2)
> 작성일: 2026-03-03
> 근거: ecowise-pipeline v0.3 영상 제작 이미지 생성 경험 (v4~v6 반복, ~90 Shot)
> 관련 문서: `docs/image_consistency_strategy.md`, `visual-director/SKILL.md`

---

## 개요

이 문서는 NB2를 활용한 두들 애니메이션 이미지 생성 과정에서 발견한 **안티패턴**과 **베스트 프랙티스**를 정리한다.
`image_consistency_strategy.md`가 레퍼런스 이미지 활용 전략을 다룬다면, 이 문서는 **텍스트 프롬프트 작성 규칙**에 집중한다.

---

## 1. 두들 어휘 규칙 — "빛·발광" 표현 금지

### 문제 패턴 (발견: v6 Shot 25, 54, 59, 61, 65, 67, 74, 77, 87)

두들 스타일 프롬프트에 사진/영화적 조명 어휘를 사용하면 두 가지 부작용이 발생한다:

| 부작용 | 설명 |
|--------|------|
| **스타일 불일치** | "glow", "luminous", "radiant" → 포토리얼리스틱 광원 렌더링 유발 |
| **채색 진해짐** | 발광 어휘가 주변 캐릭터에 고대비(high-contrast) 렌더링 적용 → 캐릭터가 기준 Shot보다 어둡게 나옴 |

### 금지 어휘 목록

```
발광/광원 계열:
  glow, glowing, gleam, luminous, radiant, luminance,
  light emanating, illuminated, backlit, halo of light,
  softly lit, warm light, golden light shines on

그림자-오브젝트 혼동 계열:
  shadow blob, shadow mass, dark shadow falling,
  shadow rendered with hatching  ← (그림자≠오브젝트)
```

### 대체 어휘

```
발광 → 두들 선 어휘:
  "warm pencil-stroke cross-hatching marks radiate softly"
  "thin pencil-line rays fan gently outward"
  "crisp clean doodle edges and sharp speed-line marks"
  "doodle circle ring around the object"

어두운 오브젝트 → 해칭 어휘:
  "heavy dark amorphous doodle mass — solid and dense,
   completely filled in with overlapping pencil cross-hatching strokes"
  "cold blue-white tint" (glow 대신)
  "cold blue-white hatching fills" (backlighting 대신)
```

### 핵심 원리

> NB2는 "warm golden light" 같은 어휘를 광원(light source)으로 처리하여
> 주변 픽셀에 고대비 조명 렌더링을 적용한다.
> 두들 스타일은 균일한 연필 해칭으로 명암을 표현하므로, 조명 어휘는 항상 두들 어휘로 치환.

---

## 2. 텍스트 렌더링 금지 패턴

### 2-1. 이미지 내 텍스트 라벨 (발견: v6 Shot 41, 47, 76, 83)

NB2는 프롬프트에 따옴표로 감싸진 문자열을 이미지에 직접 렌더링하려 한다.
한글 텍스트(`"3분 멍 때리기"`, `"AI"`, `"인쇄술"`)도 영문과 동일하게 렌더링 시도 → 흐릿하거나 기형 문자로 출력.

**금지 패턴:**
- `"3분 멍 때리기" 텍스트가 새겨진 아이콘`
- `"Faustian Bargain" 라벨이 달린 저울`
- `"인쇄술" labeled box`

**대체 패턴:**
- `두들 시계 아이콘 (바늘 3시 방향) + 멍한 두들 캐릭터 아이콘`
- `두들 저울 — 별 반짝임 소품 + 무거운 해칭 덩어리`
- `인쇄기 실루엣 두들 아이콘`

### 2-2. 한국어 라벨이 특히 위험한 이유

NB2의 텍스트 렌더링은 로마자 기반 → 한글 라벨은 마치 특수문자처럼 처리되어
더 심한 노이즈가 발생한다. visual-director가 한글 텍스트 라벨을 프롬프트에 포함하면
반드시 시각 아이콘으로 교체해야 한다.

### 2-3. SKILL.md 규칙 위치

- `visual-director/SKILL.md Rule 14`: 이미지 내 텍스트 라벨은 **한국어로 통일** — 영문 텍스트 혼용 금지. 텍스트 없이 표현 가능하면 시각적 대체물 우선
- `shot-composer/SKILL.md §8 규칙 5`: creative_intent에 텍스트 라벨 기술 금지

---

## 3. 배경·마진 마커 필수 적용

### 문제 패턴 (발견: v6 Shot 46, 60)

`{{BG_WHITE}}`와 `{{MARGIN}}` 마커가 누락된 의상 캐릭터 Shot에서:
- 캐릭터 채색이 안 됨 (라벨 + 마커 시스템이 완전하지 않으면 NB2가 기본 렌더링으로 폴백)
- 목도리 색상이 표현 안 됨

**원인 분석:**
- `{{CHAR_BODY_COSTUME}}` 마커만 있고 `{{BG_WHITE}}` + `{{MARGIN}}`이 없으면
  NB2가 CONSTRAINTS 레이어를 완전히 수신하지 못함
- 두 마커의 역할이 서로 다르므로 둘 다 필수

**규칙:**
> 모든 Shot의 image_prompt CONSTRAINTS 레이어에 `{{BG_WHITE}}`와 `{{MARGIN}}`을 반드시 포함.
> `{{BG_WHITE}}` = 배경 흰색 강제, `{{MARGIN}}` = 캔버스 여백 + 아트 스타일 금지 사항
> 두 마커는 항상 세트로 사용.

- `visual-director/SKILL.md Rule 16`에 기록됨

---

## 4. 다중 캐릭터 — 얼굴 특징 혼선 방지

### 문제 패턴 (발견: v6 Shot 43)

`{{CHAR_BODY_MULTI_COSTUME}}`는 "smooth featureless dark oval head"를 전체 캐릭터에 적용하지만,
PRIMARY 캐릭터(해빛)에 대한 명시적 얼굴 금지 문구 없이는 NB2가 눈을 그릴 수 있다.

**원인:**
- ai_robot의 visor slit은 CHARACTERS 블록에 명시되어 있어 얼굴 금지 마커(`{{FACE_END_MULTI}}`)와 충돌
- `{{FACE_END_MULTI}}` 사용 불가 → 마커 대신 PRIMARY 설명에 명시적 텍스트 필요

**해결책: CHARACTERS 블록 PRIMARY에 얼굴 금지 문구 명시**

```yaml
CHARACTERS:
  SECONDARY (ai_robot): "compact bean-shaped figure in smooth gray robot-shell,
    visor slit and flipper arms — ..."
  PRIMARY (eco-sage): "compact dark charcoal bean-shaped figure in olive-green wool scarf,
    completely featureless smooth head — no eyes, no dots, no lines on the face"
Exactly 2(2) characters appear.
```

- `visual-director/SKILL.md Rule 8`에 확장 기록됨

---

## 5. 종이 프레임 트리거 방지

### 문제 패턴 (발견: v6 Shot 70)

카메라 묘사에 "paper surface filling the entire frame" 같은 문구가 있으면
NB2가 크림색/황색 종이 질감 프레임을 렌더링한다 → `{{BG_WHITE}}`와 충돌.

**금지 패턴:**
- `"paper surface filling the entire frame"`
- `"parchment texture covering the background"`
- `"aged paper fills the canvas"`

**대체 패턴:**
- `"Front-facing wide shot, centered composition on pure white"`
- `"pure white background, the object centered in frame"`

---

## 6. 프롬프트 배치 순서 — 3계층 CONTEXT/ACTION/CONSTRAINTS

NB2는 프롬프트 후반부 제약 조건을 무시하는 경향이 있다.
제약 조건은 항상 프롬프트 **마지막**에 배치해야 한다.

```
[A] CONTEXT (정체성 확립)
  → [thinking: high]
  → {{NO_REFSHEET}}
  → SUBJECT LOCK (costume_refs 있는 Shot만)
  → 카메라 앵글/프레이밍
  → {{ART_STYLE}}

[B] ACTION (씬 구성)
  → 배경 묘사
  → 동작/포즈
  → {{FACING_FRONT}} / {{FACING_3Q}}
  → CHARACTERS 블록 (다중 캐릭터 시)
  → COSTUME 블록
  → 소품 동작
  → 소품 배치

[C] CONSTRAINTS (최종 필터 — 반드시 마지막)
  → {{BG_WHITE}}
  → {{MARGIN}}
  → {{FACE_END}} (단일 캐릭터, ai_robot 아닐 때)
  → (refer to: ... )
```

> `image_consistency_strategy.md §7 전략 8` 참조

---

## 7. SUBJECT LOCK — 인물 정체성 앵커

costume_refs가 있는 Shot에서 `{{NO_REFSHEET}}` 직후에 인물 정체성을 1줄로 선언한다.

```
SUBJECT: Eco-Sage — compact dark charcoal bean-shaped figure, olive-green wool scarf with fringed ends.
Body shape from [IDENTITY SOURCE]. Costume from [APPEARANCE SOURCE].
```

**효과:**
- NB2가 프롬프트 파싱 초기에 인물 정체성을 고정
- 이후 복잡한 씬 묘사에서도 체형·의상 혼선 방지

**규칙:**
- SUBJECT에는 "누구인가"만 (의상 상세는 COSTUME 블록에서)
- 기본 캐릭터 Shot (costume_refs 없음): 생략 가능

> `image_consistency_strategy.md §7 전략 7` 참조

---

## 8. 'THIS' 키워드 — refer-to 의미적 잠금

```
(refer to: character_ref.jpeg for body shape,
costumes/v5/main.jpeg — THIS is Main Character's costume reference,
props/v5/printing_press.jpeg — THIS is the printing press reference)
```

**효과:** 다중 레퍼런스 이미지가 있을 때 어떤 이미지가 어떤 개체에 적용되는지 명시
→ NB2가 의상 색상을 다른 캐릭터로 "bleeding"시키는 것 방지

> `image_consistency_strategy.md §7 전략 9` 참조

---

## 9. NB2 품질 안티패턴 요약

| # | 안티패턴 | 증상 | 해결 |
|---|---------|------|------|
| A | 발광/빛 어휘 (`glowing`, `warm light`) | 채색 진해짐, 스타일 불일치 | 두들 해칭 어휘로 교체 |
| B | 텍스트 라벨 (`"AI"`, `"3분 멍 때리기"`) | 기형 문자 노이즈 | 시각 아이콘으로 교체 |
| C | `{{BG_WHITE}}` + `{{MARGIN}}` 누락 | 채색 실패, 색상 없음 | 항상 세트로 포함 |
| D | 다중 캐릭터 PRIMARY 얼굴 금지 누락 | 눈이 그려짐 | CHARACTERS 블록에 명시 |
| E | "paper surface filling the frame" | 종이 질감 프레임 렌더링 | "pure white, centered" 변경 |
| F | 네거티브 지시 (`"no glow"`, `"no shadows"`) | 금지 대상을 오히려 렌더링 | 포지티브 대안으로 교체 |
| G | 제약 조건을 프롬프트 중간에 배치 | 제약 무시됨 | CONSTRAINTS 레이어를 마지막에 |
| H | `solid` 언어 (`"solid dark charcoal gray"`) | prop_ref 존재 시 완전한 솔리드 채움 | "shaded with pencil cross-hatching"으로 교체 |
| I | `[thinking: minimal]` 사용 | 복잡한 장면에서 지시 누락 | `[thinking: high]`으로 변경 |
| J | `{{NO_REFSHEET}}` 누락 | 멀티패널 레이아웃 렌더링 | 모든 씬 Shot에 포함 필수 |
| K | 배경 atmospheric 언어 (`"very faint"`, `"clearly diminishing"`, `"scene brightening"`) | 씬 전체 톤이 연하게 설정 → 캐릭터 채색도 연해짐 | 톤 중립 묘사로 교체 (`"sparse thin doodle outlines"`) |
| L | Bean 체형 왜곡 언어 (`"neck comically elongated as if rubber"`, `"neck bent deeply"`) | 목·팔다리 신장 지시 → bean 일체형 체형 붕괴 | 몸통 기울기·곡선으로 대체 (`"entire body bent deeply forward in a pronounced C-curve"`) |

---

## 10. SKILL.md 규칙 위치 맵

| 인사이트 | 위치 |
|---------|------|
| 두들 어휘 금지 (Rule 15) | `visual-director/SKILL.md` §12 Rule 15 |
| 텍스트 라벨 한국어 통일 (Rule 14) | `visual-director/SKILL.md` §12 Rule 14 |
| BG_WHITE+MARGIN 필수 (Rule 16) | `visual-director/SKILL.md` §12 Rule 16 |
| 다중 캐릭터 얼굴 금지 (Rule 8) | `visual-director/SKILL.md` §12 Rule 8 |
| 배경 atmospheric 언어 금지 (Rule 17) | `visual-director/SKILL.md` §12 Rule 17 |
| Bean 체형 왜곡 언어 금지 (Rule 18) | `visual-director/SKILL.md` §12 Rule 18 |
| creative_intent 텍스트 라벨 금지 | `shot-composer/SKILL.md` §8 규칙 5 |
| SUBJECT LOCK (전략 7) | `visual-director/SKILL.md` §9-0-c |
| 3계층 배치 (전략 8) | `visual-director/SKILL.md` §9-0-b |
| THIS 키워드 (전략 9) | `visual-director/SKILL.md` §9 템플릿 |
| CHARACTERS 블록 (전략 10) | `visual-director/SKILL.md` §6-7 |
| 씬 공간 분석 (§9-0) | `visual-director/SKILL.md` §9-0 |
| 카메라 스테이징 (§9-1) | `visual-director/SKILL.md` §9-1 |

---

## 11. 변경 이력

| 날짜 | 변경 내용 |
|------|---------|
| 2026-03-03 | 문서 초안 작성 (v6 이미지 생성 경험 기반) |
| 2026-03-03 | Rules 14~16 추가 (텍스트 라벨, BG_WHITE 필수, 두들 어휘) |
| 2026-03-03 | 전략 7~10 구현 완료 (SUBJECT LOCK, 3계층, THIS, CHARACTERS) |
| 2026-03-04 | Rule 17 추가 (배경 atmospheric 언어 금지), [thinking: minimal] → [thinking: high] 기본값 변경, Rule 18 추가 (Bean 체형 왜곡 언어 금지), Rule 14 수정 (텍스트 전면 금지 → 한국어 통일) |
