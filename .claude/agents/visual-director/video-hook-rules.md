# Video Hook Rules — Visual Director Reference

---

## Video Hook 연출 모드

`hook_media_type: video`인 SECTION00_HOOK Shot에는 2가지 연출 모드가 있다.

| 모드 | 설명 | 권장 상황 |
|------|------|----------|
| **Kinetic Transition** | 연속 KF 이미지를 start/end로 사용. 캐릭터 이동+모션 블러로 장면 전환 | Song Hook 원테이크, 시대 관통 서사 |
| **Per-Shot** | Shot별 start/end 이미지 분리 생성. 제자리 변환 | 단일 Shot 내 상태 변화, 줌인/아웃 |

---

## Mode A: Kinetic Transition (권장)

### 핵심 원리 — 캐릭터 앵커 + 드론 카메라

**3대 원칙:**

1. **캐릭터 = 앵커**: 메인 캐릭터는 **처음부터 끝까지 프레임 안에 존재**한다. 절대 프레임 밖으로 나가지 않는다.
2. **카메라 = 드론**: 카메라는 캐릭터를 중심으로 **따라가고, 회전하고, 가감속**한다. 카메라의 속도·앵글이 바뀌어도 캐릭터를 놓치지 않는다.
3. **배경 = 흘러가는 것**: 배경과 소품은 장면이 바뀔 때 프레임 밖으로 사라지거나 자연스럽게 전환된다. 캐릭터만 일관되면 배경은 자유롭게 변할 수 있다.

**캐릭터 움직임 설계:**
- 캐릭터도 적극적으로 움직인다 (걷기, 달리기, 팔 벌리기, 회전, 멈춤 등)
- 캐릭터의 에너지 아크가 가사/음악의 에너지와 동기화된다
- 에피소드별 가사/톤에 맞게 설계. 아래는 일례:
  > 예: 걷기→달리기→환호→팔 벌림→멈춤 = 상승→가속→최고조→확장→고요

**카메라 움직임 설계:**
- 카메라 회전으로 캐릭터의 다른 각도를 자연스럽게 보여줌
- 배경 전환은 카메라 회전/이동 중에 자연스럽게 발생
- 에피소드별 설계. 아래는 일례:
  > 예: 나란히 걷기→가속→원형 회전(정면→3/4→뒷모습)→줌아웃→정지

**KF 이미지 설계 규칙:**
- 모든 KF에 캐릭터가 **프레임 안에 명확하게 존재**. 위치는 구도에 따라 자유.
- KF 간 캐릭터 포즈가 **연속적** — 급격한 자세 변화 금지
- 캐릭터 크기는 KF 전체에서 **비슷하게 유지** (마지막 KF만 줌아웃 허용)

> ⚠️ **이동 방향 일관성**: 피사체의 기본 이동 방향은 KF 전체에 걸쳐 일관되어야 한다. 방향이 바뀔 때는 카메라 회전으로 자연스럽게 전환.

**군중/익명 실루엣 규칙:**
- 군중은 **character_reference.jpeg** (기본 강낭콩 형태) 참조. main_turnaround 사용 금지.
- ref_images에 character_reference.jpeg 명시적 포함.

```
캐릭터: [걷기] → [달리기] → [환호] → [팔 벌림] → [멈춤]
카메라: [나란히] → [가속]   → [회전]  → [줌아웃]  → [정지]
배경:   [플랫폼] → [기차]   → [군중]  → [풍경]    → [빈 레일]
```

### 구조

- 각 Shot = **1개 Key Frame 이미지** (해당 시대/장면에서의 연기 포즈)
- `image_prompt` = 단일 (해당 KF 이미지 생성용)
- `video_prompt` = 영어, KF_N → KF_{N+1} 키네틱 트랜지션 묘사
- `video_start_image` = 자기 Shot 이미지
- `video_end_image` = 다음 Shot 이미지
- 마지막 Shot = landing frame (`hook_media_type: image`, 전환 없음)

### image_prompt 규칙

기존 v3 순수 한국어 서술형 5단락과 동일. `image_prompt[start]/[end]` 분리 없음.
각 KF 이미지의 연기 포즈를 개별적으로 묘사한다.

### video_prompt 구조 (영어)

video_prompt는 **캐릭터의 물리적 움직임 + 카메라의 물리적 움직임**을 기술한다. 이야기/시나리오가 아닌 **촬영 지시**임을 명심.

```
video_prompt: |
  Cinematic drone-style tracking shot in pen-and-ink doodle style on white background.

  {캐릭터의 물리적 움직임 — 어디로, 어떻게 움직이는가}
  {카메라의 물리적 움직임 — 어떻게 따라가는가}
  {배경의 변화 — 무엇이 프레임에 들어오고 나가는가}

  The character must remain visible in frame throughout the entire shot.
  Duration: {video_duration}s
```

