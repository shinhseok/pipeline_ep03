# QA Issue Report — CH02 run001
DATE: 2026-03-10
SCOPE: STEP 06 visual-direction + generate_images.py + shot 파일 품질

---

## 발견 이슈 전체 목록

| # | Shot | 카테고리 | 증상 | 상태 |
|---|------|---------|------|------|
| 1 | 전체 | PIPELINE | SECTION_ORDER에 TITLECARD 누락 → shot00 미생성 | ✅ 해결 |
| 2 | 전체 | REF_MISSING | basic_charater_ref.png 파일명 오타 (charater vs charector) → 레퍼런스 미첨부 | ✅ 해결 |
| 3 | 전체 | STYLE | "Use color pencil rendering" 구지침이 art_style과 충돌 | ⚠️ 부분 해결 |
| 4 | 전체 | FIELD_CONFLICT | composition / action / appearance 필드 경계 미정의 → 중복 기술로 AI 혼란 | ✅ 해결 |
| 5 | shot25 | MARGIN | 여백 미표현 (캐릭터가 가장자리까지 채움) | ✅ 해결 |
| 6 | shot25 | COMPOSITION | CU + 팔 동작 → 캐릭터 3/4 잘림 | ✅ 해결 |
| 7 | shot25 | STYLE | safe zone 안쪽에 노란빛 배경 + 사각프레임 경계 | 🔄 진행 중 |
| 8 | shot33 | CHARACTER | 몸 채색 색상이 레퍼런스와 다름 | 🔄 진행 중 |
| 9 | shot45 | STYLE | 노란빛 배경 + 종이 질감 + 사각프레임 경계 | 🔄 진행 중 |

---

## 해결 완료 항목

### #1 — TITLECARD 미생성 (PIPELINE)
- **원인**: `generate_images.py` `SECTION_ORDER` 리스트에 `"TITLECARD"` 누락
- **수정**: `SECTION_ORDER` 첫 번째 항목으로 `"TITLECARD"` 추가
- **파일**: `.claude/skills/generate-images/scripts/generate_images.py`

### #2 — basic_charater_ref.png 레퍼런스 미첨부 (REF_MISSING)
- **원인**: 실제 파일명 `basic_charector_ref.png` vs 프롬프트 참조 `basic_charater_ref.png` 불일치
- **수정**: `resolve_ref_path()`에 `basic_char*ref*.png` glob 폴백 추가
- **파일**: `.claude/skills/generate-images/scripts/generate_images.py`

### #3 — "Use color pencil rendering" 구지침 (STYLE) — 부분 해결
- **원인**: visual-director.md 템플릿에 있던 구지침이 art_style 정의와 충돌
- **수정 완료**: `visual-director.md` 템플릿에서 제거 + shot01, shot04, shot05, shot09, shot22, shot25, shot33, shot45에서 제거
- **미완료**: 나머지 shot 파일(shot02~03, shot06~08, shot10~21, shot23~24, shot26~32, shot34~44)에 아직 잔존 가능
- **다음 액션**: 전체 06_visual_direction/run001 파일 일괄 검색·제거 필요

### #4 — composition/action/appearance 필드 경계 (FIELD_CONFLICT)
- **원인**: 필드 간 역할 미정의 → AI가 동일 정보를 중복 해석하거나 충돌 처리
- **수정**: `visual-director.md`에 필드 경계 규칙 명시
  - `composition`: 공간 배치만 (위치, 비율, 여백) — 신체 묘사·동작·소재 금지
  - `action`: 동적 동사만 — 정적 상태는 `appearance`로
  - `appearance`: ANCHOR Layer 4 그대로 + 장면 상태

### #5, #6 — shot25 여백·캐릭터 잘림
- **원인**: composition에 "fill the left half" 등 가장자리 채움 표현 + CU 샷에 팔 동작 기술 누락
- **수정**: composition safe zone 언어 적용 + "양팔·시계 완전히 프레임 내" 명시 + action에서 "Upper torso visible." 제거

---

## 진행 중 이슈 (미해결)

### #7 — shot25 사각프레임 / 노란배경 섬 현상 (STYLE)
- **증상**: safe zone 내부 영역이 노란빛 배경으로 채워지고 주변과 사각 경계로 구분됨
- **근본 원인 분석**:
  1. "safe zone / inner 70%" 용어 → AI가 해당 영역을 배경색으로 채우는 사각형 박스로 해석
  2. art_style의 "peach watercolor washes"가 배경에 적용됨
  3. art_style의 "off-white background" (→ "pure white"로 수정했으나 효과 미확인)
- **적용한 수정**:
  - art_style: `off-white background` → `pure white background`
  - constraints: "safe zone / 70% / 15%" 표현 제거 → "generous white breathing room" 으로 교체
  - constraints: "워터컬러 워시는 요소에만, 배경 무색" 추가
  - constraints: "요소는 순백 표면 위에 자연스럽게 부유" 추가
- **마지막 재생성**: 2026-03-10 (결과 미확인 — 작업 중단)
- **다음 액션**: 재생성 이미지 확인 후 효과 판단, 필요 시 art_style 추가 수정

