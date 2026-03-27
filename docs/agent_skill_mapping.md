# Agent Skill Mapping — 해빛 파이프라인

## 1. 전체 매핑 구조

```
/run-planning ──────────────────────────────────────────────────────────
  │
  ├── [PHASE 0] MCP 연결 확인
  │     └── notebooklm.list_notebooks
  │         ├── 성공 → PHASE 1 진행
  │         └── 실패 → 폴백: 파일 직접 입력 모드
  │
  ├── [PHASE 1~3] NotebookLM 소스 선택
  │     └── notebooklm.list_sources → notebooklm.ask_question
  │
  ├── [PHASE 4] 01_research 생성
  │
  ├── [PHASE 5] planner/SKILL.md → 02_planning [gemini-3.1-pro]
  │
  └── [PHASE 6] planner/SKILL.md → 04_script_final/{topic}_draft_v1.md [gemini-3.1-pro]


/run-directing ─────────────────────────────────────────────────────────
  │
  ├── [STEP 03~04] script-director/SKILL.md [claude-opus-4-6]
  │     └── INPUT: 02_planning
  │         OUTPUT: 04_script_final/{topic}_draft_v1.md → 04_script_final/{topic}_v1.md
  │
  ├── [STEP 05] shot-composer/SKILL.md [claude-opus-4-6]
  │     └── INPUT: 04_script_final
  │         OUTPUT: 05_shot_composition ANCHOR + Section별 Shot Record 골격
  │
  ├── [STEP 06] visual-director/SKILL.md [claude-opus-4-6]
  │     └── INPUT: 05_shot_composition (Section별)
  │         OUTPUT: 06_visual_direction (image_prompt 추가된 Shot Record)
  │
  ├── [STEP 07] shot-record-builder/SKILL.md [claude-haiku-4-5]
  │     └── INPUT: 05_shot_composition + 06_visual_direction (Section별)
  │         OUTPUT: 07_shot_records (el_narration/bgm/sfx 포함 완성 Shot Record) + 07 ALL
  │
```

---

## 2. Skill 상세 테이블

| Skill | 모델 | 입력 | 출력 | 핵심 역할 |
|-------|------|------|------|-----------|
| `planner` | gemini-3.1-pro | 01_research | 02_planning + 04_script_final/{topic}_draft | 기획·초안 생성 |
| `script-director` | claude-opus-4-6 | 02_planning | 04_script_final/{topic}_draft → {topic}_v1 | 대본 초안 + 해빛 페르소나 각색 |
| `shot-composer` | claude-opus-4-6 | 04_script_final | 05_shot_composition ANCHOR + Section별 | Shot 분해·창의 구성 결정 |
| `visual-director` | claude-opus-4-6 | 05_shot_composition (Section별) | 06_visual_direction/{SECTION}/shot{N}.md (Shot별) | creative_intent → Flow 프롬프트 변환 |
| `shot-record-builder` | claude-haiku-4-5 | 05 + 06 (Section별 배치) | 07_shot_records + 07_ALL.txt | el_narration + BGM/SFX/믹스 → 완성 Shot Record |

---

## 3. 모델 배정 및 비용 구조

| STEP | 작업명 | 모델 | 비용 등급 | 선택 근거 |
|------|--------|------|-----------|-----------|
| 02 | 분석 및 기획 | gemini-3.1-pro | 중간 | 복잡한 추론·SEO 기획 |
| 03~04 | 대본 작성 | **claude-opus-4-6** | 높음 | 초안 + 해빛 페르소나 각색 통합 |
| 05 | Shot 구성 | **claude-opus-4-6** | 높음 | Shot 분해·창의 연출 결정 (Disney/Pixar 원칙) |
| 06 | 비주얼 디렉팅 | **claude-opus-4-6** | 높음 | creative_intent → Flow 프롬프트 변환 (엔지니어링) |
| 07 | Shot Record Build | claude-haiku-4-5 | 낮음 | 매트릭스 기반 el_narration + BGM/SFX → 완성 Shot Record |

