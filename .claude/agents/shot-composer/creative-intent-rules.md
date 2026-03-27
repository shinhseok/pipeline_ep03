# Creative Intent Rules — Shot Composer Reference

> shot-composer §12의 creative_intent 상세 규칙 참조 파일.
> Shot 설계 전 반드시 읽는다.

---

## 1. creative_intent 태그 구조

| 태그 | 기술 내용 | 필수 여부 |
|------|-----------|---------|
| `[공간]` | **밀도 등급(L0~L5)** + 배경 환경 구조 + 서사적 역할 (§10 참조) | 필수 |
| `[소품]` | 소품 위치·크기·상태 (캔버스 내 **위치** 명시 필수 — 누락 시 NB2가 소품 생략 가능) | 소품 있을 때 |
| `[카메라]` | 앵글·구도·프레이밍 + **캐릭터 프레임 점유율**(기본 10-15%, 최대 20%) + **구도 무게 방향** — ⚠️ CU 금지 (disney-principles §14 참조) | 필수 |
| `[조명]` | 주 광원 방향·색온도 + 바닥 그림자 암시 여부 | 필수 |
| `[감정선]` | 뉘앙스 기반 3파트: `"{nuance}. {표정/포즈} — {소품 관계}"`. 통합 연출표 7차원 톤에 맞춰 기술 | 필수 |
| `[채색]` | 채색 계획: 통합 연출표 `color_point` 참조. 캐릭터 1곳 + 소품 0~1곳, **최대 3색** (disney-principles §18 참조) | 필수 |
| `[캐릭터수]` | 등장 캐릭터 수 (군중 포함). 예: `"메인 1명"`, `"메인 1명 + 군중 실루엣 5명"` | 필수 |
| `[이전샷]` | 앞 Shot과의 시각·감정 연결 + **transition_type 명시 필수** | 앞 Shot 있을 때 |

---

## 2. [이전샷] transition_type 목록

| 유형 | 설명 |
|------|------|
| `Scale Shift` | 카메라 거리 급변 (예: WS → CU) |
| `Contrast Cut` | 분위기·색감·구도 무게 급전환 |
| `Match Composition` | 앞 Shot 구도·동작선 연결 |
| `Subject Handoff` | 시선·물체·동선이 다음 Shot으로 넘어감 |
| `Scale Shock` | 인접 shot 간 크기 비율 **3배 이상** 급변. `visual_lead: 2s` 이상 권장 |
| `Mirror Composition` | 두 shot이 거의 같은 구도·크기·자세이나 **오브젝트만 다름**. 시대/맥락 대비 |

### [이전샷] 클로저 의도 기술 (SECTION01~OUTRO 권장)

transition_type 뒤에 **클로저 의도**를 명시한다. "이 두 shot 사이에서 시청자가 무엇을 상상하는가?"

```
[이전샷] Scale Shock — 앞 Shot 기어 12%(고요) → 이번 Shot 기어 70%(압도).
  클로저: 시청자가 기어가 갑자기 눈앞에 다가온 공포를 상상.

[이전샷] Mirror Composition — 앞 Shot 방적기 아래 아이 손 → 이번 Shot 노트북 앞 성인 손.
  클로저: 구도는 같고 오브젝트만 다름 — 시청자가 "250년 전과 지금이 같다"를 스스로 인식.

[이전샷] Contrast Cut — 앞 Shot 여백 85%(자유) → 이번 Shot 여백 15%(질식).
  클로저: 시청자가 "사이에 무슨 일이 있었길래?"를 상상하며 서사에 참여.
```

---

## 3. visual-director 필드 매핑 원칙 (Style Isolation)

creative_intent 태그 → visual-director 필드 변환 시 허용/금지 범위:

