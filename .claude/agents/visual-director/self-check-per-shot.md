# Self-Check per Shot — Visual Director Reference (v3 순수 한국어 자연어)

Before saving each shot, verify all items:

## A. 구조 검증 (Structure)

- [ ] `ref_images` YAML 배열 존재 (참조 이미지 있을 때)
- [ ] `thinking_level` YAML 필드 존재 (`high` 기본)
- [ ] `has_human` 값이 3값 중 하나: `main` / `anonym` / `none`
- [ ] flow_prompt에 구조적 태그 **없음**: `[thinking:`, `[SCENE]`, `[MUST]`, `[SOURCE REFERENCES]`, `TASK:` 없어야 함
- [ ] flow_prompt가 순수 한국어 서술문임 (영어 태그/라벨 없음)
- [ ] 4단락 구조 준수: P1(과제) → P2(배경) → P3(구도/감정) → P4(채색)

## B. 서술 품질 (Narrative Quality)

- [ ] **P2 배경**: "순백의 빈 공간" 또는 배경 밀도 등급에 맞는 서술 포함
- [ ] **B-2 배경 밀도**: [공간]에 밀도 등급(L0~L5) 있으면 해당 등급 서술 사용. L2 이상은 "캐릭터 선보다 연하고 가늘게" 포함. L4~L5는 원근 선 굵기 차이 명시. 배경 요소에 채색 없음
- [ ] **B-3 L3+ 순백 보장**: L3 이상일 때 "구조물 외의 빈 공간은 반드시 순백으로 남겨줘" 가드 포함. "깔려/드리워져/퍼져/가득" 등 공간 채움 동사 미사용
- [ ] **P3 크기 3중**: 수치(N%) + 상대비교 + 은유 모두 존재 (has_human: main/anonym)
- [ ] **P3 감정**: emotion_tag에 맞는 한국어 표정·포즈 묘사 자연 통합 (has_human: main)
- [ ] **P3 위치**: 오프센터 배치 (TITLECARD는 우측 55% 예외)
- [ ] **P4 색 계획 + 선 질감**: 채색 대상과 색상 명시 + "떨리는 손그림 느낌" 스케치 강조 문구 포함
- [ ] has_human: none → P3에서 소품/환경 구도 묘사

## C. ref_images 완전성 검증

- [ ] ref_images 첫 항목이 style_reference.png인가 (모든 shot 필수)
- [ ] `main` + `costume_refs: []` → main_turnaround 포함
- [ ] `main` + `costume_refs: [변장명]` → characters/{RUN_ID}/{변장명}.jpeg 포함
- [ ] `main` + secondary_chars 직접 등장 → 캐릭터별 ref 각각 포함 + THIS {name} 구분
- [ ] `anonym` → character_reference.jpeg 포함 + `THIS character_reference` 패턴 사용
- [ ] `none` → 캐릭터 ref 없음 (style_ref + prop_refs만)
- [ ] prop_refs의 모든 항목이 ref_images에 경로로 포함되어 있는가
- [ ] character_prop → ref_images에 포함 (우선순위 1)
- [ ] ref_images 최대 5개 이하 (style_ref 포함)
- [ ] generate_images.py에 의존하는 자동 첨부 없음 — ref_images가 최종 목록

## D. 신체 표현 규칙

- [ ] `main`인데 신체 일부만 → ref_images에 캐릭터 ref + `THIS {name}의 손/실루엣` 패턴
- [ ] `anonym`인데 신체 일부만 → `assets/reference/style/character_reference.jpeg` + `THIS character_reference의 형태를 따른 손/실루엣` 패턴
- [ ] 제네릭 "콩 캐릭터" 표현 사용 금지 → 반드시 THIS {name} 참조

## E. 추가 조건 분기 검증

- [ ] TITLECARD → 좌 45% 여백 + "왼쪽 45%는~" 포함
- [ ] secondary_chars 직접 등장 → 다중 캐릭터 패턴 (각각 THIS {name})
- [ ] 환경 구조물 (L3+) → "얇고 연한 잉크 윤곽선으로만~" 포함
- [ ] 실루엣 Shot → 얼굴 규칙 제거 (모순 방지)

## F. NB2 품질 (Quality)

- [ ] 품질 접미사 없음 (4k, masterpiece, HD)
- [ ] hex 코드 없음 (#FFFFFF 등)
- [ ] **THIS {name} 일치**: flow_prompt의 THIS {name}이 ref_images 파일명 stem과 일치
- [ ] 부정문 과다 없음 (동일 금지 표현 4회 이상 반복 금지)
- [ ] "frame", "border", "panel" 표현 없음
- [ ] 대문자 구역 레이블 없음 ("LEFT ZONE —" 등 → NB2가 텍스트로 렌더링)
- [ ] 과잉 스타일링 금지어 없음 (charcoal fill, solid fill, dense shadow 등)

## G. 구도 아키타입 검증

- [ ] [카메라]에 아키타입 명시된 경우 P3에 해당 패턴 적용
- [ ] 캐릭터 점유율이 아키타입 범위 내 (VAST:8-10%, INTIMATE:15-20% 등)
- [ ] MCU (20-30%) 사용 시: REVEAL/TENSION 절정이고 연속 3Shot 내 1회만

## H. 7차원 톤 일관성 검증 (emotion_nuance 있을 때)

- [ ] **P3 감정 3파트**: face + upper_body + gesture가 뉘앙스의 `v3_emotion_direction` 값과 일치
- [ ] **P2 배경 밀도**: 뉘앙스의 `bg_density` 등급에 맞는 서술 사용
- [ ] **P4 소품 관계**: 뉘앙스의 `prop_relation` (크기 대조·공간 관계)과 일치
- [ ] **P3 카메라**: 뉘앙스의 `camera` (앵글·거리)와 일치
- [ ] **P5 색**: 뉘앙스의 `color_point` (채색 대상·색상)과 일치
- [ ] **톤 수렴**: 5차원이 동일한 감정 톤으로 수렴 (압박인데 밝은 색, 환희인데 어두운 배경 → 불일치)

## I. 신체 변형 한계 검증

- [ ] 감정 과장형 표현만 사용 (허용: 움츠림, 어깨 과장, 스프링, 팔 ±20%, 압축/신장)
- [ ] 체형 해체 금지 (금지: 목 늘리기, 팔 3배, Bean→인간 비율, 해부학적 불가능 꺾임)
- [ ] Bean 정체성 유지: 머리-몸통 일체형, 짧은 팔다리, 콩 형태 기본 유지
