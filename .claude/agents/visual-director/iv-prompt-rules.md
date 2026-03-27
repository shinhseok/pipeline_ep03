# iv_prompt Rules — Visual Director Reference (Canvas vs Director)

---

## 대원칙: Canvas vs Director

이미지는 이미 **Canvas**(화면 구성 — 구도, 색, 배치)를 완성했다.
iv_prompt는 **Director**(감독)로서 **동작**, **카메라**, **환경 변화**만 지시한다.

> ❌ 이미지에 이미 있는 씬·배경·인물 외형 반복 금지
> ✅ "무엇이 움직이는가", "카메라가 어떻게 이동하는가", "환경이 어떻게 변하는가"만 기술

---

## thinking level 결정

| 조건 | thinking level |
|------|----------------|
| `has_human: main` AND (`emotion_tag` ∈ {REVEAL, TENSION} OR 동적 동작) | `high` |
| [CAMERA] 복합 모션 (2개 이상 동작 연결) | `high` |
| `has_human: none/anonym` OR 단순 카메라 드리프트 | `low` |

---

## iv_prompt 구조 (Veo 3 I2V, 영어)

```
[thinking: low/high]

[CAMERA]
{shot-composer [카메라] 모션 시퀀스 → 영어 변환. 1~2문장.}

[ACTION]
{shot-composer [감정선] 모션 아크(시작→정점→여운) → 영어 변환. 2~3문장.
구체적 동사 필수. 상태 묘사 금지.}

[ENVIRONMENT]
{배경 시각 효과 — 먼지, 안개, 조명 변화, 잉크 호흡. 1문장.
없으면 None.}

[AUDIO]
SFX: {emotion_tag 필수 SFX}
Ambient: {배경 환경음}
Duration: {duration_est}s
```

---

## [CAMERA] — shot-composer 모션 시퀀스 매핑

shot-composer `[카메라]`의 모션 시퀀스를 영어로 변환한다. **"Static" 남발 금지** — 모션 패턴이 지정된 Shot은 반드시 반영.

### 6종 모션 패턴 변환 테이블

| shot-composer 패턴 | iv_prompt [CAMERA] | clip_rhythm 속도 |
|-------------------|-------------------|-----------------|
| **하강 공개** (틸트다운) | `Slow tilt down from top of frame, revealing the subject at bottom over {N}s` | breath: 매우 느리게 |
| **상승 공개** (틸트업) | `Gentle tilt up from ground detail to full context over {N}s` | standard: 보통 |
| **수평 추적** (패닝) | `Smooth pan {left to right / right to left}, tracking across the scene over {N}s` | standard: 보통 |
| **줌 발견** (줌인) | `Slow push in toward the subject, from wide establishing to medium detail over {N}s` | quick~standard |
| **여백 호흡** (줌아웃) | `Subtle pull back, expanding negative space around the subject over {N}s` | breath: 느리게 |
| **정지+미동** | `Nearly static. Barely perceptible drift with faint ambient motion` | breath |

### 복합 모션 (2개 연결)

shot-composer가 `모션: A(Ns) → B(Ns)` 형태로 2개를 연결한 경우:
```
[CAMERA]
Slow tilt up over 3 seconds, then holds with barely perceptible drift for 2 seconds.
```

### clip_rhythm → 속도 매핑

| clip_rhythm | 카메라 속도 | 모션 강도 |
|-------------|-----------|----------|
| quick (3-4s) | 빠르고 명확 | 즉각적 줌/패닝 |
| standard (5-6s) | 보통, 부드러운 | 자연스러운 흐름 |
| breath (6-7s) | 매우 느린, 명상적 | 미세 드리프트 or 슬로우 틸트 |

---

## [ACTION] — 모션 아크 3단계 반영

shot-composer `[감정선]`의 모션 아크(시작→정점→여운)를 **영어 동사 문장**으로 변환한다.

### Bad vs Good

```
❌ Bad: "The character is standing in front of a large gear."
   (이미 이미지에 서 있다면 → 정지화면)

✅ Good: "The character slowly lifts their head upward. At the apex, they freeze —
   the gear extends beyond the frame. Shoulders stiffen as they take one step back."
   (시작→정점→여운이 있는 동작 시퀀스)
```

```
❌ Bad: "A sad scene with a lonely character."
   (상태 묘사 — Director가 아닌 Canvas 역할)

✅ Good: "Hair strands sway gently in the wind. The character's hand slowly unclenches,
   fingers spreading apart."
   (구체적 동사 — 바람, 손가락 움직임)
```

### has_human별 [ACTION] 전략

