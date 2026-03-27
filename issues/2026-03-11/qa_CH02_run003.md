# QA Issue Report — CH02 run003
DATE: 2026-03-11
SCOPE: STEP 06 visual-direction flow_prompt 내부 구조 + 이미지 QA + 파이프라인 아키텍처

---

## 핵심 발견: visual-director 지침 준수 실패의 근원

### 구조적 근본 원인 (3 Layer)

**Layer 1 — 생성 에이전트 = 검증 에이전트 (가장 근본적)**
- Self-Check를 실행하는 주체가 오류를 생성한 동일한 에이전트
- 확증 편향: 잘못 생성한 Shot이 자가 검토에서 통과됨
- → 해결책: 코드 기반 자동 검증 (`validate_flow_prompt.py`)

**Layer 2 — 순차 생성 중 컨텍스트 드리프트**
- Shot 1에서 형성된 오류 패턴이 Shot 83까지 "정상 패턴"으로 굳어져 복제됨
- 470줄 문서에서 핵심 규칙을 매 Shot마다 재확인하지 않음
- → 해결책: 고정 요소를 사전 완성 Base Template으로 분리

**Layer 3 — 고정 요소와 조건부 요소 혼재**
- TASK block, REDRAW constraint 등 `◆ ALL` 항목이 470줄 문서에 산재
- LLM이 매 Shot마다 "고정인가 조건부인가" 재판단 → 누락 발생
- → 해결책: 필수 고정 블록을 문서 최상단에 독립 섹션으로 분리

**Layer 4 — prompt-auditor가 선택적 실행**
- flow_prompt 내부 구조 검증이 의무 게이트가 아님
- → 해결책: `validate_flow_prompt.py` → merge 전 의무 실행

---

## 발견 이슈 전체 목록

### 시스템 레벨 (전체 83개 Shot 영향)

| # | 카테고리 | 증상 | 영향 Shots | 상태 |
|---|---------|------|-----------|------|
| S1 | REDRAW_MISSING | REDRAW constraint 전면 누락 — 채색 누락 직접 원인 | 전체 83개 | ✅ 해결 (visual-director.md) |
| S2 | TASK_BLOCK_MISSING | TASK block 전면 누락 — 레퍼런스 시트 모드 전환 위험 | 전체 83개 | ✅ 해결 (visual-director.md) |
| S3 | BACKGROUND_VALUE | background 고정값 불일치 (Pure solid white vs Bare white canvas) | 전체 83개 | ✅ 해결 (visual-director.md) |
| S4 | ARTSTYLE_BG_EXPR | art_style에 "pure white background" 배경 색상 표현 포함 | 전체 83개 | ✅ 해결 (visual-director.md) |
| S5 | VALIDATE_MISSING | flow_prompt 자동 검증 스크립트 부재 | — | ✅ 해결 (validate_flow_prompt.py 신설) |

### Shot 레벨

