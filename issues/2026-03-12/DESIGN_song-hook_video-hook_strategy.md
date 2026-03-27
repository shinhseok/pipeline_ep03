# Design Strategy: Song Hook + Video Hook

DATE: 2026-03-12
STATUS: DESIGN APPROVED — PENDING IMPLEMENTATION
SCOPE: content-planner, script-director, shot-composer, audio-director, generate-images, generate-videos

---

## 1. 배경 및 목적

Hook(≤30초)의 임팩트를 극대화하기 위해 두 가지 새로운 옵션을 추가한다:

1. **Song Hook** — 30초 웃긴 싱어송라이터 느낌의 노래로 Hook을 제작, Shorts로도 재활용
2. **Video Hook** — Veo3/Kling을 이용해 Hook을 실제 동영상 클립으로 제작

두 옵션은 **직교적(독립 선택 가능)**:

| 조합 | 설명 |
|------|------|
| Standard + Image | 기존 방식 (나레이션 + 이미지) |
| Standard + Video | 나레이션 + 영상 클립 |
| Song + Image | 노래 + 이미지 |
| Song + Video | 노래 + 영상 클립 (최대 임팩트) |

---

## 2. Song Hook 설계 전략

### 2-1. Hook 타입 분기

기획 단계(STEP 02)에서 Hook 타입을 선택한다:

```
HOOK_TYPE: standard | song
```

- `standard`: 기존 나레이션 Hook (변경 없음)
- `song`: 30초 노래 Hook + Shorts 듀얼 활용

### 2-2. 시그니처 멜로디 전략

- **멜로디 고정**: 채널 시그니처 멜로디를 1회 확정 후 전 에피소드에서 재사용
- **가사 변동**: 에피소드별 주제에 맞는 가사만 변경
- 시청자가 멜로디만 들어도 채널을 인식하는 **브랜딩 효과**

### 2-3. 가사 작성 규칙

- 대본(STEP 03~04)에서 Song Hook 선택 시 **나레이션 대신 가사**를 기입
- 가사 구조: 도입(4마디) → 핵심 질문(4마디) → 후크라인(반복)
- 톤: 유머러스, 자기비하적, 에코현자 캐릭터에 맞는 화법

### 2-4. 브릿지 설계 (톤 전환 — 핵심 과제)

Song Hook → Setup 나레이션으로의 전환이 부자연스러우면 시청 이탈 발생.
3단계 브릿지로 해결:

```
[1] 후크라인 질문화 — 노래 마지막 소절을 질문으로 끝냄
    예: "♪ 그런데 정말 그럴까~ ♪"
[2] 짧은 침묵 (0.5~1초) — 톤 리셋 포인트
[3] 나레이션 이어받기 — "사실, 이건 우리 모두의 이야기입니다."
```

- 브릿지 설계는 **script-director가 대본 작성 시** 명시적으로 처리
- `[BRIDGE]` 태그로 전환 구간 표기

### 2-5. 오디오 파이프라인 확장

- **Suno 프롬프트**: audio-director(STEP 07)에서 Song Hook Shot에 대해 `suno_style` + `suno_lyrics` 추가
- 기존 `bgm` 필드와 별도 — 노래 자체가 메인 오디오
- Suno 생성 → Shorts 편집 → Hook 삽입 (수동 워크플로우)

### 2-6. Shorts 듀얼 활용

- Song Hook 30초 = 독립 Shorts 콘텐츠
- Shorts용 세로 크롭/리프레임은 편집 단계(STEP 10)에서 수동 처리
- 기획 단계에서 Shorts 적합성 미리 고려 (세로 구도 친화적 Shot 구성)

---

## 3. Video Hook 설계 전략

### 3-1. 영상 생성 기본 요소

Veo3/Kling에 입력하는 요소:

