# Shot Composer 수행 지침 (§10) — PHASE A + PHASE B

> shot-composer.md의 §10 상세 실행 흐름.
> PHASE A/B 실행 전 반드시 이 파일을 읽는다.

---

## 2단계 실행 구조

- **PHASE A (05A)**: 나레이션 배분 — 대본 → Shot 경계 확정 → narration_map 사용자 승인
- **PHASE B (05B)**: 창의적 연출 — narration_map → Shot 파일 생성

**핵심 원칙**: narration_span은 PHASE A에서 확정된다. PHASE B는 narration_span을 절대 변경·분리·병합하지 않는다.

---

## PHASE A — 나레이션 배분 (STEP 0~3)

### STEP 0. 사전 준비

(PRE) RUN_ID 확인
→ version_manifest.yaml에서 current_run 읽기 (없으면 v1)

(A) IMAGE_MODEL 확인
→ NB2 고정 (ANCHOR 헤더에 IMAGE_MODEL: NB2 기록)

(B) ANCHOR 사전 초안
→ ⚠️ anchor-generation.md 읽기 (상세 규칙 참조)
→ 역사적 고증 트리거 확인 → 웹 검색 리서치 수행
→ 텍스트 ANCHOR 묘사구 초안 작성
→ 리서치 결과를 anchor_research.md로 저장

(C) 핵심 메타포 계획
→ Section별 핵심 메타포 1개씩 확정

(D) 감정 태그 설계
→ 나레이션 텍스트를 Section별로 분석하여 emotion_tag 흐름 결정
→ 감정 태그 5종(HUMOR, REFLECTIVE, AWE, REVEAL, TENSION) — §7 설계 규칙 참조
→ 나레이션 내용 기반 판단: 코믹 상황→HUMOR, 성찰·여백→REFLECTIVE, 경외감→AWE, 반전→REVEAL, 긴장→TENSION
→ HUMOR RATIO 사전 계산 (HOOK≥30%, SEC01≥20%, SEC02≥20%, SEC03≥35%, OUTRO≥10%)
→ 미달 시 breath Shot의 emotion_tag 조정 또는 사용자에게 보고

(E) 내러티브 구조 + 감정 아크 확인
→ 02_planning의 `## 내러티브 구조 + 감정 아크` 섹션 읽기
→ 5단계(훅-셋업-텐션-페이오프-아웃트로) + 타임라인을 Section별 Shot 배치 전략에 반영
→ 셋업→텐션 구간(SECTION01~02)에 tension/reveal Shot 집중 배치
→ 페이오프 구간(SECTION03)에 reveal → breath 전환 설계
→ Hook ≤30초, Outro 20~30초 타이밍 준수 확인

(F) 핵심 메시지 + 비주얼 모티프 확인
→ 02_planning의 `## 핵심 메시지 설계` + `## 비주얼 스토리텔링 전략` + `## Hook 제작 옵션` 읽기
→ 비주얼 모티프를 creative_intent의 관통 요소로 활용:
  - 훅: 모티프 초기 상태로 등장
  - 셋업~텐션: 모티프가 변형·확장
  - 페이오프: 모티프가 해소된 형태
  - 아웃트로: 모티프가 새로운 의미로 순환 (Hook Shot과 시각적 대응)
→ 키 비주얼 Shot 확인 → 해당 Shot의 creative_intent를 가장 정교하게 설계
→ 메시지 앵커링 맵의 각 단계 전달 포인트가 Shot의 감정 태그/씬 유형과 호응하는지 확인

(G) Hook 제작 옵션 확인
→ 02_planning의 `## Hook 제작 옵션`에서 HOOK_TYPE + HOOK_MEDIA 읽기
→ HOOK_TYPE: song → SECTION00_HOOK Shot에 `hook_type: song` 필드 추가
→ HOOK_MEDIA: video → SECTION00_HOOK Shot에 아래 필드 추가:
  - `hook_media_type: video`
  - `video_duration: {N}s` (클립 길이)
  - `video_engine: veo3` (기본값) 또는 `kling`
