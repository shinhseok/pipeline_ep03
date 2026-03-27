# ANCHOR 생성 규칙 (§9) + 출력 템플릿

> shot-composer.md의 §9, §12 ANCHOR 관련 섹션 참조 파일.
> STEP 0 (C)와 STEP 2에서 이 파일을 읽어 ANCHOR를 작성한다.

---

## §9. Character & Prop ANCHOR 생성 규칙

### ANCHOR 역할
해빛 캐릭터, 인용 인물 변장, 핵심 소품의 텍스트 묘사구를 전역 단일 소스로 정의한다.
STEP 05 (visual-director)는 이 ANCHOR를 읽어 Flow 프롬프트를 작성한다.

### REF PATH REGISTRY (필수)
ANCHOR 파일에 `[REF PATH REGISTRY]` 섹션을 반드시 포함한다. 채널 공통 레퍼런스(style_ref, main_turnaround, character_reference)와 프로젝트별 캐릭터/소품의 실제 파일 경로를 YAML로 정의한다. 모든 하류 에이전트(visual-director)와 스크립트(generate_images.py)는 이 레지스트리에서 경로를 참조한다.

```yaml
ref_paths:
  # 채널 공통
  style_ref: assets/reference/style/style_reference.png
  main_turnaround: assets/reference/style/main_turnaround.jpeg
  character_reference: assets/reference/style/character_reference.jpeg
  style_yaml: assets/reference/style/sempe-ink.yaml
  # 프로젝트별 (Phase 1 생성 후 채움)
  {entity_name}: {path}
```

### 인용 인물 변장 묘사 규칙
- 캐릭터 기본 형태(강낭콩 실루엣, 다크 차콜 그레이, 얼굴 없음) 유지
- 해당 인물을 연상시키는 **소품·의상·외형 요소만** 추가 (안경, 수염, 모자, 가운 등)
- 실루엣 자체는 절대 변형하지 않음

### 소품 ANCHOR 묘사 규칙
- 단순 명사 금지: `a telescope` → `an antique 17th-century brass maritime telescope`
- 시대·재료·크기·특징을 포함한 정밀 묘사구 작성
- 모든 Shot에서 조사 하나 틀리지 않고 동일하게 사용 → 시각 일관성 확보

### 역사적 인물·시대 배경 고증 규칙

스크립트에 역사적 인물, 시대적 직업, 특정 문화권 인물 또는 시대 배경이 등장하는 경우:
ANCHOR 작성 전에 **웹 검색으로 시각적 고증 리서치를 반드시 수행**한다.

#### 리서치 트리거 조건 (하나라도 해당되면 필수)

| 조건 | 예시 |
|------|------|
| 실존 역사 인물 | 구텐베르크, 다 빈치, 뉴턴 |
| 특정 시대 직업 | 15세기 필사 수도사, 르네상스 금속 장인 |
| 문화권 특유 의상 | 조선 시대 갓, 중세 유럽 성직자 수도복 |
| 역사적 도구·작업 과정 | 금속활자 주조, 중세 채색 필사, 포도주 압착 |

#### 리서치 범위

1. **인물 외형**: 초상화·조각상·시대 기록에서 특징적 외모
2. **시대 의상**: 계층·직업·지역에 맞는 실제 복식 구성 요소
3. **작업 도구·환경**: 해당 직업 종사자가 실제 사용한 도구
4. **특징적 자세·동작**: 도구를 쥐는 방식, 작업 특유의 신체 자세

#### 고증 결과 반영 방법

- **ANCHOR Layer 1** 묘사구에 리서치 결과 직접 반영
- **ANCHOR Layer 2** Phase 1 프롬프트에 역사적으로 정확한 외형 묘사 포함
- **creative_intent**에 해당 직업의 고유 도구·자세 사용
- **오해 유발 요소 사전 차단**: 범용 오브젝트가 다른 직업과 혼동될 수 있으면 해당 직업 고유 도구로 교체

| 구분 | 잘못된 설계 | 올바른 설계 |
|------|------------|------------|
| 구텐베르크 | 큰 구리 냄비 앞에 집게 → **요리사 연상** | 소형 주형틀(hand mold) + 소형 도가니 → **금속 주조** |
| 중세 수도사 | 일반 책상에 펜 → **사무원 연상** | 경사진 필사 책상(lectern), 깃털 펜, 양피지 |

