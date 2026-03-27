# Pipeline Reference — YouTube Production Workflow

> 행동 규칙: pipeline-rules.md 참조 | 이 파일: 구조·스키마·경로 레퍼런스

---

## 3. 파일 네이밍 규칙

### 기본 형식:
`{단계번호}_{작업명}/{RUN_ID}/{SECTION}/shot{shot_id:02d}.md`

> **Run-Based 버전 관리**: `version_manifest.yaml` 매니페스트 존재 시 `{RUN_ID}` = `run001`, `run002` 등.
> 매니페스트 없으면 레거시 `v1/`, `v2/` 폴더 방식 유지.

### 예시 (STEP 04 — ANCHOR + Shot 파일):
```
04_shot_composition/
  └── {RUN_ID}/
      ├── ANCHOR.md            ← 전역 사전 (단일 소스)
      ├── anchor_research.md   ← 역사적 고증 기록 (트리거 있을 때만)
      ├── TITLECARD/shot00.md
      ├── SECTION00_HOOK/shot01.md, shot02.md ...
      ├── SECTION01/shot11.md ...
      └── ...
```

### Section 값 목록:
`TITLECARD` · `SECTION00_HOOK` · `SECTION01` · `SECTION02` · `SECTION03` · `SECTION04_OUTRO`

---

## 4. 저장 위치 규칙

| 단계 | 파일 종류 | 저장 경로 |
|------|-----------|-----------|
| 01~04 | 리서치·기획·대본 | `projects/{PROJECT_CODE}/{단계번호}_{작업명}/` |
| 05 | Shot base | `projects/{PROJECT_CODE}/04_shot_composition/{RUN_ID}/` |
| 06 | Visual delta | `projects/{PROJECT_CODE}/05_visual_direction/{RUN_ID}/` |
| 07 | Audio delta | `projects/{PROJECT_CODE}/06_audio_narration/{RUN_ID}/` |
| MERGE | Shot Records | `projects/{PROJECT_CODE}/07_shot_records/{RUN_ID}/` |
| RENDER | Storyboard | `projects/{PROJECT_CODE}/08_storyboard/{RUN_ID}/` |
| 09 | 이미지 에셋 | `projects/{PROJECT_CODE}/09_assets/images/{RUN_ID}/` |
| 09 | 영상 에셋 | `projects/{PROJECT_CODE}/09_assets/videos/` |
| 09 | 레퍼런스 | `projects/{PROJECT_CODE}/09_assets/reference/` |
| STEP 11 | 업로드 패키지 | `projects/{PROJECT_CODE}/10_youtube_publish/{RUN_ID}/` |

---

## 10. Shot / Scene / Section 번호 체계 정의

| 단위 | 정의 | 생성 단계 | 번호 형식 |
|------|------|-----------|-----------|
| **Section** | 대본 구조 단위 | STEP 03 | `SECTION00_HOOK`, `SECTION01`~`SECTION04_OUTRO` |
| **Scene** | 나레이션 의미 단락 단위 | STEP 06 | `scene_id` 필드로 표현 |
| **Shot** | 비주얼 클립 단위 | STEP 04 | 전역 순번 (Shot 0 = Title Card) |

### 관계 규칙
- 1 Section = 복수의 Shot
- Shot 0은 항상 Title Card로 예약
- Shot 번호(`shot_id`)는 **전역 순번** — 에피소드 전체에서 연속

---

## 12. 채널 공통 에셋 규칙

### 채널 레퍼런스 이미지

| 파일 | 경로 | 내용 |
|------|------|------|
| `basic_charector_ref.png` | `09_assets/reference/basic_charector_ref.png` | 해빛 기본 형태·비율·채색 |

- `has_human: main` 또는 `anonym` Shot에 항상 SOURCE REFERENCES에 포함

### 소품·변장 비주얼 ANCHOR (Phase 1)

- **경로**: `projects/{PROJECT_CODE}/09_assets/reference/props/v{N}/`
- **생성 시점**: STEP 09 Phase 1 (씬 이미지 생성 전 Canonical Shot 우선 확정)

### ElevenLabs Voice ID
- `_meta.md`의 `VOICE_ID` 항목에 프로젝트 시작 시 1회 설정

### STEP 05 Flow 이미지 모델 선택
STEP 04 시작 시 NB-Pro(Gemini 3 Pro) vs NB2(Gemini 3.1 Flash) 중 1회 선택
→ `04_shot_composition/{RUN_ID}/ANCHOR.md` 헤더 `FLOW_MODEL:` 기록

---

## 14. Shot Record YAML 스키마 (공통 참조)

**델타 모델**: 각 단계는 담당 필드만 별도 파일(delta)로 출력한다.

### 필드 담당 STEP 매핑

