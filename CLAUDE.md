# ecowise-pipeline v0.4 — Claude 작업 가이드

> 해빛 YouTube 영상 제작 파이프라인. Shot Record 중심.

---

## 파이프라인 구조

```
STEP 02    content-planner      sonnet  기획안 (02_planning)
STEP 03 script-director      opus    대본 (03_script_final/ — Phase A: draft → 사용자 승인 → Phase B: final)
STEP 04A   shot-composer        opus    나레이션 배분 → narration_map (사용자 승인)
Phase 1    generate_images      NB2 API 비주얼 ANCHOR 이미지 생성
STEP 04B   shot-composer ×5     opus    섹션별 병렬 → Shot base 파일
  ↓
┌─ STEP 05  visual-director  opus    창의적 장면 연출 → 05 delta  ┐ 병렬
└─ STEP 06  audio-director   haiku   나레이션+오디오 태깅 → 06 delta┘
  ↓
MERGE      merge_records.py  스크립트  04 base + 05 + 06 → Shot Record
  ↓
STEP 11    youtube-publisher sonnet  YouTube 업로드 메타데이터 확정 (10_youtube_publish)
```

> **STEP 04A**: 단일 에이전트 — narration_map 생성 후 사용자 승인 대기.
> **STEP 04B**: 섹션별 5개 병렬 에이전트 — narration_map의 shot_id 범위를 각자 처리.
> **STEP 05, 06은 병렬 서브에이전트** — 각각 04만 읽어 delta 출력.
> **오케스트레이터**: `run-director` 에이전트 — 전체 파이프라인 조율, 스크립트 직접 실행.

---

## 버전 관리 (Run-Based)

`version_manifest.yaml` 중앙 매니페스트로 단계 간 버전을 통합 관리한다.

### 개념
- **Run**: 파이프라인 1회 실행 단위 (run001, run002, ...)
- **부분 업데이트**: SECTION01만 수정 → `new-run --sections SECTION01` → 나머지 Section은 이전 run 폴백
- **레거시 호환**: 매니페스트 없으면 기존 `v1/`~`vN/` 폴더 자동 탐색

### 버전 관리 (version-manager — Python 스크립트)
```bash
VM=".claude/skills/version-manager/scripts/version_manager.py"
python $VM --project CH02 init|new-run|bump|status
```

### 상태 확인 (check-status — Python 스크립트)
```bash
CS=".claude/skills/check-status/scripts/check_status.py"
python $CS --project CH02
```

### 스크립트 호출 (각 스킬 폴더 내 스크립트)
매니페스트 있으면 `--version` 생략 시 자동 해상도. 레거시 강제는 `--version v1`.
```bash
RD=".claude/skills/run-directing/scripts"
GI=".claude/skills/generate-images/scripts"
GV=".claude/skills/generate-videos/scripts"

python $RD/validate_image_prompt.py --project CH02  # MERGE 전 의무 실행 (image_prompt 구조 검증)
python $RD/merge_records.py --project CH02  # MERGE 실행
python $RD/validate_shot_records.py --project CH02
python $GI/generate_images.py --project CH02                          # Phase 2 씬 이미지: 섹션별 병렬 실행 권장 (--section 옵션)
python $GV/generate_videos.py --project CH02
```

### 폴더 구조 (매니페스트 모드)
```
projects/CH02/
  version_manifest.yaml
  04_shot_composition/run001/{SECTION}/shot{N}.md   ← SECTION00_HOOK ~ SECTION04_OUTRO (TITLECARD 없음)
  05_visual_direction/run001/{SECTION}/shot{N}.md
  06_audio_narration/run001/{SECTION}/shot{N}.md
  07_shot_records/run001/{SECTION}/shot{N}.md + 07_ALL.txt
  09_assets/images/run001/shot{N}.png
  09_assets/videos/run001/shot{N}.mp4               ← Video-First: 전 Shot 비디오 생성
```

> **미변경**: `characters/v5/`, `props/v5/` 등 Phase 1 레퍼런스 — 독립 버전 체계 유지.