**비용 최적화 원칙**:
- Opus 4.6 → 창의적 판단 + 프롬프트 엔지니어링 핵심 3단계 (STEP 04, 05, 06)
- Haiku 4.5 → 매트릭스 기반 태깅·병합 (STEP 07, Section 단위 배치 6회)
- 영상 1편당 Opus 3회 + Haiku 6회 호출. STEP 07 병합으로 ~97% 비용 절감

---

## 4. Skill 의존성 트리

```
01_research
    └── 02_planning (planner)
            └── 04_script_final (script-director: draft → final)
                            └── 05_shot_composition (shot-composer) ←── 핵심 분기점
                                    └── 06_visual_direction (visual-director)
                                            └── 07_shot_records (shot-record-builder)
```

> **Shot Record 누적 구조**: 각 STEP은 이전 단계 YAML 필드를 보존하고 담당 필드만 추가.
> 05 → 06 → 07이 동일 Shot Record를 누적 완성하므로 교차 파일 참조 불필요.

---

## 5. MCP 도구 매핑

| MCP 도구 | 사용 단계 | 목적 |
|----------|-----------|------|
| `notebooklm.list_notebooks` | PHASE 0, 1 | 연결 확인 + 노트북 목록 조회 |
| `notebooklm.list_sources` | PHASE 2 | 소스 목록 조회 |
| `notebooklm.ask_question` | PHASE 4 | PRIMARY/SECONDARY 자료 추출 |

---

## 6. 외부 도구 산출물 연동

| 산출 파일 | 연동 도구 | 사용 방식 |
|-----------|-----------|-----------|
| `07_narration_elevenlabs_ALL` | ElevenLabs Eleven v3 | Shot 단위 Audio Tag 전체 통합 → 나레이션 생성 |
| `06_visual_direction` image_prompt | Google Flow UI | Shot 단위 프롬프트 복사 → 이미지 생성 (수동) |
| `scripts/generate_images.py` | Gemini API | image_prompt 자동 파싱 → 이미지 일괄 생성 (API) |
| `07_shot_records` bgm/sfx | CapCut | Shot별 BGM/SFX 큐 → 오디오 트랙 배치 |
| `07_shot_records` | CapCut | Shot Record → 편집 가이드 |

---

## 7. 버전 관리 및 수정 시 재실행 규칙

| 수정 파일 | 재실행 필요 Skill (순서 포함) |
|-----------|------------------------------|
| `01_research` 수정 | planner → script-director → shot-composer → visual-director → shot-record-builder  |
| `02_planning` 수정 | script-director → shot-composer → visual-director → shot-record-builder  |
| `04_script_final` 수정 | shot-composer → visual-director → shot-record-builder  |
| `05_shot_composition` 수정 | visual-director → shot-record-builder  |
| `06_visual_direction` 수정 | shot-record-builder  |
| `07_shot_records` 수정 | (재실행 불필요 — 최종 산출물) |

**버전 증가 규칙**: 수정 시 새 버전 파일 생성 (덮어쓰기 금지)
예: `04_script_final_AI기술전망_v1.md` → `04_script_final_AI기술전망_v2.md`

---

## 8. 크리에이티브 레이어 매핑

| 크리에이티브 요소 | 정의 위치 | 구현 위치 |
|------------------|-----------|-----------|
| 해빛 페르소나 | `script-director/SKILL.md` | STEP 04 |
| 4단계 인지 여정 | `script-director/SKILL.md` + `planner/SKILL.md` | STEP 02, 03, 04 |
| Shot 분해·연출 구성 | `shot-composer/SKILL.md` | STEP 05 |
| 두들 비주얼 아이덴티티 | `visual-director/SKILL.md` | STEP 06 |
| Flow 프롬프트 변환 | `visual-director/SKILL.md` | STEP 06 |
| ElevenLabs v3 Audio Tag | `shot-record-builder/SKILL.md` | STEP 07 |
| 사운드 에코시스템 | `shot-record-builder/SKILL.md` | STEP 07 |
| Shot/Scene 번호 체계 | `pipeline_reference.md` §10 | 전 단계 |
| 모델 버전 고정 | `pipeline_rules.md` §11 | 전 단계 |