리서치 결과를 `anchor_research.md`로 별도 저장: `04_shot_composition/{RUN_ID}/anchor_research.md`

### ANCHOR 대상 선별 기준 (Phase 1 대상)
에피소드 내 **3회 이상 등장** OR **시대적 디테일이 정밀해야 하는 소품** OR **복잡한 변장**

### 반복 등장 비의상 캐릭터 ANCHOR 등록 규칙 ⚠️

대본에서 **2회 이상 등장**하는 독립 캐릭터(AI 로봇, 비서, 의인화 오브젝트 등)는 ANCHOR에 등록.

| 등록 위치 | 기재 내용 |
|-----------|----------|
| **Layer 1** | 텍스트 묘사구 (`[Character N: {이름}]`) |
| **Layer 2** | Phase 1 사전 렌더링 프롬프트 (**Type: character_prop** 템플릿 사용) |

> 해당 캐릭터가 등장하는 Shot의 `prop_refs`에 레퍼런스 파일명을 기재 (costume_refs가 아님).
> **단, generate_images.py는 `character_prop` 타입 파일을 자동으로 CHARACTER SOURCE 레벨로 격상하여 처리한다.**
> visual-director는 SOURCE REFERENCES에 `[CHARACTER SOURCE: {name}]` 라벨을 사용한다.

### Phase 1 레퍼런스 이미지 형식

**기본값: 턴어라운드 시트 (Turnaround Sheet) — 전체 타입 공통**

> ⚠️ 단일 포즈(Single-Pose)는 **폐기**. 실험 결과, 턴어라운드 시트가 NB2의 캐릭터/소품 재현 정확도를
> 크게 향상시키는 것으로 확인됨 (넥커치프→셔츠 오인식 문제 해결, 앞뒤 구분 가능).
> 씬 이미지에 시트 레이아웃이 재현되는 문제는 flow_prompt에서 장면 묘사로 방지.

| 형식 | 뷰 구성 | 사용 조건 |
|------|---------|-----------|
| **캐릭터 턴어라운드 (기본)** | 정면/3·4/측면/후면 (수평 1줄 4개) | 모든 costume |
| **소품 턴어라운드 (기본)** | 정면/측면/상면/3·4뷰 (수평 1줄 4개) | 모든 prop |
| ~~단일 포즈 (폐기)~~ | ~~3/4 뷰 전신 1장~~ | ~~사용 금지~~ |

**캐릭터 턴어라운드 뷰 규칙:**
| 뷰 | 보여주는 것 |
|----|------------|
| 정면 (Front) | 얼굴 정면, 의상 앞면 디테일 |
| 3/4뷰 (Front 3/4) | 약간 우측으로 돌린 자세 |
| 측면 (Side) | 완전한 우측 프로필 |
| 후면 (Back) | 완전한 뒷모습, 얼굴 안 보임, 엉덩이 라인 살짝 |

**소품 턴어라운드 뷰 규칙:**
| 뷰 | 보여주는 것 |
|----|------------|
| 정면 (Front) | 소품의 주요 면 — 가장 특징적인 앵글 |
| 측면 (Side) | 깊이, 두께, 메커니즘 구조 |
| 상면 (Top-down) | 위에서 본 평면 구조, 부품 배치 |
| 3/4뷰 | 입체감, 전체 구조 파악 |

**공통 규칙:**
- **순수 이미지**: 텍스트 라벨, COLOR SWATCH STRIP, 색상명, Hex 코드 일체 금지
- 채색 없이 잉크 라인만 (턴어라운드 시트는 형태 참조용)
- 모든 뷰에서 동일 대상, 동일 비율, 높이 정렬
- 안티-텍스트 문장 필수: "텍스트, 라벨, 화살표, 주석은 넣지 마."

**API content 배열 구조 (Phase 1):**

캐릭터 생성 시:
```
THIS {base_character} — 이 캐릭터의 체형과 드로잉 스타일을 기반으로 그려줘:
<base_character 이미지 — 채널 앵커 캐릭터 (assets/reference/style/character_reference.jpeg)>

<프롬프트>
```