→ HOOK_MEDIA: image (기본) → 추가 필드 없음 (기존 동작)
→ Video Hook 연출 모드 선택:
  - **Kinetic Transition (권장)**: 캐릭터 앵커 + 드론 카메라 방식의 원테이크 체이닝.
    **3대 원칙:**
    1. 캐릭터 = 앵커 — 처음부터 끝까지 프레임 안에 존재. 절대 밖으로 나가지 않음.
    2. 카메라 = 드론 — 캐릭터를 따라가고, 회전하고, 가감속. 캐릭터를 놓치지 않음.
    3. 배경 = 흘러가는 것 — 프레임 밖으로 사라지거나 자연스럽게 전환.
    - 캐릭터도 적극적으로 움직임 (걷기, 달리기, 팔 벌리기, 멈춤 등)
    - 캐릭터 에너지 아크를 가사/음악 에너지와 동기화
    - 각 Shot = 1개 Key Frame 이미지 (캐릭터가 프레임 안에 명확히 존재)
    - KF 간 캐릭터 포즈가 연속적 — 급격한 자세 변화 금지
    - image_prompt = 단일 (해당 KF 이미지 생성용)
    - creative_intent에 `[Kinetic Transition]` 태그 명시:
      ```
      [Kinetic Transition] KF{N} → KF{N+1}.
        캐릭터 동작: {어떻게 움직이는가}
        카메라 동작: {어떻게 따라가는가}
        배경 변화: {무엇이 들어오고 나가는가}
      ```
    - 마지막 KF = landing frame (`hook_media_type: image`, 전환 없음)
    - 의상 전환 가능: 모션 블러/증기가 캐릭터를 가리는 순간 costume 변경
    - 군중 실루엣: character_reference.jpeg 참조 (main_turnaround 사용 금지)
    - ⚠️ **이동 방향 일관성**: 피사체의 기본 이동 방향은 전체 KF에 걸쳐 일관. 방향 전환 시 카메라 회전으로 처리.
  - **Per-Shot (레거시)**: Shot별 start/end 이미지 분리 생성. 제자리 변환.
    - image_prompt[start] + image_prompt[end] 분리 작성
    - creative_intent의 `[카메라]` 태그에 `[Video: 1장]` 또는 `[Video: 2장]` 명시


### STEP 1. 나레이션 단위 분류

대본 전체를 순서대로 읽으며 각 나레이션 문장·절에 유형을 부여한다.

| 유형 | 조건 | Shot당 나레이션 | duration_est |
|------|------|----------------|-------------|
| `info` | 사실·정보 전달 문장 | 1~2문장 (의미 단락 내) | 3~4초 |
| `emotional` | 감정 코멘터리·비꼬기·공감 | 1문장 이하 | 3~4초 |
| `reveal` | 반전·핵심 통찰 ([REVEAL] 태그) | 1절 이하 | 2~3초 |
| `tension` | 긴장·위기 ([TENSION] 태그) | 1절 이하 | 3~4초 |
| `breath` | 감정 정점 직후 여운, 또는 전환 | 매우 짧거나 무나레이션 | 2~3초 |
| `sub` | `[보조]` 태그가 붙은 보조 나레이터 대사 | 1문장 | 3~4초 |

> **[보조] 대사 처리 규칙**:
> - `[보조]` 대사는 **단독 Shot** 또는 직전/직후 해빛 대사와 **대화 Shot**으로 묶을 수 있음
> - 대화 Shot: 해빛 + happy_rabbit 함께 등장 (두 나레이션을 1 Shot에 배치)
> - 단독 Shot: happy_rabbit만 등장 (해빛 없이)
> - shot-composer가 서사 흐름에 따라 판단 (강제 규칙 아님)
> - scene_type: 주로 `Doodle-Character` 권장 (캐릭터 등장 Shot)