| # | Shot | 카테고리 | 증상 / 원인 | 상태 |
|---|------|---------|------------|------|
| 1 | 01, 02 | PROP_INCONSISTENCY | 알람시계(shot01) vs 스마트폰(shot02) 불일치 — 연속 아침 장면 소품 불일치 | ✅ 해결 |
| 2 | 06 | CONTENT_POLICY | 파이프 흡연 연출 — 콘텐츠 가이드라인 위반 → 찻잔으로 교체 | ✅ 해결 |
| 3 | 13,17,30,33,44,53,54,56 | REF_CONFLICT | [CHARACTER SOURCE] + [BASE BODY REFERENCE] 동시 포함 → 무채색 ref가 의상 채색 억제 | ✅ 해결 |
| 4 | 23 | DEPRECATED_IDENTIFIER | "THIS WISEMAN in CAPPED costume" 형식 → "THIS CAPPED" 수정 + 동일 identifier 2개 | ✅ 해결 |
| 5 | 10 | STYLE_ISOLATION | scene_description에 "dense cross-hatch ink strokes", "heavy pencil hatching" — 스타일 표현 금지 필드 혼입 | ✅ 해결 |
| 6 | 46 | STYLE_ISOLATION | props.description에 "red watercolor wash pooling", scene_description에 "bleeds slightly outside the lines" | ✅ 해결 |
| 7 | 12, 59, 64 | SILHOUETTE_FACE_CONFLICT | 실루엣(flat dark) 인물에 face constraint 적용 → 모순 지시 → NB2가 기본 미소 표정 렌더링 | ✅ 해결 |
| 8 | 33, 44, 53 | EMOTION_EXPR_MISSING | emotion_tag에 맞는 표정 매핑이 action에 없음 | ✅ 해결 |
| 9 | 25 | PROP_DUPLICATE | loom이 props 블록 + scene_description 두 곳에 묘사 → NB2가 2개 생성 가능 | ✅ 해결 |
| 10 | 18 | PROP_UNREGISTERED | jenny spinning frame이 ANCHOR 미등록, props 블록 없음 → NB2 자유 생성 | ✅ 해결 |
| 11 | 65 | HAS_HUMAN_FORM | disembodied hand — bean-shaped 캐릭터 형체 미준수 | ✅ 해결 |
| 12 | 68 | HAS_HUMAN_FORM | child-proportion hands — bean-shaped 캐릭터 형체 미준수 | ✅ 해결 |
| 13 | 54 | SCENE_DESIGN | 달력 전체 blank 설계 → 숫자/요일 있는 달력에 특정 셀만 비워야 자연스러움 | ✅ 해결 |
| 14 | 66 | MARGIN_CONFLICT | composition 15% 마진 + scene_description 아일 벽이 화면 채움 → 양립 불가 충돌 | ✅ 해결 |
| 15 | 73 | STYLE_MISMATCH | CHARACTER SOURCE 메인 캐릭터 + BASE BODY REFERENCE 군중 실루엣 혼합 → 스타일 차이 | ✅ 해결 |
| 16 | 17, 75 | TEXT_TRIGGER | TASK block 부재 + 모호한 묘사 → NB2 텍스트 라벨 추가 위험 | ✅ 해결 |
| 17 | 07 | SCENE_COMPLEXITY | XWS 원근감 골목 + 다수 요소 → NB2 재현 한계 | ✅ 해결 |
| 18 | 30, 81 | SCENE_COMPLEXITY | 소품 크기/투명도 조건 복잡 + REF_CONFLICT 복합 | ✅ 해결 (REF_CONFLICT 제거) |

---

## 시스템 레벨 해결 사항

### S1~S4 — visual-director.md 구조 개선

**MANDATORY FIXED BLOCKS 섹션 신설** (문서 최상단):
- TASK block, REDRAW constraint, background 고정값, art_style 고정값을 "절대 수정 불가 복사 블록"으로 명시
- 에이전트가 이 블록들을 선택적으로 포함/제외할 수 없도록 구조화

**Variant별 Base Template 추가**:
- A/B/C/D 각 Variant에 대해 고정 요소가 사전 채워진 copy-paste 템플릿 제공
- 에이전트는 `[FILL: ...]` 마커 부분만 채움
- 고정 요소는 템플릿에 이미 존재하므로 드리프트 불가

### S5 — validate_flow_prompt.py 신설

**자동 검증 항목:**
1. TASK block 존재 여부
2. REDRAW constraint 존재 여부
3. [CHARACTER SOURCE] + [BASE BODY REFERENCE] 동시 포함 여부
4. deprecated identifier "WISEMAN in" 패턴
5. background 고정값 준수 여부
6. art_style 배경 표현 혼입 여부
7. Style Isolation 위반 (금지어가 비스타일 필드에 있는지)
8. emotion_tag → 표정 매핑 누락 여부 (07 모드)

**파이프라인 통합:**
- `merge_records.py` 실행 전 의무 실행
- 오류 발견 시 merge 블로킹 (run-director.md에 명시)

---

## Shot 레벨 수정 근거 요약

### REF_CONFLICT 수정 (shots 13, 17, 30, 33, 44, 53, 54, 56)
- `[BASE BODY REFERENCE]` 줄을 SOURCE REFERENCES에서 제거
- `costume_refs` 있는 shot에 BASE BODY REFERENCE는 스타일 충돌 원인

### SILHOUETTE_FACE_CONFLICT 수정 (shots 12, 59, 64)
- face constraint 제거 → 실루엣 형체에 표정 강제 불가
- 대신 action에 "flat dark silhouette form, no visible facial features" 추가

### EMOTION_EXPR_MISSING 수정 (shots 33, 44, 53)
- visual-director.md 규칙: `action` 마지막에 `; {emotion_tag 표정}` 필수
- shot33 REFLECTIVE: `; eyes cast downward, mouth closed in quiet stillness`
- shot44 HUMOR: `; one eyebrow cocked high, corners of mouth curl into a lopsided grin`
- shot53 TENSION: `; eyes narrowed with worry, brow creased tight`