| 요소 | 필수 | 설명 |
|------|------|------|
| Start Image | O | 영상 시작 프레임 (NB2 flow_prompt로 생성) |
| End Image | X | 영상 끝 프레임 (nullable — 없으면 AI 자유 생성) |
| Motion Prompt | O | 동작/전환 지시 (iv_prompt 필드 활용) |
| Duration | O | 클립 길이 (초) |
| Engine | O | veo3 / kling |

### 3-2. 이미지 1장 vs 2장 선택 기준

Shot별로 선택 가능 (`video_end_image` nullable):

| 상황 | 권장 |
|------|------|
| 카메라 줌인/패닝, 단순 움직임 | 1장 (Start only) |
| 캐릭터 변신, 상황 전환, 감정 변화 | 2장 (Start + End) |
| 배경만 있는 분위기 Shot | 1장 (Start only) |

- 2장은 비효율이 아님 — **의도한 전환을 정밀 제어**할 수 있어 리테이크 비용 절감
- Hook은 30초 안에 시선을 잡아야 하므로 핵심 전환 Shot은 2장 권장

### 3-3. Hook 미디어 타입 분기

```
HOOK_MEDIA: image | video
```

기획 단계(STEP 02)에서 선택. Shot 스키마에 반영:

| 필드 | 용도 | 적용 조건 |
|------|------|-----------|
| `hook_media_type` | `image` / `video` | SECTION00_HOOK Shot만 |
| `video_start_image` | 시작 프레임 이미지 경로 | `video`일 때 |
| `video_end_image` | 끝 프레임 이미지 경로 (nullable) | `video`일 때 |
| `video_prompt` | Veo3/Kling 모션 프롬프트 | `video`일 때 |
| `video_duration` | 클립 길이 (초) | `video`일 때 |
| `video_engine` | `veo3` / `kling` | `video`일 때 |

### 3-4. 이미지 생성 순서 변경

Video Hook 선택 시 이미지 생성 순서가 달라짐:

```
기존:    ANCHOR 이미지(Phase 1) → 씬 이미지(Phase 2)
Video:   Hook 이미지(Phase 0) → ANCHOR(Phase 1) → 씬(Phase 2) → 영상 생성(Phase 3)
```

- Hook Shot 이미지가 **영상 생성의 입력**이므로 먼저 생성해야 함
- `generate-images` 스킬에 Phase 0 (Hook priority) 로직 추가 필요

### 3-5. flow_prompt와의 관계

Video Hook Shot도 기존 `flow_prompt`(NB2 JSON)는 **그대로 필요**:
- Start Image / End Image 생성에 NB2 flow_prompt 사용
- 추가로 `video_prompt`(모션 지시)를 별도 작성
- 기존 `iv_prompt` 필드를 Video Hook 프롬프트로 활용 가능 (이미 스키마에 존재)

### 3-6. Song + Video 조합 시 오디오 처리

- Veo3는 자체 오디오를 생성하지만 → **Veo3 오디오 무시**, Suno 음원 사용
- Kling은 오디오 없는 영상 생성 가능 → 오디오 충돌 없음
- 에코현자 캐릭터는 점 눈+입만 있으므로 립싱크 문제 없음

---

## 4. 통합 분기 구조

```
STEP 02 (content-planner) 기획 시 선택:
  ├─ HOOK_TYPE:  standard | song
  └─ HOOK_MEDIA: image | video

STEP 03~04 (script-director):
  ├─ standard → 기존 나레이션 작성
  └─ song → 가사 작성 + [BRIDGE] 태그 + 브릿지 설계

STEP 05 (shot-composer):
  ├─ image → 기존 Shot 구성
  └─ video → hook_media_type: video + video_prompt + video_duration
  └─ video + 2장 → video_start_image + video_end_image 경로 설정

STEP 06 (visual-director):
  ├─ image → 기존 flow_prompt 변환
  └─ video → flow_prompt (Start/End 이미지용) + video_prompt 작성

STEP 07 (audio-director):
  ├─ standard → 기존 el_narration + bgm
  └─ song → suno_style + suno_lyrics + bgm (시그니처 멜로디 참조) + [BRIDGE] 오디오 태깅

generate-images:
  └─ video → Phase 0 (Hook 이미지 우선 생성)

generate-videos:
  └─ video → Hook Shot 영상 생성 (Start/End Image + video_prompt + duration)
```