| 태그 | 허용 | 금지 |
|------|------|------|
| `[공간]` | 배경 환경 구조·분위기 | 스타일 표현 (`solid fill`, `watercolor wash` 등) |
| `[소품]` | 소품 식별명 + 캔버스 내 위치 | 위치 없는 소품 기술 |
| `[카메라]` | 카메라 거리·앵글·구도 무게 | 캐릭터 신체 묘사·동작 |
| `[조명]` | 주 광원 방향·색온도만 | 렌더링 스타일 (`charcoal fill`, `dense shadow`) |
| `[감정선]` | 시청자 감정 효과 | 렌더링 지시 |

**스타일 표현은 creative_intent 어디에도 사용 금지** — visual-director의 `art_style` 필드가 단독 정의한다.
`composition` 필드는 위치·비율·여백만; `appearance` 필드는 ANCHOR 원문 + 장면 상태만; `action`은 동적 동사만.

---

## 4. [조명] 금지 표현 + 대체

| ❌ 금지 표현 | 문제 | ✅ 대체 |
|------------|------|--------|
| `"warm golden glow"` | 배경 전체 노란빛 오염 | `"Single neutral pencil spotlight directly above the subject only."` |
| `"candlelight"` | 배경 전체 주황빛 오염 | `"Flat neutral ambient light."` |
| `"sunlight through leaves"` | 배경 전체 오염 | `"Soft diffuse top light. No background tint."` |

---

## 5. 콘텐츠 가이드라인 (절대 금지 연출)

다음 연출은 creative_intent에 포함 금지. 발견 즉시 대체 연출로 교체:

| 금지 항목 | 대체 방향 |
|---------|---------|
| 흡연 (파이프, 담배, 전자담배 등) | 찻잔·온기·여유로운 자세로 대체 |
| 음주·음주 연상 소품 | 음료수·주스 등으로 대체 |
| 신체 폭력·충돌 | 충격 심볼(별, 번개)로 간접 표현 |
| 성인 콘텐츠 암시 | 해당 Shot 삭제 또는 중립 표현으로 대체 |

---

## 6. 연속 Shot 소품 일관성 규칙

동일 공간·시간대를 연속으로 묘사하는 Shot (예: 아침 루틴 2~3개 Shot)에서는 **동일 소품을 일관되게 사용**한다.

- Shot1에서 `alarm_clock`을 사용했다면 Shot2에서 `smartphone`으로 교체 금지
- ANCHOR에 등록된 소품 식별명을 동일 시퀀스 내에서 반드시 유지

---

## 7. ANCHOR 미등록 소품 금지

creative_intent에 등장하는 소품은 반드시 ANCHOR Layer 1에 등록되어 있어야 한다.

- 등록되지 않은 소품을 creative_intent에서 처음 언급하면 → 해당 Shot 작성 전 ANCHOR에 먼저 추가
- 특히 비교·진화 Shot(예: 3단계 소품 나열)에서 중간 소품을 누락하지 않도록 주의

---

## 8. secondary_chars 필드 조건

| 조건 | 값 |
|------|----|
| 보조 캐릭터 없음 | `secondary_chars: []` |
| 기본 빈 캐릭터 등장 | `secondary_chars: [bean]` |
| 그림자·실루엣만 | `secondary_chars: [crowd_shadow]` |
| 특정 역할 보조 캐릭터 | `secondary_chars: [monk_scribe, king]` |

---

## 9. Video Hook Shot 추가 필드 (HOOK_MEDIA: video일 때)

```yaml
# SECTION00_HOOK Shot에만 추가
hook_media_type: video
hook_type: song          # 또는 standard
video_duration: 5s
video_engine: veo3
# ⚠️ flow_prompt[start], flow_prompt[end]는 STEP 05 visual-director가 작성
# ⚠️ video_prompt는 STEP 05 visual-director가 작성
```

---

## 10. [공간] 배경 밀도 등급 (L0~L5)

shot-composer는 [공간] 태그에 **밀도 등급(L0~L5)**을 명시한다.
visual-director는 이 등급에 따라 `sempe-ink.yaml` E10의 서술 블록을 사용한다.

### 등급 정의