### 스타일 정의 (채널 공통)
```
assets/reference/style/
├── sempe-ink.yaml    ← 현재 기본 스타일 (Sempé Fine Ink)
└── README.md
```
> 스타일 변경 시 YAML 파일 1개만 수정하면 전 파이프라인(STEP 04 ANCHOR + STEP 05 image_prompt)에 반영.
> ANCHOR.md 헤더에 `STYLE: sempe-ink` 기재 → 에이전트가 `assets/reference/style/{STYLE}.yaml` 읽음.

---

## 규칙 문서 참조

| 규칙 | 파일 |
|------|------|
| 행동 규칙 (§1,2,5~9,11,13) | `.claude/rules/pipeline-rules.md` |
| 파일 네이밍·저장 위치·스키마 | `.claude/rules/pipeline_reference.md` |
| 피드백 루프 규약 (역방향 통신) | `.claude/rules/feedback-protocol.md` |

에이전트 / 스킬 위치:
- 오케스트레이터: `.claude/agents/run-director.md` (sonnet)
- STEP 02: `.claude/agents/content-planner.md` (sonnet)
- STEP 03: `.claude/agents/script-director.md` (opus)
- STEP 04: `.claude/agents/shot-composer.md` (opus)
- STEP 05: `.claude/agents/visual-director.md` (opus)
- STEP 06: `.claude/agents/audio-director.md` (haiku)
- 품질 검토: `.claude/agents/prompt-auditor.md` (haiku)
- STEP 11: `.claude/agents/youtube-publisher.md` (sonnet)
- 워크플로우: `.claude/skills/run-directing/`, `run-planning/`, `check-status/`, `start-project/`
- 이미지: `.claude/skills/generate-images/`
- 영상: `.claude/skills/generate-videos/`
- 에이전트 템플릿: `.claude/agent-template.md`

---

## 필수 파일 구조 규칙

### 저장 위치 ({RUN_ID} 또는 vN/ + per-shot 파일)
```
04_shot_composition/{RUN_ID}/ANCHOR.md            ← 전역 단일 소스
04_shot_composition/{RUN_ID}/{SECTION}/shot{N}.md ← STEP 04 base
05_visual_direction/{RUN_ID}/{SECTION}/shot{N}.md ← STEP 05 delta (ref_images + thinking_level + image_prompt + iv_prompt + has_human + asset_path)
06_audio_narration/{RUN_ID}/{SECTION}/shot{N}.md  ← STEP 06 delta (el_narration + bgm + volume_mix)
07_shot_records/{RUN_ID}/{SECTION}/shot{N}.md     ← 병합 완성본 (merge_records.py)
07_shot_records/{RUN_ID}/07_ALL.txt               ← ElevenLabs 통합본 (merge_records.py)
09_assets/images/{RUN_ID}/shot{N}.png             ← 전역 shot_id만 사용
09_assets/reference/characters/v{N}/{인물명}.jpeg   ← Phase 1 레퍼런스 (독립 버전)
09_assets/reference/props/v{N}/{소품명}.jpeg
assets/reference/style/character_reference.jpeg  ← 채널 공통 (프로젝트 상위)
```

> `{RUN_ID}` = 매니페스트 모드: `run001` | 레거시: `v1`

### 자주 실수하는 규칙 (위반 금지)
- **Shot 1개 = 파일 1개** (모든 단계 공통)
- **버전은 폴더로** — 파일명에 `_v1` 접미사 붙이지 않음
- **수정 재생성**: `new-run --sections SECTION01`로 새 run 생성 (레거시: `v{N+1}/`)
- **STEP 05는 prompt engineering + scene staging** — shot-composer 결정을 서술형으로 변환, 약한 부분 보강 가능
- **ANCHOR 신규 생성 금지** — STEP 05는 05 ANCHOR 참조만
- **NB2 품질 접미사 금지** — `4k`, `masterpiece`, `HD` 사용하면 품질 저하

---

## NB2 image_prompt 핵심 규칙 (v3 — 순수 한국어 자연어)