소품 생성 시:
```
THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:
<style_reference.png — 캐릭터 없는 앵커 이미지 (assets/reference/style/style_reference.png)>

<프롬프트>
```

> 캐릭터는 character_reference.jpeg(체형+스타일)를, 소품은 style_reference.png(스타일만)를 참조.
> style_ref는 반드시 **캐릭터가 없는** 이미지를 사용 (캐릭터 오염 방지).

**NB2 서술형 프롬프트 규칙 (v3 — 턴어라운드 시트용):**

1. **구조적 태그 금지**: `[thinking:]`, `TASK:`, `[SOURCE REFERENCES]`, JSON 구조 사용 금지 — 순수 서술형만
2. **의상 묘사 = 순수 외형만**: 외형 아이템 나열만. 기능 설명·스타일 지시 혼입 금지
3. **하의 커버리지**: 상의 아이템은 반드시 "엉덩이까지 자연스럽게 덮는" 표현 추가
4. **진한 색상 톤 다운**: `deep crimson` → `muted crimson`, `bright gold` → `soft gold`
5. **앞뒤 구분 포인트**: 캐릭터의 경우 앞(의상 앞면 디테일)+뒤(엉덩이 라인+의상 뒷면 디테일) 반드시 명시
6. **스타일 값 참조**: `{style.X}` 플레이스홀더는 ANCHOR.md 헤더 `STYLE:` 값 → `assets/reference/style/{STYLE}.yaml` YAML 키 참조

**이미지 분석 활용 규칙:**
- 해당 캐릭터의 실제 이미지 자료가 있으면 → 이미지를 분석하여 시각적 특징 추출 → 턴어라운드 프롬프트에 반영
- 이미지 분석 시 추출 대상: 의상 구성, 색상 톤, 특징적 액세서리, 체형 비율

**채널 공통 턴어라운드 시트 (Phase 1 생성 제외):**

아래 2종은 채널 레벨 에셋으로 이미 존재하므로, **별도 지시가 없는 한 ANCHOR Layer 2에 포함하지 않는다.**
Phase 1 생성 대상에서 자동 제외되며, 씬 이미지 생성 시 자동 첨부된다.

| 에셋 | 경로 | 용도 |
|------|------|------|
| 메인 캐릭터 (넥커치프) | `assets/reference/style/main_turnaround.jpeg` | `has_human: main` + `costume_refs: []` Shot에 visual-director가 ref_images에 포함 |
| 군중 캐릭터 (익명) | `assets/reference/style/crowd_turnaround.jpeg` | `has_human: anonym` + 군중 Shot에 자동 첨부 |

> 재생성 필요 시: `python scripts/generate_main_turnaround.py --overwrite --target main|crowd|all`

- ANCHOR Layer 2에는 **변장 costume** (artisan, factory_worker 등)과 **소품**만 기재
- 캐릭터 참조: `assets/reference/style/character_reference.jpeg`, 소품/character_prop 참조: `assets/reference/style/style_reference.png`

---

## §12. ANCHOR 출력 형식

### ANCHOR 파일 — `04_shot_composition/{RUN_ID}/ANCHOR.md`

```markdown
# ANCHOR.md
ROLE: Global Character Costume & Prop Anchor Dictionary
INPUT_REF: 03_script_final_{topic}_v1.md
MODEL: claude-opus-4-6
FLOW_MODEL: {NB-Pro | NB2}
ESTIMATED_DURATION: {N}초
MIN_SHOTS: {N}개
CREATED: {날짜}

---

## [Global Visual Anchor — Layer 1: 텍스트 묘사구]

- **[Prop 1: {소품명}]**: `{정밀 텍스트 묘사구 — 영어}`
- **[Character 1: {인물명}]**: `{기본 바디 설명 + 의상·소품 묘사구 — 영어}`

## [Global Visual Anchor — Layer 2: Phase 1 턴어라운드 시트 프롬프트]

> **API content 배열**: [ref_label + ref_image, 프롬프트] 순서로 전달.
> 캐릭터는 character_reference.jpeg 참조, 소품/character_prop은 style_reference.png 참조.

Type: prop
Filename: {소품명}.jpeg
Style: {STYLE} (from ANCHOR.md header → assets/reference/style/{STYLE}.yaml)
ref_images: []
ref_label: "THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:"
ref_file: assets/reference/style/style_reference.png
thinking_level: high
Flow 프롬프트:
```
THIS style의 드로잉 스타일로, {소품명}의
소품 턴어라운드 시트를 그려줘.