| 등급 | 이름 | 잉크 밀도 | 배경 요소 | 적합 상황 |
|------|------|-----------|----------|----------|
| **L0** | bare | 0% | 순백. 아무것도 없음 | AWE, ISOLATED |
| **L1** | trace | ~2% | 단일 힌트: 수평선/바닥자국/그림자 | REFLECTIVE |
| **L2** | whisper | ~5% | 환경 편린 2-3개 (풀잎+바닥선 등) | HUMOR, REFLECTIVE |
| **L3** | sketch | ~10% | 단일 구조물 윤곽 (문틀, 나무 등) | TENSION, REVEAL |
| **L4** | scene | ~15% | 다중 구조물 (방 윤곽+가구 암시) | TENSION, REVEAL |
| **L5** | panorama | ~18% | 풍경 스케치 (지평선+건물군+깊이감) | AWE, TENSION |

### 등급 선택 흐름

```
1. emotion_tag 확인 → 적합 등급 범위 파악
2. 구도 아키타입 확인 → VAST/ISOLATED는 L0~L1 선호, PANORAMIC은 L4~L5
3. 서사적 필요성 → 공간이 이야기의 핵심이면 등급 상향
```

### [공간] 기술 형식

```
[공간] L{N}. {환경 키워드} — {서사적 역할}
```

**예시:**
```
[공간] L0. 순백의 여백 — 고독과 경외감 극대화
[공간] L1. 희미한 수평선 — 시간의 흐름 암시
[공간] L2. 풀잎+바닥선 — 전원적 분위기 편린
[공간] L3. 공방 문틀 윤곽 — 밀폐된 공간의 긴장감
[공간] L4. 방 윤곽+가구+창문 — 압도적 환경 속 작은 캐릭터
[공간] L5. 지평선+건물군+길 — 파노라마 속 여정
```

### 등급 미기재 시 (레거시 호환)

기존 [공간] 태그에 등급 없으면 visual-director가 키워드 기반 자동 매핑:

| [공간] 키워드 | 자동 매핑 등급 |
|--------------|--------------|
| "빈 캔버스", 환경 미언급 | L0 |
| "수평선", "바닥선", "그림자" | L1 |
| 환경 편린 2~3개 언급 | L2 |
| 단일 구조물 ("문틀", "나무", "기둥") | L3 |
| 다중 구조물 ("방", "가구", "창문") | L4 |
| 풍경 ("지평선+건물", "파노라마") | L5 |

---

## 10.5. 뉘앙스 기반 7차원 응집 가이드

**emotion_nuance를 선택하면 [감정선]·[공간]·[소품]·[카메라]·[채색]이 자동 응집된다.**

통합 연출표(`sempe-ink.yaml` E11)의 7차원 값을 참조하여 creative_intent를 작성한다.

### [감정선] 기술 형식 (뉘앙스 기반 3파트)

```
[감정선] "{nuance}. {표정/포즈 묘사} — {소품 관계}"
```

**예시:**
```
[감정선] "slapstick. 입이 오벌로 벌어지고 상체가 스프링처럼 튀어오름 — 3배 크기의 소품에 압도당하며 양팔 벌려 허우적"
[감정선] "contemplative. 시선을 아래로 떨구고 S자 곡선으로 서 있음 — 멀리 놓인 작은 소품을 조용히 바라봄"
[감정선] "pressure. 몸통이 찌그러진 듯 압축, 이마에 주름 — 5배 크기의 소품이 위에서 내려누름"
```

### 7차원 응집 체크리스트

뉘앙스 선택 후, creative_intent 각 태그가 동일한 톤을 공유하는지 확인:

```
① [감정선]의 표정/포즈 ↔ 뉘앙스의 face + upper_body + gesture
② [공간]의 밀도 등급 ↔ 뉘앙스의 bg_density
③ [소품]의 크기 대조 ↔ 뉘앙스의 prop_relation
④ [카메라]의 앵글/거리 ↔ 뉘앙스의 camera
⑤ [채색]의 색/위치 ↔ 뉘앙스의 color_point
```

> 재정의 시에도 이 5개 차원이 하나의 톤으로 수렴해야 한다.

---

## 11. 군중·실루엣 가이드라인

