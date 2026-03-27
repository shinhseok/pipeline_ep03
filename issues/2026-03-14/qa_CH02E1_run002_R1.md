# QA Report — CH02E1 run002 Round 1
DATE: 2026-03-14

## 검수 결과
- 총 이미지: 93개
- 전량 통과: 68개 (73%)
- 실패: 25개 (27%)

## 카테고리별 실패 분포

| 카테고리 | 실패 수 | 비율 | 대표 증상 | 수정 수준 |
|---------|--------|------|---------|---------|
| A INTENT | 12 | 13% | 텍스트 렌더링(4), 흐린 이미지(4), 연출 실패(4) | 시스템 |
| B STYLE | 9 | 10% | 드로잉 선 불일치(4), 채색 스타일 이탈(5) | 시스템 |
| C BG | 5 | 5% | 배경색 오염 | 시스템 |
| G FACE | 3 | 3% | TENSION인데 웃는 표정 | 시스템 |
| I ARTIFACT | 3 | 3% | 프레임 생성, 텍스트 삽입 | 개별+시스템 |
| H REF | 2 | 2% | 레퍼런스 미참조 | 개별 |
| E COMPOSITION | 1 | 1% | 여백 부족 | 개별 |

## 근원 패턴 분석 (5그룹)

### P1. 텍스트 렌더링 (shot33, 42, 79, 90)
- 원인: creative_intent에 NB2가 표현 불가능한 의미적 변환 (실→전구, 점선 아크)
- 수정: shot-composer NB2 시각화 원칙 N2 — 공간 배치 기법 7종 도입

### P2. 흐린 이미지 (shot25, 35, 64, 80)
- 원인: "extremely faint", "afterimage" 등 저대비 지시
- 수정: shot-composer NB2 시각화 원칙 N1 — 최소 시각적 무게 10%+, 금지어 목록

### P3. 선 스타일 불일치 (shot51, 74, 76, 93)
- 원인: 레퍼런스 이미지 스타일이 art_style 압도 + 제스처 정밀도 충돌
- 수정: REDRAW constraint에 선 일관성 명시 + generate_images.py 라벨 강화

### P4. 감정 표현 불일치 (shot23, 24, 34)
- 원인: action 필드 감정 접미어를 NB2가 무시
- 수정: constraints에 감정 표현 강제 문구 이중 삽입

### P5. 배경·스타일 이탈 (shot00, 05, 06, 40, 41, 62, 88, 91)
- 원인: 레퍼런스 이미지 배경/채색 전이
- 수정: constraints에 배경 강제 + 다중 레퍼런스 경고 (generate_images.py)

## 추가 개선 — 구도 아키타입 시스템 (사용자 요청)
- 6종 아키타입: VAST, OPPRESSIVE, INTIMATE, ISOLATED, JUXTAPOSE, PANORAMIC
- shot-composer disney-principles.md + visual-director field-rules.md에 반영
- Sempé "빨개지는 아이" 구도를 체계적으로 적용

## 시스템 수정 이력

| 파일 | 변경 내용 |
|------|---------|
| `shot-composer/execution-flow.md` | SR-10~13 자가검증 추가, ④.5 구도 아키타입 선택 단계 |
| `shot-composer/disney-principles.md` | NB2 시각화 원칙 N1~N3, 공간 배치 기법 7종, 구도 아키타입 6종, Shot 설계 흐름 확장 |
| `visual-director/field-rules.md` | 감정 constraint 이중 삽입, 배경 강제 constraint, 아키타입→composition 변환 테이블 |
| `visual-director.md` | REDRAW 고정값 선 일관성 강화, Self-Check 4항목 추가 |
| `generate_images.py` | 레퍼런스 라벨에 선 일관성 명시, 다중 레퍼런스(3+) 스타일 경고 삽입 |
| `CLAUDE.md` | NB2 시각화 원칙, 구도 아키타입, 감정 constraint 요약 추가 |

## STATUS: SYSTEM_FIX_APPLIED — 개별 Shot 재생성은 다음 run에서 적용