| 필드 | 담당 STEP | 데이터 타입 | 비고 |
|------|----------|------------|------|
| `shot_id` | 04 | int | 전역 순번, 0부터 |
| `section` | 04 | enum | 6종 Section |
| `local_id` | 04 | int | Section 내 순번 |
| `duration_est` | 04 | string | `{N}s` 형식 |
| `emotion_tag` | 04 | enum | 5종 감정 태그 (§16 참조) |
| `narration_span` | 04 | text | 대본 발췌 |
| `scene_type` | 04 | enum | 6종 씬 유형 (§15 참조) |
| `creative_intent` | 04 | text | 6-tag 구조: [공간][소품][카메라][조명][감정선][이전샷] |
| `emotion_nuance` | 04 | string (optional) | 15종 뉘앙스 (미기재 시 tag 기본 뉘앙스) |
| `pose_archetype` | 04 | string (optional) | 15종 포즈 아키타입 (H1~T3) |
| `line_of_action` | 04 | enum | 에너지 라인 (S-curve, C-curve, 역C-curve 등 — pose-repertoire.md 참조) |
| `silhouette_note` | 04 | string (optional) | 실루엣 판독성 메모 (예: "측면 실루엣, 한 손 가리킴") |
| `prop_refs` | 04 | list | ANCHOR 소품명 |
| `costume_refs` | 04 | list | ANCHOR 변장명. 빈 배열 = 기본 해빛 (정상). 변장 시만 기재 (예: [stephenson]) |
| `secondary_chars` | 04 | list | 보조 인물명 리스트 |
| `has_human` | 04→05 | enum | `main` / `anonym` / `none`. 05에서 최종 확정. ref_images 캐릭터 소스의 유일한 결정 키 |
| `ref_images` | 05 | list | 참조 이미지 경로 배열 (순서 = 서수 참조). visual-director가 완전 구성. style_ref + 캐릭터 ref + 소품 ref 모두 포함 |
| `thinking_level` | 05 | enum | `high` (기본) / `low` |
| `flow_prompt` | 05 | text | 순수 한국어 서술형 4단락 |
| `iv_prompt` | 05 | text | Veo 3 I2V 프롬프트 |
| `scene_id` | 06 | int | 나레이션 Scene 그룹 |
| `el_narration` | 06 | text | Audio Tag 포함 |
| `bgm` | 06 | string | EL 프롬프트 포함 |
| `sfx` | 05 (iv_prompt) | string | Veo 3 iv_prompt [AUDIO]에서 생성. STEP 06 delta에는 미포함 |
| `volume_mix` | 06 | string | 비율 표기 |
| `visual_lead` | 04 | string (optional) | `{N}s` 형식. 이미지가 나레이션보다 먼저 등장하는 시간. 기본값 `0s` (동시). §17 참조 |
| `asset_path` | 04 | path | `09_assets/images/{RUN_ID}/shot{N}.png` |
| `status` | 05 | emoji | ⏳ / ✅ |
| | | | |
| **— Hook 확장 필드 (SECTION00_HOOK 전용) —** | | | |
| `hook_media_type` | 05 | enum | `image` (기본) / `video` |
| `video_start_image` | 06 | path | 시작 프레임 이미지 경로. `hook_media_type: video`일 때 필수 |
| `video_end_image` | 06 | path \| null | 끝 프레임 이미지 경로. nullable (없으면 AI 자유 생성) |
| `video_prompt` | 06 | text | Veo3 모션 프롬프트. `hook_media_type: video`일 때 필수 |
| `video_duration` | 05 | string | 클립 길이 `{N}s`. `hook_media_type: video`일 때 필수 |
| `video_engine` | 05 | enum | `veo3` (기본) / `kling` |
| `hook_type` | 02→05 | enum | `standard` (기본) / `song` |
| `suno_style` | 07 | text | Suno Style 필드. `hook_type: song`일 때 필수 |
| `suno_lyrics` | 07 | text | Suno Lyrics (Metatags 포함). `hook_type: song`일 때 필수 |
| `suno_params` | 07 | object | `{instrumental: false, negative_tags: ...}`. `hook_type: song`일 때 필수 |

### Hook 확장 필드 규칙

- **적용 범위**: `SECTION00_HOOK` Shot에만 적용. 다른 Section에서는 무시
- **기본값**: `hook_media_type: image`, `hook_type: standard` → 기존 동작과 동일
- **Video Hook 연출 모드** (2종):
  - **Mode A — Kinetic Transition (권장)**: 연속 KF 이미지를 start/end로 사용. 캐릭터 이동+모션 블러로 장면 전환
    - `flow_prompt` = **단일** (해당 KF 이미지 생성용, v3 순수 한국어)
    - `video_start_image` = 자기 Shot 이미지 (`09_assets/images/{RUN_ID}/shot{N}.png`)
    - `video_end_image` = 다음 Shot 이미지 (`09_assets/images/{RUN_ID}/shot{N+1}.png`)
    - `video_prompt` = 영어, KF_N → KF_{N+1} 키네틱 트랜지션 묘사
    - 마지막 KF = landing frame (`hook_media_type: image`, video_prompt 없음)
    - 의상 전환 가능: 모션 블러/증기가 캐릭터를 가리는 순간 costume 변경
  - **Mode B — Per-Shot (레거시)**: Shot별 start/end 이미지 분리 생성. 제자리 변환
    - `flow_prompt[start]` + `flow_prompt[end]` 분리 작성
    - `video_start_image` = `shot{N}_start.png`, `video_end_image` = `shot{N}_end.png`