---

## 5. 파이프라인 영향도 분석

| 영향 대상 | 변경 수준 | 내용 |
|-----------|----------|------|
| content-planner | 중간 | HOOK_TYPE + HOOK_MEDIA 선택 옵션 추가 |
| script-director | 중간 | Song 가사 작성 규칙 + [BRIDGE] 태그 + 브릿지 설계 |
| shot-composer | 중간 | Video Shot 필드 추가 (hook_media_type 등) |
| visual-director | 낮음 | Video Shot에 대한 video_prompt 추가 작성 |
| audio-director | 중간 | Song Hook → suno_style + suno_lyrics 필드 추가 |
| generate-images | 중간 | Phase 0 (Hook 우선 생성) 로직 |
| generate-videos | 중간 | Hook 영상 생성 로직 추가 |
| pipeline_reference.md | 낮음 | 스키마 필드 추가 문서화 |
| pipeline-rules.md | 낮음 | Hook 분기 규칙 추가 |
| 기존 동작 호환 | 완전 | HOOK_TYPE=standard + HOOK_MEDIA=image가 기본값 → 무변경 |

---

## 6. 구현 순서 (제안)

```
Phase 1 — 스키마 & 기획 확장
  1. pipeline_reference.md: Shot Record에 Video Hook 필드 추가
  2. content-planner: HOOK_TYPE + HOOK_MEDIA 선택 섹션 추가
  3. _meta.md 템플릿에 HOOK_TYPE, HOOK_MEDIA 필드 추가

Phase 2 — 대본 & Shot 구성
  4. script-director: Song 가사 규칙 + [BRIDGE] 태그 처리
  5. shot-composer: Video Shot 필드 매핑 + hook_media_type 분기

Phase 3 — 프롬프트 & 오디오
  6. visual-director: Video Shot용 video_prompt 작성 규칙
  7. audio-director: Song Hook → suno_style + suno_lyrics 출력 규칙

Phase 4 — 생성 스크립트
  8. generate-images: Phase 0 Hook 우선 생성
  9. generate-videos: Hook 영상 생성 워크플로우

Phase 5 — 검증 & 전파
  10. pipeline-monitor: Hook 관련 검증 항목 추가
  11. run-director: Hook 분기 오케스트레이션
  12. 의존성 전파 체크 (pipeline-rules.md §12)
```

---

## 7. 미결 사항 — 결정 완료

| # | 항목 | 결정 |
|---|------|------|
| 1 | 시그니처 멜로디 확정 방법 | **Suno로 AI 생성** — 첫 에피소드에서 시그니처 멜로디 확정 후 재사용 |
| 2 | Suno 프롬프트 포맷 | **확정 — §8 참조** |
| 3 | 기본 영상 엔진 | **Veo3 우선 사용** |
| 4 | End Image flow_prompt 분리 | **태그 방식 확정**: `flow_prompt[start]` + `flow_prompt[end]` 2개 작성. End Image 없으면 `flow_prompt[end]: null` |
| 5 | Shorts 리프레임 | **수동 처리** (편집 단계) |
| 6 | Song Hook 가사 길이 | **확정 — §9 참조** |

---

## 8. Suno 프롬프트 구조 (확정)

> 출처: Suno 공식 Help Center + Community Guide — Custom Mode + Metatags

### 프롬프트 = Style 필드 + Lyrics 필드 (분리 입력)

**Style 필드** (음악 스타일 지시 — 세미콜론 구분, 4~7개 디스크립터):

```
Genre ; Tempo ; Mood ; Instrument ; Vocal Style ; Production
```

→ 예시: `Acoustic singer-songwriter; comedic folk; mid-tempo; playful; self-deprecating humor; warm guitar strumming; lo-fi intimate recording`