### 11.1 금지 용어

| ❌ 금지 | 이유 | ✅ 대체 |
|--------|------|--------|
| "검은 blob" | NB2가 형체 없는 검은 덩어리로 해석 | "어두운 잉크 윤곽선의 콩 캐릭터 실루엣" |
| "잉크 덩어리" | 동일 문제 | "성긴 해칭으로 어둡게 표현한 실루엣" |
| "납작한 형체" | 팔다리 없는 평면 형태로 해석 | "콩 캐릭터 형태(둥근 머리, 짧은 팔다리)" |

### 11.2 실루엣 기본 원칙

- **콩 캐릭터 기본 형태 유지**: 둥근 머리 + 통통한 몸통 + 짧은 팔다리
- **제거 대상**: 얼굴, 의상 디테일, 개별 표정
- **유지 대상**: 체형 비율, 자세(서 있기/앉기/걷기), 머리-몸통-팔다리 구분

### 11.3 크기 대비로 연령·지위 시각화 (필수)

군중 Shot에서 **연령(어른 vs 아이)** 또는 **지위(권력자 vs 약자)** 차이가 서사에 있으면, **밝기(tone)가 아닌 크기(size) 대비**를 1차 수단으로 사용한다.

| 서사적 차이 | ❌ 밝기만 | ✅ 크기 대비 |
|-----------|---------|-----------|
| 어른 vs 아이 | "2명 밝음 + 8명 어두움" | "2명 키 12% + 8명 키 6% (절반 크기)" |
| 권력자 vs 피지배자 | "1명 앞 + 다수 뒤" | "1명 20% + 다수 8% (1/2.5 크기)" |
| 소수 vs 다수 | "N명 밝음 + M명 어두움" | 크기 + 밝기 병행 |

**[캐릭터수] 태그 기술 형식:**
```
[캐릭터수] 어른 2명(12%) + 아이 8명(6%) — 크기 차이로 연령 구분
```

### 11.4 [감정선]에서 실루엣 묘사

```
❌ "나머지는 검은 blob으로 개별성 상실"
✅ "나머지는 성긴 해칭으로 어둡게 표현한 콩 캐릭터 실루엣 — 자세만 보이고 얼굴은 없음"
```

---

## 12. Shot 파일 YAML 예시 (완성본)

```markdown
# shot12.md
SECTION: SECTION02
SHOT_ID: 12
INPUT_REF: 03_script_final_{topic}_v1.md
ANCHOR_REF: 04_shot_composition/{RUN_ID}/ANCHOR.md
MODEL: claude-opus-4-6
FLOW_MODEL: NB2
CREATED: {날짜}

---
```

```yaml
---
shot_id: 12
section: SECTION02
local_id: 03
duration_est: 4s
emotion_tag: REVEAL
emotion_nuance: eureka
pose_archetype: V1

narration_span: |
  구텐베르크는 포도주 압착기를 오래 바라보았다. 바로 이 순간이었다.
scene_type: Doodle-Character
creative_intent: |
  [공간] L3. 어둑한 중세 공방 내부 — 밀폐 공간의 역사적 전율. 돌바닥, 목조 천장 들보.
  [소품] 포도주 압착기 — 캐릭터 키의 2배 높이, 나사 스크류가 중앙 두드러짐. 소품 돌연 명확.
  [카메라] 정면 WS→MCU 전환. 로우앵글.
  [감정선] "eureka. 상체 스프링 상승, 눈 크게 떠지고 입이 벌어짐 — 한 손이 나사를 가리키며 순간 정지"
  [채색] 소품(나사 스크류)에 bright accent 워시 1곳
  [이전샷] Scale Shift — 앞 Shot WS → 이번 MS 급접근.
line_of_action: 역C-curve
silhouette_note: "측면 실루엣, 한 손 가리킴 — 명확히 판독 가능"
prop_refs: [printing_press]
costume_refs: [gutenberg]
secondary_chars: []

asset_path: 09_assets/images/{RUN_ID}/shot12.png
status: ⏳
---
```