- **이미지 생성 순서**: Video Hook → Phase 0 (Hook 이미지 우선) → Phase 1 (ANCHOR) → Phase 2 (씬)
- **Song Hook 가사 기준**: 80~120 음절, 6~10줄, 30초 (중간 템포 ~4음절/초)
- **상세 규칙**: `.claude/agents/visual-director/video-hook-rules.md` 참조

---

## 15. Scene Type 정의

| 유형 | 설명 | 사용 시점 |
|------|------|-----------|
| `Doodle-Illust` | 정적 두들 일러스트 | 개념·메타포 시각화 |
| `Doodle-Animation` | 두들이 그려지는 과정 | 프로세스·변화·흐름 묘사 |
| `Text-Motion` | 핵심 키워드 타이포그래피 | 인용구·강조 키워드 |
| `Doodle-Character` | 해빛 캐릭터 등장 | Hook·질문·전환점 |
| `Doodle-Diagram` | 두들 스타일 도표·차트 | 수치·비교·구조 설명 |
| `Whiteboard-Reveal` | 화이트보드 그림 등장 | 개념 전개·단계 설명 |

> ❌ 사용 금지: B-roll, AI Video, Infographic, 실사 사진, 포토리얼, 3D 그래픽

---

## 16. 공통 출력 파일 구조

### Shot별 파일 헤더 표준

```markdown
# shot{shot_id:02d}.md
SECTION: {TITLECARD | SECTION00_HOOK | SECTION01 | SECTION02 | SECTION03 | SECTION04_OUTRO}
SHOT_ID: {shot_id}
INPUT_REF: {이전 단계 파일 경로}
MODEL: {사용 모델}
CREATED: {날짜}

---
```

### Section별 디렉토리 패턴

```
{단계폴더}/
  └── {RUN_ID}/
      ├── TITLECARD/shot00.md
      ├── SECTION00_HOOK/shot01.md ...
      ├── SECTION01/
      ├── SECTION02/
      ├── SECTION03/
      └── SECTION04_OUTRO/
```

- **Shot 1개 = 파일 1개**: 05~08 전 단계 공통
- **Run 폴더**: `run001/` (매니페스트) 또는 `v1/` (레거시)

### 감정 태그 정의 (5종)

| 태그 | 의미 | 대표 장면 |
|------|------|-----------|
| `HUMOR` | 코믹·유머 비트 | 자기비하, 과장 반응 |
| `REFLECTIVE` | 성찰·사유의 여백 | 철학적 질문, 조용한 은유 |
| `AWE` | 경외·압도감 | 거대한 것과 작은 캐릭터 |
| `REVEAL` | 반전·아하! 순간 | 개념 전환점, 핵심 키워드 |
| `TENSION` | 긴장·압박 | 빚쟁이 그림자, 위기 장면 |

---

## 17. Visual Lead — 이미지-나레이션 타이밍 분리

스틸 이미지 시퀀스(SECTION01~OUTRO)에서 이미지 등장과 나레이션 시작 시점을 분리하여 시청자 경험을 제어한다.

### `visual_lead` 필드

```yaml
visual_lead: 2s   # 이미지가 나레이션보다 2초 먼저 등장
```

| 값 | 의미 | 타이밍 |
|----|------|--------|
| `0s` (기본) | 이미지+나레이션 동시 | 대부분의 shot |
| `1s`~`3s` | **Visual Lead** — 이미지가 먼저 | Scale Shock, AWE, 발견 경로가 필요한 shot |
| 미기재 | `0s`과 동일 | 하위 호환 |

### 적용 가이드

| 조건 | visual_lead | 이유 |
|------|-------------|------|
| Scale Shock (이전 shot 대비 크기 3배+ 변화) | `2s`~`3s` | 시청자가 크기 충격을 먼저 체감한 후 나레이션이 해설 |
| AWE (여백 80%+, 캐릭터 ≤5%) | `2s` | 발견의 여정(눈이 그림을 탐색)에 시간 필요 |
| REVEAL (반전) | `0s`~`1s` | 나레이션 단어와 이미지의 동시 타격 또는 약간의 선행 |
| Breath / PAUSE | `0s` | 나레이션 없으므로 무관 |
| 일반 서사 shot | `0s` | 기본 동시 등장 |

### duration_est와의 관계

```
실제 shot 체류 시간 = visual_lead + 나레이션 길이 + visual_tail(자연 여운)
duration_est ≈ 위 값의 근사치
```

> 수동 편집에서 최종 타이밍 결정. `visual_lead`는 편집자에게 의도를 전달하는 가이드.