수평 한 줄로 4개 뷰를 나란히 배치:
1. 정면 (Front) — {정면에서 보이는 핵심 구조}
2. 측면 (Side) — {측면에서 보이는 핵심 구조}
3. 상면 (Top-down) — 위에서 내려다본 구조
4. 3/4뷰 — 약간 위에서 비스듬히, 입체감과 전체 구조

{소품 특징 상세 — 부품 5개 이상, 재질·촉감 언어}

모든 뷰에서:
- 동일한 소품 — 같은 형태, 같은 비율
- 높이 정렬
- 채색 없이 잉크 라인만

순백 배경. 텍스트, 라벨, 화살표, 주석은 넣지 마.
```

Type: costume
Filename: {인물명}.jpeg
Style: {STYLE} (from ANCHOR.md header → assets/reference/style/{STYLE}.yaml)
ref_images: []
ref_label: "THIS main — 이 캐릭터의 체형과 드로잉 스타일을 기반으로 그려줘:"
ref_file: assets/reference/style/character_reference.jpeg
thinking_level: high
Flow 프롬프트:
```
THIS main의 드로잉 스타일과 체형을 기반으로,
{캐릭터 설명} 캐릭터의 턴어라운드 시트를 그려줘.

수평 한 줄로 4개 뷰를 나란히 배치:
1. 정면 (Front) — 얼굴이 정면을 향해
2. 3/4뷰 (Front 3/4) — 약간 우측으로 돌린 자세
3. 측면 (Side) — 완전한 우측 프로필
4. 후면 (Back) — 완전한 뒷모습, 얼굴 안 보임, 엉덩이 라인 살짝

모든 뷰에서:
- THIS main과 동일한 콩 체형 — 같은 머리/몸 비율
- 똑바로 선 자세 (자연스러운 차렷)
- 머리/어깨/발 높이 정렬
- 캐릭터 구분 포인트: {고유 의상/액세서리} ({워시 색} 유일한 색)
- 앞: {앞에서 보이는 특징}
- 뒤: {뒤에서 보이는 특징 — 앞과 반드시 다르게, 엉덩이 라인 포함}

순백 배경. 텍스트, 라벨, 화살표, 주석은 넣지 마.
```

Type: character_prop
Filename: {캐릭터명}.jpeg
Style: {STYLE} (from ANCHOR.md header → assets/reference/style/{STYLE}.yaml)
ref_images: []
ref_label: "THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:"
ref_file: assets/reference/style/style_reference.png
thinking_level: high
Flow 프롬프트:
```
THIS style의 드로잉 스타일로, {캐릭터명}의
소품 턴어라운드 시트를 그려줘.

수평 한 줄로 4개 뷰를 나란히 배치:
1. 정면 (Front) — {정면에서 보이는 핵심 구조}
2. 측면 (Side) — {측면에서 보이는 핵심 구조}
3. 상면 (Top-down) — 위에서 내려다본 구조
4. 3/4뷰 — 약간 위에서 비스듬히, 입체감과 전체 구조

{캐릭터 외형 아이템만 나열}

모든 뷰에서:
- 동일한 엔티티 — 같은 형태, 같은 비율
- 높이 정렬
- 채색 없이 잉크 라인만

순백 배경. 텍스트, 라벨, 화살표, 주석은 넣지 마.
```

```

> **NB2 v3 서술형**: 스타일 값은 `assets/reference/style/{STYLE}.yaml`에서 읽음. `{style.X}`는 YAML 키 참조. 구조적 태그·JSON 사용 금지.

### 리서치 파일 — `04_shot_composition/{RUN_ID}/anchor_research.md`

```markdown
# anchor_research.md
ROLE: Historical Visual Research Documentation
CREATED: {날짜}

## 리서치 트리거 항목

| 유형 | 항목 | 트리거 | 상태 |
|------|------|--------|------|

## 항목별 리서치 결과

### [{type} N: {name}]
**검색 쿼리:** ...
**핵심 발견:** ...
**ANCHOR Layer 1 반영 내용:** ...
```