> 권장: CHARACTER/CAMERA/BACKGROUND를 분리하여 기술하면 구조적이지만, 자연어 묘사도 허용. 핵심은 **물리적 동작 기술**이지 서사/시나리오가 아니라는 점.
> ⚠️ **"캐릭터가 기차를 탄다"** 같은 서사적 묘사 금지. 대신 **"캐릭터가 우측으로 걸어간다. 카메라가 따라간다. 배경에서 기차가 프레임에 들어온다."** 식의 물리적 동작 기술.

### 전환 효과 유형

| 전환 효과 | 설명 | 적합한 상황 |
|----------|------|----------|
| **모션 블러** | 배경이 속도선으로 흘러감 | 장소 변경 (공방→공장) |
| **증기/연기** | 증기가 화면을 삼키고 새 장면 등장 | 산업/공장 전환 |
| **빛 전환** | 밝아졌다가 새 공간으로 | 시대 변환 (과거→현대) |
| **페이드** | 배경이 서서히 순백으로 사라짐 | 마지막 전환 (현실→여백) |

### 의상 변환 (Costume Transition)

키네틱 트랜지션 중 의상 변환이 가능하다.
모션 블러/증기가 캐릭터를 가리는 순간 의상이 바뀐다.

- `video_prompt`에 의상 변환 명시: "costume has seamlessly transformed: {old} dissolved into {new}"
- 전환 전 Shot: `costume_refs: [old_costume]`, `ref_images: old_character.jpeg`
- 전환 후 Shot: `costume_refs: [new_costume]`, `ref_images: new_character.jpeg`
- 캐릭터 체형(콩 실루엣)은 반드시 동일 유지

### creative_intent [Kinetic Transition] 태그 (STEP 04)

```
[Kinetic Transition] KF{N} → KF{N+1}.
  전환 트리거: {캐릭터가 무엇을 하다가 움직이기 시작하는가}
  전환 동작: {이동 방향과 속도}
  전환 효과: {모션 블러/증기/빛 중 어떤 효과}
  착지: {다음 KF에서 캐릭터가 무엇을 하는가}
```

마지막 KF: `[Kinetic Transition] KF{N} — 착지 프레임. 전환 없음.`

### 이미지 경로 규칙 (Kinetic Transition)

| 필드 | 경로 형식 | 비고 |
|------|-----------|------|
| `video_start_image` | `09_assets/images/{RUN_ID}/shot{N}.png` | 자기 Shot 이미지 |
| `video_end_image` | `09_assets/images/{RUN_ID}/shot{N+1}.png` | 다음 Shot 이미지 |

### YAML 출력 형식 (Kinetic Transition)

```yaml
---
shot_id: 2
ref_images:
  - characters/run002/artisan.jpeg
  - props/run002/spinning_jenny.jpeg
thinking_level: high
image_prompt: |
  {v3 순수 한국어 서술형 — 해당 KF 이미지 생성용}
video_prompt: |
  {영어 — KF2→KF3 키네틱 트랜지션 묘사}
iv_prompt: |
  {영어 — KF2 정적 이미지 미세 애니메이션용}
has_human: main
asset_path: 09_assets/images/run002/shot02.png
video_start_image: 09_assets/images/run002/shot02.png
video_end_image: 09_assets/images/run002/shot03.png
---
```

---

## Mode B: Per-Shot (레거시)

### image_prompt[start] / [end] 분리 규칙

단일 Shot 내에서 Start→End 변환이 필요한 경우.

```yaml
image_prompt[start]: |
  {Start Image용 — 기존 image_prompt 규칙과 동일}

image_prompt[end]: |
  {End Image용 — Start와 동일 has_human·art_style, 상태만 변경}
  # 또는 null (1장만 필요한 Shot)
```

### video_prompt 구조 (Per-Shot)

```
video_prompt: |
  [ACTION]
  {Start → End 이미지 간 전환 동작 기술. 3인칭, 동사 중심.}

  [CAMERA]
  {카메라 움직임.}

  Duration: {video_duration}s
```

### 이미지 경로 규칙 (Per-Shot)

| 필드 | 경로 형식 | 비고 |
|------|-----------|------|
| `video_start_image` | `09_assets/images/{RUN_ID}/shot{N}_start.png` | 필수 |
| `video_end_image` | `09_assets/images/{RUN_ID}/shot{N}_end.png` | null 허용 |

---

## 공통 규칙

- Video Hook의 `video_prompt`는 **영어**로 작성 (Veo3 최적화)
- `iv_prompt`는 별도 유지 — 정적 이미지 미세 애니메이션용
- `video_engine`: `veo3` (기본) / `kling`
- Song Hook(`hook_type: song`)과 조합 가능 — suno_lyrics와 video_prompt 동시 사용