> ⚠️ **문장 내 분할 허용**: 하나의 긴 문장이 여러 비주얼 장면을 포함하는 경우, 절(clause) 단위로 분할하여 각각 별도 Shot으로 배정할 수 있다. 방송에서는 한 문장 안에서도 컷이 바뀌는 것이 자연스럽다. 단, 같은 나레이션을 두 Shot이 중복 사용하는 것은 금지.

Section별 기준 템포:

| Section | 내러티브 단계 | 타임라인 | 기준 템포 | 이유 |
|---------|-------------|---------|---------|------|
| SECTION00_HOOK | 훅 | 00:00~00:30 | 2~3초 | 핵심 8초 임팩트, 30초 내 완결 |
| SECTION01 | 셋업 | 00:30~02:00 | 3~4초 | 배경·갈등 제시 |
| SECTION02 | 텐션 | 02:00~04:30 | 3~4초 | 갈등 최고조 + 메타포 전환 (가장 긴 섹션) |
| SECTION03 | 페이오프 | 04:30~06:00 | 3~4초 | 해소·실천 해법 |
| SECTION04_OUTRO | 아웃트로 | 06:00~06:30 | 3~5초 | Hook 순환 + 오픈 루프 (20~30초) |

분류 규칙:
- `reveal` / `tension` 유형 나레이션은 반드시 단독 Shot — 앞·뒤 문장과 합치기 금지
- `breath` Shot은 감정 정점(REVEAL/TENSION) 직후 1개 삽입 권장
- `info` 유형이라도 2개의 의미 단락을 넘으면 분리
- 한 Shot에 배정된 나레이션 총 글자 수가 80자 초과 시 분리 검토


### STEP 2. narration_map 작성 및 사용자 승인

→ Section별로 아래 표 형식으로 출력한다:

```
📋 NARRATION MAP — {SECTION명}
기준 템포: {N}초/Shot | 예상 Shot 수: {N}개

| local_id | 유형 | duration_est | emotion_tag | scene_type | 화자 | visual_direction | narration_span |
|----------|------|-------------|------------|-----------|------|-----------------|----------------|
| 01 | info | 4초 | AWE | Doodle-Illust | 해빛 | 거대한 시간의 흐름 속 작은 사람 | "인류는 수천 년 동안 거의 같은 수준으로 살았거든요." |
| 02 | sub | 4초 | HUMOR | Doodle-Character | 보조 | happy_rabbit이 고개를 갸웃 | "[보조] 잠깐, 25배? 그게 마을이야 바이러스야?" |
...

Section 합계: {N}개 Shot / {N}초
누적 Shot_id: {시작}~{끝}
```

→ 모든 Section 출력 완료 후 전체 요약:

```
📊 NARRATION MAP 전체 요약
총 Shot 수: {N}개 (shot_id 1부터)
총 예상 시간: {N}초
평균 클립 길이: {N}초
clip_rhythm 분포: quick:{N} / standard:{N} / breath:{N}
Section별: HOOK:{N} / SEC01:{N} / SEC02:{N} / SEC03:{N} / OUTRO:{N}

비주얼 ANCHOR 기획 (Phase 1 대상):
| 대상 | Type | 파일명 | 적용 Section |
|------|------|--------|-------------|

IMAGE_MODEL: NB2
```

→ 사용자 승인 후 PHASE B 진행
  ⚠️ 승인 이후 narration_span 수정 불가. 수정 필요 시 이 단계로 돌아온다.

> **visual_direction 작성 규칙**:
> - 순수 비주얼 장면 묘사만 (텍스트를 장면의 주요소로 사용 금지)
> - Sempé 원칙 반영: 오프센터 배치, 스케일 대비, 빈 공간, 환경 암시
> - 캐릭터 동작/표정 + 핵심 소품 + 공간감을 한 줄에 압축
> - PHASE B creative_intent의 기초 방향 — PHASE B에서 6-tag로 확장


### STEP 3. ANCHOR 파일 확정 및 저장