> 상세 규칙은 `.claude/agents/visual-director.md` 참조.
> visual-director, prompt-auditor 에이전트는 해당 파일의 규칙을 따른다.
> v3 전용 파이프라인. v2 구조적 태그는 더 이상 지원하지 않는다.

### 순수 한국어 서술형 포맷 (v3 간소화 — THIS {name} + style_ref)

image_prompt는 **순수 한국어 서술형** 4단락으로 작성한다. 구도/감정/채색에만 집중.
style_ref + 턴어라운드 시트가 외형/스타일을 담당하므로 image_prompt에서는 제거.

**API content 배열:**
```
THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:  ← style_ref (ref_images 첫 항목)
<style_ref.png>
THIS {name} — 이 대상의 형태만 따라 그려줘:  ← ref별 라벨 (자동)
<턴어라운드 시트>
(필요한 만큼 반복)
<image_prompt>
```

**YAML 구조:**
```yaml
ref_images:              # visual-director가 완전 구성 — generate_images.py는 그대로 전달
  - assets/reference/style/style_reference.png       # style ref (모든 shot 필수)
  - characters/run001/artisan.jpeg                   # 캐릭터 ref (has_human 기반)
  - props/run001/spinning_wheel.jpeg                 # 소품 ref
thinking_level: high     # API config용
image_prompt: |           # 순수 한국어 — 구도+감정+채색만
  THIS style의 드로잉 스타일로, 유튜브 교육 영상에 사용할
  서사적인 삽화 한 장을 그려줘.

  배경은 순백의 빈 공간이되, 바닥선이 희미하게 암시되어 있어.

  화면 좌측 하단에는 THIS artisan이 전체 화면의 약 10%,
  THIS spinning_wheel의 절반 크기로, 마치 거대한 세계 속
  하나의 점처럼 작게 앉아 있어. ...

  반드시 물레에만 deep amber 워시를 입혀줘 — 캐릭터는 참조 이미지의 색을 그대로 유지해줘.
```

**4단락 구조:**
| 단락 | 내용 |
|------|------|
| P1 | 과제 소개 — "THIS style의 드로잉 스타일로, ... 삽화 한 장을 그려줘." |
| P2 | 배경 (밀도 등급 L0~L5) |
| P3 | 구도/배치/크기 (THIS {name} 직접 참조) + 감정/포즈 |
| P4 | 채색 포인트 — 캐릭터는 ref 시트 색 유지. "반드시 {장면 대상}에만 {색} 워시를 입혀줘 — 캐릭터는 참조 이미지의 색을 그대로 유지해줘." |

**image_prompt에서 제거된 항목** (ref 이미지가 담당):
- ~~스타일 묘사~~ — style_ref 이미지가 지배
- ~~얼굴 규칙~~ — 턴어라운드 시트가 담당
- ~~REDRAW~~ — "THIS {name} — 이 대상의 형태만 따라 그려줘:" 라벨이 대체
- ~~카운트 제약~~ — 구도 묘사에서 요소가 명시됨
- ~~장면 가드~~ — 구도 묘사에서 장면이 명시됨

**has_human 기반 분기 (ref_images 결정의 유일한 키):**
| has_human | costume_refs | ref_images 캐릭터 소스 |
|-----------|-------------|----------------------|
| `main` | `[]` (기본 해빛) | style_ref + main_turnaround.jpeg |
| `main` | `[변장명]` | style_ref + characters/{RUN_ID}/{변장명}.jpeg |
| `anonym` | `[]` | style_ref + character_reference.jpeg |
| `none` | - | style_ref만 (캐릭터 ref 없음) |

> **ref_images 원칙**: visual-director가 완전 구성. generate_images.py는 추가/제거 없이 그대로 API에 전달.

추가 조건 분기: `secondary_chars` 존재 → 다중 캐릭터 패턴 (예: `[happy_rabbit]` = 보조 나레이터 캐릭터), L3+ 밀도 → 환경 구조물 패턴

