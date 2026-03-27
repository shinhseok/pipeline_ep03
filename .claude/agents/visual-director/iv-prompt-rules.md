# iv_prompt Rules — Visual Director Reference (Veo 3 I2V)

---

## 대원칙: Canvas vs Director

이미지는 이미 **Canvas**(화면 구성 — 구도, 색, 배치, 인물 외형)를 완성했다.
iv_prompt는 **Director**(감독)로서 **주체의 행동**, **카메라 움직임**, **환경 변화**를 지시한다.

> ❌ 이미지에 이미 있는 씬·배경·인물 외형을 다시 묘사하지 않는다
> ✅ "주체가 무엇을 하는가", "카메라가 어떻게 움직이는가"에 집중한다

Veo 3 I2V는 입력 이미지의 스타일(스케치/일러스트)을 잘 보존한다.
스타일 보존을 별도 지시할 필요 없다 — **동작을 잘 지시하면 스타일은 따라온다.**

---

## iv_prompt 구조 (Veo 3 I2V, 영어)

```
[thinking: low/high]

[CAMERA]
{카메라 움직임. 시네마틱 동사 사용. 1문장.}

[ACTION]
{주체가 무엇을 하는가. 구체적 동사 + 방향 + 속도. 2~3문장.}

[ENVIRONMENT]
{배경의 미세 변화. 1문장. 없으면 None.}

[AUDIO]
SFX: {효과음}
Ambient: {배경음}
Duration: {초}s
```

---

## [ACTION] — 주체의 행동이 핵심

### 원칙: "주체가 무엇을 하는지" 구체적으로 지시

Veo는 [ACTION]에서 주체의 동작을 읽고 이미지를 움직인다.
**"무엇을 하지 마라"가 아니라 "무엇을 하라"**로 작성한다.

### Bad vs Good

```
❌ Bad: "The sketch remains still. The character breathes."
   → Veo가 할 일이 없어서 자체 판단으로 종이 넘김/3D 전환 추가

❌ Bad: "A sad scene with a lonely character."
   → 상태 묘사 — Director가 아닌 Canvas 역할

✅ Good: "The character slowly turns their head to the right,
   then lowers their gaze toward the object at their feet."
   → 구체적 동사 + 방향 + 시퀀스

✅ Good: "One arm rises slightly as the character shifts weight
   to the back foot. The neckerchief catches a faint draft."
   → 미세하지만 의미 있는 동작
```

### shot-composer [감정선] → [ACTION] 변환

shot-composer의 `[감정선]` 모션 아크(시작→정점→여운)를 읽고, **구체적 행동으로 변환**한다.

| [감정선] 모션 아크 | iv_prompt [ACTION] |
|-------------------|-------------------|
| "고개를 천천히 올리기 시작 → 기어 끝 인식 → 한 발 뒤로" | "The character slowly lifts their head upward. At the apex, the gaze locks on the towering object. One step backward, shoulders drawing inward." |
| "팔짱 끼고 서 있음 → 어깨 으쓱" | "The character shifts weight to one side, then one shoulder lifts in a slow shrug." |
| "S자 곡선으로 서서 아래를 바라봄" | "The character's head dips gently downward. Weight settles onto one leg. A slow exhale shifts the posture." |
| "정적, 사색" | "The character turns their head slightly to the side, then returns to center. A gentle weight shift." |

### emotion_tag별 행동 패턴

| emotion_tag | 권장 행동 (미세하지만 의미 있는) |
|-------------|------------------------------|
| **HUMOR** | 고개 갸웃, 어깨 으쓱, 시선 이동, 한 발 무게 이동 |
| **REFLECTIVE** | 고개 숙임, 시선 아래로, 느린 자세 변화, 손 위치 미세 조정 |
| **AWE** | 고개 천천히 올림, 한 걸음 뒤로, 어깨 경직, 시선 상향 고정 |
| **REVEAL** | 갑작스러운 시선 이동, 고개 들어올림, 한 팔 미세하게 올림 |
| **TENSION** | 어깨 움츠림, 무게 중심 낮아짐, 고개 미세하게 숙임, 정적 후 미동 |

### has_human별 전략

| has_human | [ACTION] 초점 | 예시 |
|-----------|--------------|------|
| **main** | 캐릭터 동작 — 고개/시선/자세/무게 변화 | "The character turns head to the right, then lowers gaze" |
| **anonym** | 실루엣 동작 — 무게 이동, 미세 움직임 | "One silhouette shifts weight forward. Another turns slightly." |
| **none** | 소품/환경 동작 — 빛 이동, 먼지, 미세 움직임 | "A faint glint of light moves along the rail surface" |

### 동작 강도 가이드

| 레벨 | 표현 | 적합 상황 |
|------|------|----------|
| **미세** | turns head, shifts weight, gaze moves | REFLECTIVE, breath |
| **가벼운** | one arm rises, leans forward, takes one step | HUMOR, standard |
| **보통** | lifts head upward, steps backward, shoulders draw in | AWE, REVEAL |

> ⚠️ "보통" 이상의 과격한 동작(springs, flails, arches, contorts)은 캐릭터 외형 변형을 유발하므로 금지.

### 모션 아크 시간 배분

| clip_rhythm | 아크 비율 (시작:정점:여운) |
|------------|------------------------|
| quick | 1:2:1 — 빠른 정점, 짧은 여운 |
| standard | 1:2:2 — 충분한 정점 + 여운 |
| breath | 1:2:3 — 긴 여운이 다음 클립까지 이어짐 |