→ ⚠️ anchor-generation.md 재확인 (Layer 4 JSON 작성 규칙)
→ 승인된 묘사구로 ANCHOR 파일 생성 (IMAGE_MODEL 기록)
→ Layer 2 비주얼 ANCHOR 테이블 작성 (⏳ 상태로 초기화)
→ SAVE: 04_shot_composition/{RUN_ID}/ANCHOR.md

---

## PHASE B — 창의적 연출 (STEP 4~6)

### 병렬 실행 구조

PHASE A 완료 + 사용자 승인 후, 오케스트레이터가 Section별로 shot-composer를 동시에 5개 호출한다.

각 PHASE B 에이전트 입력 (프롬프트에 반드시 포함):
- SECTION: {담당 섹션명}
- SHOT_ID_RANGE: {시작}~{끝} ← narration_map 기준
- narration_map 해당 섹션 행 전체 (복사하여 프롬프트에 첨부)
- RUN_ID, ANCHOR_REF 경로

각 에이전트는 자신의 섹션만 처리한다:
- SECTION00_HOOK: 에이전트 1
- SECTION01: 에이전트 2
- SECTION02: 에이전트 3
- SECTION03: 에이전트 4
- SECTION04_OUTRO: 에이전트 5

> **TITLECARD 없음**: Title Card / 썸네일은 STEP 10(수동 편집). shot_id는 1부터.

⚠️ 각 에이전트는 자신의 SHOT_ID_RANGE 이외의 shot_id를 절대 사용하지 않는다.
⚠️ shot_id는 narration_map에서 이미 확정된 값 — 에이전트가 임의로 변경 금지.

### PHASE B 시작 전 확인 (각 에이전트)

☐ 입력 프롬프트에서 담당 SECTION과 SHOT_ID_RANGE를 확인했는가
☐ narration_map(해당 섹션 행)을 입력받았는가
☐ ANCHOR.md 경로를 알고 있는가
☐ narration_span을 변경하지 않겠다는 원칙을 숙지했는가


### STEP 4. Section별 Shot Record 생성

narration_map의 각 행(local_id 순)을 Shot으로 변환한다.

각 Shot에 대해:
→ ① narration_map에서 해당 local_id의 narration_span, 유형, duration_est, scene_type, emotion_tag 확인
  ⚠️ narration_span, scene_type, emotion_tag는 절대 수정 금지 — narration_map 값을 그대로 복사
→ ②  Section 내 메타포 계획 확인
→ ③ scene_type은 narration_map에서 이미 확정됨 — 재결정 금지
→ ④ 감정 태그 확인 → §7 설계 규칙 적용
→ ④.5 **구도 아키타입 선택** → disney-principles.md §구도 아키타입 참조
→ ⑤ Line of Action 결정
→ ⑥ creative_intent 작성 (Disney/Pixar 원칙 + NB2 시각화 원칙 — disney-principles.md 참조)
  - `breath` 유형: creative_intent에 "이전 Shot 감정 여운 지속" 명시
→ ⑦ 실루엣 테스트 통과 확인
→ ⑧ prop_refs / costume_refs 기재
    - 기본 해빛 등장 (변장 없음): costume_refs: []
    - 변장 등장: costume_refs: [해당 costume명] (예: [stephenson])
    - 그림자·실루엣 전용: costume_refs: []
    ⚠️ costume_refs: [] = 기본 해빛 (정상). 변장이 있을 때만 변장명 기재.
       has_human 값이 ref_images 캐릭터 소스를 결정하는 유일한 키.
→ ⑧.5 보조 캐릭터 (secondary_chars) 설정:
    - narration_span에 `[보조]` 태그가 있으면 → `secondary_chars: [happy_rabbit]`
    - creative_intent에 happy_rabbit 배치 포함:
      `[캐릭터수] 메인 1명 + 보조(happy_rabbit) 1명` (해빛과 함께 등장 시)
      `[캐릭터수] 보조(happy_rabbit) 1명` (단독 등장 시)
    - happy_rabbit도 특정 캐릭터이므로 has_human: main
    - ⚠️ `[보조]` narration_span이 있는데 `secondary_chars`에 happy_rabbit이 없으면 위반