### #8 — shot33 몸 채색 색상 불일치 (CHARACTER)
- **증상**: 캐릭터 몸 색상이 레퍼런스 이미지와 다름
- **근본 원인 분석**:
  - `generate_images.py` `IMAGE_LABELS["basic_charater_ref"]`가 "Ignore colors" 지시 → AI가 임의 색상 사용
  - ~~appearance에 `#2D2D20` 명시 시도~~ → 구지침, 레퍼런스 색상과 불일치 확인 후 제거
- **적용한 수정**:
  - IMAGE_LABELS: "Ignore colors" → "Extract body silhouette, proportions, AND the dark charcoal body base color"
  - appearance: `#2D2D20` 추가 후 제거 (구지침 확인)
- **마지막 재생성**: 2026-03-10 (결과 미확인 — 작업 중단)
- **다음 액션**: 재생성 이미지로 IMAGE_LABELS 수정 효과 확인

### #9 — shot45 노란빛 배경 / 종이 질감 (STYLE)
- **증상**: safe zone 내부에 노란빛이 돌고 종이 질감이 표현됨, 사각프레임 경계 발생
- **근본 원인**: shot25 #7과 동일 + WS(Wide Shot)로 빈 공간 면적이 넓어 더 두드러짐
- **적용한 수정**: shot25 #7과 동일 수정 적용
- **마지막 재생성**: 2026-03-10 (결과 미확인 — 작업 중단)
- **다음 액션**: 재생성 이미지 확인

---

## 시스템 레벨 변경 사항 (이번 세션 적용)

| 파일 | 변경 내용 |
|------|---------|
| `.claude/agents/visual-director.md` | art_style `off-white` → `pure white` / constraints 템플릿: safe zone 용어 제거, floating 제약 추가 / 필드 경계 규칙 추가 |
| `.claude/skills/generate-images/scripts/generate_images.py` | SECTION_ORDER에 TITLECARD 추가 / basic_char*ref glob 폴백 / IMAGE_LABELS["basic_charater_ref"] Ignore colors 제거 |
| `.claude/skills/qa-images/SKILL.md` | 신규 생성 (QA 4-Phase 워크플로우) |

---

---

## 2026-03-10 2차 세션 추가 수정

### #3 완전 해결 — "color pencil rendering" 잔존 파일 일괄 제거
- 38개 파일에서 trailing comma 포함 완전 제거 완료

### #8 IMAGE_LABELS 원복
- 몸 색상은 art_style 태그에서 처리 → IMAGE_LABELS는 실루엣/비율만 추출 (Ignore colors)
- `IMAGE_LABELS["basic_charater_ref"]`: 이전 "dark charcoal" 수정 취소 → 원래 "Ignore colors" 로직 유지

### #10 NEW — "safe zone" / "inner 70%" 구도-충돌 이슈 (시스템 레벨)
- **증상**: composition 필드의 "safe zone" / "inner 70% working area" 표현 → AI가 시각적 경계 박스로 해석 → #7/#9 노란배경·사각프레임 현상의 근본 원인
- **수정 완료**:
  - `visual-director.md` template: composition 가이드에서 "safe zone"/"inner 70%" 완전 제거, 자연 캔버스 좌표 언어로 교체
  - `visual-director.md` self-check: "safe zone/inner 70% 금지" 항목으로 교체
  - shot04, shot05, shot09, shot22, shot45: composition 필드 자연 좌표 언어로 수정
  - shot04, shot05, shot09, shot22: 구식 constraints("inner 70%") → 신식 3개 constraints
  - 전체 46개 파일: `off-white background` → `pure white background` 일괄 치환

### 재생성 필요 Shot 목록
| Shot | 이유 |
|------|------|
| shot04 | composition/constraints/art_style 수정 |
| shot05 | composition/constraints/art_style 수정 |
| shot09 | composition/constraints/art_style 수정 |
| shot22 | composition/constraints/art_style 수정 |
| shot25 | 오생성 (포토리얼 박제 인형 — 완전 wrong output) |
| shot33 | 채색 불일치 + IMAGE_LABELS 재수정 |
| shot45 | composition 수정 + art_style 수정 |

---

### #11 NEW — 프레임 경계 반복 발생 (STYLE — 시스템 레벨)
- **근원 원인**: constraints의 부정형 "Do NOT add any panel border..." → AI가 "frame" 개념을 활성화해 역효과
- **수정**: 긍정형으로 교체 — "Draw all elements directly on the open white canvas — the scene has no border, no frame, no enclosing box of any kind."
- **적용 범위**: 전체 46개 shot 파일 + visual-director.md 템플릿

### #12 NEW — 소품 누락 (COMPOSITION — 시스템 레벨)
- **근원 원인**: `composition` 필드에 소품 위치가 없으면 AI가 레퍼런스 이미지(캐릭터+의상)에만 집중하고 props 블록 무시
- **수정**: `visual-director.md` 템플릿 — composition에 모든 소품 공간 위치 필수 기술 + self-check 항목 추가
- **적용 범위**: visual-director.md 템플릿 (신규 생성 shot에 자동 적용)

---

## STATUS: RESOLVED
- 전체 이슈 해결 완료 (2026-03-10 2차 세션)
- shot04, 05, 09, 22, 25, 33, 45 재생성 완료 및 검수 통과