---

## [CAMERA] — 시네마틱 카메라 동사

### 6종 모션 패턴

| shot-composer 패턴 | iv_prompt [CAMERA] |
|-------------------|-------------------|
| **하강 공개** | `Slow tilt down over {N}s` |
| **상승 공개** | `Gentle tilt up over {N}s` |
| **수평 추적** | `Smooth pan left to right over {N}s` |
| **줌 발견** | `Slow dolly in toward the subject over {N}s` |
| **여백 호흡** | `Subtle pull back over {N}s` |
| **정지+미동** | `Camera holds static with barely perceptible drift` |

### clip_rhythm → 속도

| clip_rhythm | 속도 |
|-------------|------|
| quick | 빠르고 명확 |
| standard | 부드러운 |
| breath | 매우 느린, 명상적 |

### 규칙
- 카메라 동작은 **단일 동작 + holds** (2회 변경 금지)
- 이미지 내부에서 소화 가능한 범위만 (넓은 횡단 패닝 금지)

---

## [ENVIRONMENT] — 환경 변화

장면에 생동감을 더하는 미세 변화. **스케치 세계관 안에서.**

| 적합 | 금지 |
|------|------|
| "A gentle breeze stirs the neckerchief" | "glow", "pulse", "beam" (VFX) |
| "Faint dust settles on the surface" | "smoke", "haze" (정책 위반) |
| "Subtle light shift across the scene" | "paper-edge flutter" (리터럴 종이 프레임) |
| "A single leaf drifts past" | "buildings grow", "transforms" (장면 변환) |

> 모든 Shot에 환경 변화가 필요하지는 않음. 적합하지 않으면 `None.`

---

## [AUDIO] — SFX + Ambient

| emotion_tag | 필수 SFX |
|-------------|---------|
| `TENSION` | `SFX: soft deep heartbeat, slow pulse, close-up foley` |
| `AWE` | `SFX: chime with deep reverb, lingering resonance, one-shot` |
| `REVEAL` | `SFX: small delicate bell chime, clear bright ring, one-shot` |
| `HUMOR` | `SFX: gentle soft bubble pop, light and airy, one-shot` |
| `REFLECTIVE` | `SFX: soft wind chime, distant single note, fading` |

---

## thinking level 결정

| 조건 | thinking level |
|------|----------------|
| `has_human: main` AND (`emotion_tag` ∈ {REVEAL, TENSION} OR 동적 동작) | `high` |
| 그 외 | `low` |

---

## 통합 예시

### 예시 A: AWE + breath + 캐릭터 등장

```
[thinking: high]

[CAMERA]
Slow tilt down over 5 seconds, then holds.

[ACTION]
The character slowly lifts their head upward, gazing at the towering object.
At the apex, the gaze locks — one small step backward, shoulders drawing inward.

[ENVIRONMENT]
A faint dust mote drifts downward across the scene.

[AUDIO]
SFX: chime with deep reverb, lingering resonance, one-shot
Ambient: distant factory hum, metallic resonance
Duration: 6s
```

### 예시 B: HUMOR + quick + 보조 캐릭터

```
[thinking: low]

[CAMERA]
Quick dolly in over 2 seconds, then holds.

[ACTION]
The character tilts head to one side. One shoulder lifts in a knowing shrug.
Weight shifts from left foot to right.

[ENVIRONMENT]
None.

[AUDIO]
SFX: gentle soft bubble pop, light and airy, one-shot
Ambient: quiet room tone
Duration: 4s
```

### 예시 C: has_human: none + 소품 중심

```
[thinking: low]

[CAMERA]
Smooth pan left to right over 4 seconds, then holds.

[ACTION]
A faint glint of light moves along the rail surface from left to right.
One drawn leaf at the edge catches a draft and shifts slightly.

[ENVIRONMENT]
Subtle light shift follows the camera pan direction.

[AUDIO]
SFX: soft scratching of pen on paper, continuous
Ambient: quiet, ticking clock
Duration: 5s
```

---

## 금지 사항

### 캐릭터 외형 변형 유발 동작
- ❌ `springs backward`, `torso arching`, `arms flailing`, `mouth stretches`, `body contorts`, `limbs extend`
- ✅ `slowly tilts head`, `shifts weight`, `one arm rises slightly`, `leans forward`

### Veo 정책 금지어
| 금지 | 대체 |
|------|------|
| `heat haze`, `haze` | `shimmer of light` |
| `smoke`, `smoking` | `steam`, `wisp` |
| `explosion`, `fire`, `blood`, `gun` | 장면 재설계 |

### 스타일 이탈 유발
| 금지 | 이유 |
|------|------|
| `glow`, `pulse`, `beam`, `radiate` | VFX 이펙트 |
| `paper-edge flutter`, `page curl` | 종이 프레임 리터럴 렌더링 |
| `fingers spread`, `presenting gesture` | 실사 인체 전환 |
| `grow upward`, `transforms into` | 장면 변환/생성 |

### 운영 규칙
- [ACTION]이 "remains still" / "stays as drawn" **만** 있으면 금지 — 최소 1개 의도된 동작 필수
- 카메라 2회 이상 변경 금지
- 이미지에 그려진 기존 요소 위치/상태 변경 금지
- 이미지에 텍스트 포함 시 → 정적 이미지 사용 검토 또는 `Text elements remain unchanged` 명시