**Lyrics 필드** (가사 — Metatags 포함):

```
[Intro]
[Instrumental]

[Verse]
{에피소드별 가사 — 4~6줄}

[Hook]
{후크라인 반복 — 2줄}

[Outro]
{질문형 마무리 — 브릿지 연결용}
[Fade Out]
```

### Suno Custom Mode 주요 파라미터

| 파라미터 | 설정값 |
|----------|--------|
| Mode | **Custom** (직접 가사 + 스타일 입력) |
| Style / Genre | 세미콜론 구분 디스크립터 (v4.5+: 최대 1,000자) |
| Lyrics | Metatags 포함 가사 |
| Instrumental | **false** (보컬 있음) |
| negativeTags | 필요 시 제외할 요소 |

> ⚠️ Suno는 직접적인 duration 파라미터 없음. 가사 길이 + `[Outro]`/`[Fade Out]` 태그로 간접 제어.
> 기본 생성 길이 ~2분이므로 30초 Hook용으로는 가사를 짧게 유지 + `[End]` 태그 필수.

### audio-director 출력 필드

Song Hook Shot에 대해 기존 `bgm` 대신:

```yaml
suno_style: "Acoustic singer-songwriter; comedic folk; mid-tempo; playful; lo-fi intimate"
suno_lyrics: |
  [Intro]
  [Instrumental]
  [Verse]
  {가사}
  [Hook]
  {후크라인}
  [Outro]
  {질문형 마무리}
  [End]
suno_params:
  instrumental: false
  negative_tags: "heavy metal, electronic, auto-tune"
```

### Metatags 레퍼런스 (Suno 공식)

**구조 태그:**

| 태그 | 용도 |
|------|------|
| `[Intro]` | 오프닝 |
| `[Verse]`, `[Verse 2]` | 메인 내러티브 |
| `[Pre-Chorus]` | 코러스 빌드업 |
| `[Chorus]` / `[Hook]` | 반복 핵심 파트 |
| `[Bridge]` | 대비 연결부 |
| `[Outro]` / `[End]` / `[Fade Out]` | 마무리 (종료 신호) |
| `[Instrumental]` | 보컬 없는 구간 |
| `[Break]` / `[Breakdown]` | 리듬 멈춤 |

**보컬 태그:**

| 태그 | 효과 |
|------|------|
| `[Whispered]` | 속삭임 |
| `[Spoken Word]` | 말하기 (노래 아님) |
| `[Falsetto]` | 고음역 |
| `[Ad-lib]` | 즉흥 보컬 |

---

## 9. Song Hook 가사 길이 기준 (확정)

> 목표: 정확히 30초

### 한국어 노래 음절 수 기준

| 템포 | 속도 (음절/초) | 30초 총 음절 | 비고 |
|------|---------------|-------------|------|
| 느린 발라드 | ~3 | ~90 | 여유로운 전달 |
| **중간 템포 (채택)** | **~4** | **~120** | **싱어송라이터 적합** |
| 빠른 업템포 | ~5 | ~150 | 코미디 랩 느낌 |

### 가사 분량 가이드

```
총 음절: 80~120 음절 (중간 템포 기준)
줄 수:   6~10줄
구조:    [Intro](2~4초) + [Verse](12~16초) + [Hook](8~10초) + [Outro](2~4초)
```

- **[Intro]**: 기타 인트로, 가사 없음 (2~4초)
- **[Verse]**: 에피소드 주제 소개, 4~6줄 (50~70 음절)
- **[Hook]**: 후크라인 1~2회 반복 (20~30 음절)
- **[Outro]**: 질문형 마무리 1줄 → 브릿지 연결 (10~20 음절)

### script-director 검증 규칙

```
Song Hook 가사 작성 시:
- 총 음절 수: 80~120 음절 (±10% 허용)
- 초과 시 경고 → 가사 축약 필요
- 미달 시 경고 → 악기 구간 또는 반복 추가
```