| has_human | [ACTION] 초점 |
|-----------|--------------|
| **main** | 캐릭터 동작 — 고개/팔/자세 변화, 표정 미세 변화 (시작→정점→여운) |
| **anonym** | 실루엣 동작 — 걸음, 흔들림, 군중 파동 |
| **none** | 소품/환경 동작 — 기어 회전, 잉크 번짐, 종이 흔들림, 물결 |

### 모션 아크 시간 배분

| clip_rhythm | 아크 비율 (시작:정점:여운) |
|------------|------------------------|
| quick | 1:2:1 — 빠른 정점, 짧은 여운 |
| standard | 1:2:2 — 충분한 정점 + 여운 |
| breath | 1:2:3 — 긴 여운이 다음 클립까지 이어짐 |

---

## [ENVIRONMENT] — 배경 시각 효과 (신규)

배경에 생동감을 부여하는 미세 시각 효과. 선택 사항 — 필요 없으면 `None`.

### 유형별 예시

| 유형 | 예시 |
|------|------|
| **Particles** | `Fine dust motes drift slowly through the air` |
| **Atmosphere** | `Faint mist flows along the ground` |
| **Lighting** | `Subtle light shift as if clouds pass overhead, casting moving shadows` |
| **Organic** | `Ink lines at the edges seem to breathe, expanding and contracting slightly` |
| **Weather** | `Gentle breeze causes paper edges to flutter` |

### emotion_tag별 환경 효과 기본값

| emotion_tag | 권장 환경 효과 |
|-------------|--------------|
| **TENSION** | 그림자 천천히 접근, 먼지 떨어짐, 미세 진동 |
| **AWE** | 빛 줄기 이동, 광활한 공간 안개, 미세 입자 부유 |
| **REVEAL** | 조명 변화 (어두움→밝음), 선명해지는 디테일 |
| **HUMOR** | 가벼운 바람, 종이/잎 흔들림, 물방울 |
| **REFLECTIVE** | 잉크 선 미세 호흡, 그림자 느린 이동, 정적 속 미동 |

---

## [AUDIO] — SFX + Ambient

### emotion_tag별 필수 SFX

| emotion_tag | 필수 SFX |
|-------------|---------|
| `TENSION` | `SFX: soft deep heartbeat, slow pulse, close-up foley` |
| `AWE` | `SFX: chime with deep reverb, lingering resonance, one-shot` |
| `REVEAL` | `SFX: small delicate bell chime, clear bright ring, one-shot` |
| `HUMOR` | `SFX: gentle soft bubble pop, light and airy, one-shot` |
| `REFLECTIVE` | `SFX: soft wind chime, distant single note, fading` |

Ambient는 creative_intent [공간]에서 파생한 환경음.

---

## 통합 예시

### 예시 A: AWE + breath + 하강 공개

```
[thinking: high]

[CAMERA]
Slow tilt down from the vast empty sky, gradually revealing the tiny character
at the bottom of the frame over 5 seconds, then holds.

[ACTION]
The character slowly tilts their head upward. At the apex, they freeze completely —
the massive gear extends far beyond the frame edge. One small step backward,
shoulders stiffening.

[ENVIRONMENT]
Fine soot particles drift downward through the air. The gear's shadow
creeps slowly across the ground toward the character.

[AUDIO]
SFX: chime with deep reverb, lingering resonance, one-shot
Ambient: distant factory hum, metallic resonance
Duration: 6s
```

### 예시 B: HUMOR + quick + 줌 발견

```
[thinking: low]

[CAMERA]
Quick push in from wide shot to the prop detail over 2 seconds.

[ACTION]
The character's eyebrow rises sharply. Head tilts to one side
with a slight bounce.

[ENVIRONMENT]
None.

[AUDIO]
SFX: gentle soft bubble pop, light and airy, one-shot
Ambient: quiet room tone
Duration: 4s
```

### 예시 C: has_human: none + standard + 수평 추적

```
[thinking: low]

[CAMERA]
Smooth pan from left to right over 4 seconds, tracking across the timeline,
then holds for 1 second.

[ACTION]
Ink lines of the leftmost element begin to fade slightly while the rightmost
element's lines darken and sharpen, as if drawn in real-time.

[ENVIRONMENT]
Subtle light shift moves across the scene from left to right,
following the camera pan.

[AUDIO]
SFX: soft scratching of pen on paper, continuous
Ambient: quiet study room, ticking clock
Duration: 5s
```

---

## 제약

- 이미지의 구도·비율·캐릭터 외형 변경 없음 (I2V는 시작 프레임을 잠금)
- 단일 샷 내 자체 모션만 — 씬 전환 없음
- 대사(Dialogue) 작성 금지 — 나레이션은 ElevenLabs 별도 처리
- [CAMERA]가 shot-composer 모션 시퀀스와 일치해야 함 — 임의 변경 금지