---

## 추가 고려 사항 (미래 방지)

### shot-composer.md 개선 예정 (다음 run)
1. 콘텐츠 금지 항목 추가 (흡연, 폭력)
2. 연속 Shot 간 소품 일관성 체크 규칙
3. ANCHOR 미등록 소품 사용 금지 명시

### 실루엣 Shot 규칙 신설 (visual-director.md)
- has_human:true + flat dark silhouette 형체: face constraint 적용 불가
- 신체 일부 Shot: bean-shaped 캐릭터 체형 유지 규칙 명시

### 군중 + 메인 캐릭터 혼합 Shot 규칙 신설
- CHARACTER SOURCE 메인 + 배경 군중 실루엣 혼합 시
- 군중 스타일 명시: "flat dark bean-shaped doodle silhouettes, same art_style"

---

## STATUS: RESOLVED (2026-03-11)

### Phase 3 수정 완료 요약

**시스템 레벨 (모든 83 shot 일괄 적용):**
- TASK block 추가 (`[thinking: high/low]` 두 패턴 모두 처리)
- REDRAW constraint 추가 (face constraint 있는 Variant A/C/D + 없는 Variant B 모두 처리)
- background 값 수정: "Pure solid white..." → "Bare white canvas. No fill or tint on empty areas."
- art_style 수정: ", pure white background" 제거
- constraints 문구 정규화: "Do NOT add any panel border..." → "Draw all elements directly on the open white canvas..."
- constraints 문구 정규화: "pure white throughout" → "bare white"

**Shot 레벨 (24 shots):**
- REF_CONFLICT 제거: shots 13, 17, 21, 24-29, 30-31, 33-35, 37-38, 44-45, 47, 49, 51, 53-54, 56, 64, 66-67, 69-70, 73, 77 (추가 발견 포함)
- DEPRECATED_ID 수정: shot23
- EMOTION_EXPR_MISSING 수정: shots 33, 44, 53, 81
- STYLE_ISOLATION 수정: shots 10, 46
- SILHOUETTE_FACE_CONFLICT 수정: shots 12, 59, 64
- CONTENT_POLICY 수정: shot06
- PROP_INCONSISTENCY 수정: shots 01, 02
- PROP_DUPLICATE 수정: shot25
- PROP_UNREGISTERED 수정: shot18
- HAS_HUMAN_FORM 수정: shots 65, 68
- SCENE_DESIGN 수정: shot54
- MARGIN_CONFLICT 수정: shot66
- STYLE_MISMATCH 수정: shot73
- TEXT_TRIGGER 수정: shots 17, 75

**최종 검증 결과 (validate_flow_prompt.py):**
- 오류: 0건 ✅
- 경고: 5건 (STYLE_ISOLATION — dense cross-hatch 표현 shots 11, 12, 63, 67)

**파이프라인 완료:**
- merge_records.py → 83개 Shot Record ✅
- render_storyboard.py → 83개 Storyboard (376s) ✅

**validate_flow_prompt.py 버그 수정 및 검증 항목 추가:**
- REF_CONFLICT 검사 범위를 [SOURCE REFERENCES] 섹션으로 한정 (TASK block의 [CHARACTER SOURCE] 언급이 오탐 유발 → 수정)
- THINKING_LEVEL_INVALID 체크 추가: `[thinking: low/medium]` → NB2 API가 지원하지 않아 이미지 생성 실패 원인

**추가 발견 (STEP 09 이미지 생성 중):**
- `[thinking: low]` 사용 shot들이 NB2 API 오류 발생 (shots 46, 65, 69, 75)
- 근원: visual-director가 Variant B (has_human: false) 등 일부 shot에 [thinking: low] 사용
- 해결: visual-director.md에 [thinking: high] 고정 명시 추가; 06_visual_direction 전체 일괄 교체 (43 files)

**재생성 필요 shot 목록 (STEP 09):**
01, 02, 06, 10, 12, 13, 17, 18, 21, 23, 25, 26, 30, 31, 33, 34, 35, 37, 38, 44, 45, 46, 47, 49, 51, 53, 54, 56, 59, 64, 65, 66, 68, 69, 70, 73, 75, 77, 81
