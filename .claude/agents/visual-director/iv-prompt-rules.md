# iv_prompt Rules — Visual Director Reference

---

## thinking level 결정

| 조건 | thinking level |
|------|----------------|
| `has_human: main` AND (`emotion_tag` ∈ {REVEAL, CLIMAX, TENSION} OR `[액션]`에 동적 동작 포함) | `high` |
| `has_human: none/anonym` OR 단순 카메라 드리프트 / 배경 분위기 | `low` |

---

## iv_prompt 구조 (Veo 3 I2V 공식 형식, 영어)

Write an **Image-to-Video prompt** following Veo 3 official I2V structure.
The still image already defines the scene — describe only **what changes**.

```
[thinking: low/high]

[ACTION]
{무엇이 바뀌는지 — 동사 중심, 3인칭, 1~2문장.
이미지에 이미 있는 씬·배경·인물 설명 반복 금지.}

[CAMERA]
{카메라 움직임 1문장. 미세하게 — 최대 5~10% drift.}

[AUDIO]
SFX: {효과음 — emotion_tag 필수 SFX 또는 creative_intent 기반 상황음}
Ambient: {배경 환경음}
Duration: {duration_est}s
```

---

## emotion_tag별 필수 SFX

| emotion_tag | 필수 SFX |
|-------------|---------|
| `TENSION` | `SFX: soft deep heartbeat, slow pulse, close-up foley` |
| `AWE` | `SFX: chime with deep reverb, lingering resonance, one-shot` |
| `REVEAL` | `SFX: small delicate bell chime, clear bright ring, one-shot` |
| `HUMOR` | `SFX: gentle soft bubble pop, light and airy, one-shot` |
| 기타 | creative_intent [소품]/[공간]에서 파생 |

---

## 제약

- 이미지의 구도·비율·캐릭터 외형 변경 없음 (I2V는 시작 프레임을 잠금)
- 단일 샷 내 자체 모션만 — 씬 전환 없음
- 대사(Dialogue) 작성 금지 — 나레이션은 ElevenLabs 별도 처리