> **보조 캐릭터 (happy_rabbit)**: 대본 `[보조]` 태그 장면에 사용하는 채널 공통 디지털 토끼 캐릭터.
> `secondary_chars: [happy_rabbit]` → ref_images에 `happy_rabbit.jpeg` 포함, image_prompt에서 `THIS happy_rabbit` 참조.
> **표정 규칙**: 디지털/스크린 형태로 표현 (LED 눈, 픽셀 표정). 아날로그 표정 금지.

**스타일 빌딩 블록**: `assets/reference/style/sempe-ink.yaml` E섹션 (활성: E1, E3~E4, E7, E10~E13)

---

## 컨텍스트 관리 전략

**`/clear` 실행 시점**:
- STEP 04 완료 → STEP 05+06 서브에이전트 실행 전
- 동일 작업 2회 수정 후에도 결과가 맞지 않으면 `/clear` + 프롬프트 재작성
- 무관한 작업으로 전환 시 `/clear`

**모델 전환**:
- STEP 02~05: `/model claude-opus-4-6` (복잡한 창의 작업)
- STEP 05: opus (창의적 장면 연출), STEP 06: haiku — 서브에이전트 정의에 모델 포함

---

## NB2 패턴 검토가 필요할 때

`prompt-auditor` 서브에이전트를 호출한다:
> "prompt-auditor로 `05_visual_direction/{RUN_ID}/SECTION01/` 의 image_prompt를 검토해줘"

---

## Shot Record YAML 필수 필드 (빠른 참조)

```yaml
shot_id:         # 전역 순번 (1부터 — TITLECARD 없음)
section:         # SECTION00_HOOK ~ SECTION04_OUTRO (5종)
local_id:        # Section 내 순번
clip_rhythm:     # quick (3-4s) / standard (5-6s) / breath (6-7s) — STEP 04
duration_est:    # 초 (float)
emotion_tag:     # 단일 태그 (5종: HUMOR/REFLECTIVE/AWE/REVEAL/TENSION)
emotion_nuance:  # 15종 뉘앙스 (선택, 미기재 시 tag 기본값) — STEP 04
pose_archetype:  # 15종 포즈 아키타입 H1~T3 (선택) — STEP 04
has_human:       # main/anonym/none (main=특정 캐릭터, anonym=익명 실루엣·군중, none=사람 없음)
scene_type:      # pipeline_reference.md §15 참조
narration_span:  # [시작초, 끝초]
creative_intent: # [공간][소품][카메라][조명][감정선][이전샷] — [카메라]에 모션 시퀀스 포함
costume_refs:    # 인물명 목록 (변장 있을 때)
prop_refs:       # 소품 파일명 목록
secondary_chars: # 보조 인물 (직접 등장 여부 포함)
ref_images:      # STEP 05 작성 (v3) — 참조 이미지 경로 배열 (서수 참조 순서)
thinking_level:  # STEP 05 작성 (v3) — high (기본) / low
image_prompt:     # STEP 05 작성 — v3: 순수 한국어 서술
iv_prompt:       # STEP 05 작성 — Veo 3 I2V 모션 프롬프트 (Canvas vs Director: 동작+카메라+환경만)
el_narration:    # STEP 06 작성
bgm:             # STEP 06 작성
sfx:             # STEP 06 작성
volume_mix:      # STEP 06 작성
asset_path:      # 09_assets/images/{RUN_ID}/shot{N}.png
status:          # pending / done

# --- Hook 확장 필드 (SECTION00_HOOK 전용, 조건부) ---
hook_media_type: # video (기본) — Video-First
hook_type:       # standard (기본) / song — STEP 02→05
video_duration:  # 클립 길이 — hook_media_type: video일 때
video_engine:    # veo3 (기본) / kling — hook_media_type: video일 때
video_prompt:    # Veo3 모션 프롬프트 — STEP 05 작성, video일 때
suno_style:      # Suno Style 필드 — STEP 06 작성, song일 때
suno_lyrics:     # Suno Lyrics (Metatags 포함) — STEP 06 작성, song일 때
suno_params:     # Suno 파라미터 — STEP 06 작성, song일 때
```

> 스키마 전체: `.claude/rules/pipeline_reference.md §14`