→ ⑨ has_human 초기 추정 (3값):
    - 해빛/변장 캐릭터 전신 등장 → `main`
    - 명명된 학자/역사인물이 직접 등장 → `main`
    - 특정 캐릭터의 손/팔/실루엣 등장 → `main`
    - **인체 형태가 인식 가능한 모든 익명 존재** → `anonym`
      (예: 익명 실루엣, 군중, 아이 실루엣, 익명의 손/팔, 신체 일부)
      ⚠️ creative_intent에 "실루엣", "아이", "손", "군중", "사람" 등
         신체 형태 키워드가 있으면 반드시 `anonym` — `none`으로 분류 금지
    - 소품/오브젝트만, 사람 형태 완전 부재 → `none`
→ ⑨.5 명명된 학자/역사인물 ANCHOR 등록 검증:
    - creative_intent에 학자/인물이 등장하는데 ANCHOR에 costume_ref가 없으면 → **BLOCKED**
    - ANCHOR Layer 1+2+3에 해당 인물 등록 후 진행
→ ⑩ YAML 블록 작성
→ ⑩.5 Self-Reflection (저장 전 필수)

    === 그룹 A: 필수 정합성 (위반 시 저장 불가) ===
    ☐ A-1: has_human ↔ creative_intent 일치
           - 특정 캐릭터 등장 → main
           - 신체 키워드(실루엣/군중/손/사람) → anonym (none 금지)
           - 소품/환경만 → none
    ☐ A-2: narration_span, scene_type, emotion_tag가 narration_map과 동일한가 (변경 금지)
    ☐ A-3: NB2 금지어 없음 (faint, ghost, afterimage, 4k, masterpiece, HD)
    ☐ A-4: [보조] narration_span → secondary_chars: [happy_rabbit] 설정 확인

    === 그룹 B: 연출 품질 (위반 시 경고, 진행 가능) ===
    ☐ B-1: 이전 Shot과 시각 연속성 명시 ([이전샷] 태그)
    ☐ B-2: 동일 카메라/구도/emotion_nuance/pose_archetype 연속 한도 미초과
    ☐ B-3: [감정선]에 구체적 표정 묘사 포함
    ☐ B-4: 변환/인과 관계 → 공간 배치 기법 사용

    === 그룹 C: 전체 밸런스 (섹션 완료 후 1회) ===
    ☐ C-1: 02_planning 내러티브 구조와 emotion_tag 분포 호응
    ☐ C-2: 비주얼 모티프 변형·순환
    ☐ C-3: 키 비주얼 Shot 정교성
    ☐ C-4: 복수 캐릭터/포즈 수량 명시

→ ⑪ 카메라 거리·구도·line_of_action 변화 확인 (그룹 B-2에서도 커버)

각 Shot 파일 즉시 저장: 04_shot_composition/{RUN_ID}/{SECTION}/shot{shot_id:02d}.md

⚠️ 배치 분할 규칙: 1개 응답당 최대 7 Shot. Write 도구로만 저장 — 텍스트 출력 금지.
배치 완료 후 자동 진행. 배치 요약만 출력: "Batch N: Shot X~Y 저장 완료 (N개)"


### STEP 5. 최종 검증

→ (A) 유머 공백 점검: "코믹 없는 연속 구간" 최대값 ≥3 이면 수정
→ (B) Visual Rhythm Check 출력 (§8 규칙 6 형식)
→ (C) 밀도 확인 (narration_map 승인 시점에 이미 보장되어 있으므로 검증만)

```
DENSITY CHECK
  Total shots:       {N}개
  Total duration:    {N}초
  Average duration:  {N}초  (≤5초 기준)
  Status:            PASS ✅ / FAIL ❌
```

→ 검증 통과 후 사용자 검토 요청
