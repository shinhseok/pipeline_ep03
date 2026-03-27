---
name: qa-images
description: "Image QA workflow: QA Sheet 생성 → 사용자 기입 → 패턴 분석 → 수정 → 보고. Run /qa-images."
disable-model-invocation: true
---

# Workflow: qa-images
## 트리거: /qa-images
## 목적: 생성된 이미지를 구조화된 체크시트로 검수하고, 반복 이슈를 시스템 레벨에서 개선

---

## 워크플로우 개요

```
PHASE 1  Sheet Gen     QA_SHEET.md 자동 생성 → 사용자에게 기입 안내
PHASE 2  User Review   사용자가 이미지 확인 후 QA_SHEET.md 직접 기입
PHASE 3  Analysis      기입 완료된 시트 읽기 → 패턴 분석 → 해결 방안 보고
PHASE 4  Fix           승인된 수정 적용 + 이미지 재생성
PHASE 5  Archive       QA 결과를 issues/ 에 영구 저장 + 최종 보고
```

---

## PHASE 1 — QA Sheet 생성

스크립트를 실행하여 QA 체크시트를 자동 생성한다.

```bash
QA=".claude/skills/qa-images/scripts"
python $QA/generate_qa_sheet.py --project {PROJECT_CODE}
python $QA/generate_qa_sheet.py --project {PROJECT_CODE} --section SECTION01  # 특정 섹션만
python $QA/generate_qa_sheet.py --project {PROJECT_CODE} --round 2           # 재검수
```

생성 위치: `projects/{PROJECT_CODE}/09_assets/images/{RUN_ID}/QA_SHEET.md`

### 사용자 안내 출력

```
📋 QA Sheet 생성 완료

파일: 09_assets/images/{RUN_ID}/QA_SHEET.md
Shot 수: {N}개 | 체크 항목: 9개

각 Shot 이미지를 확인하고 판정을 기입해 주세요:
  O = 통과 | X = 실패 | - = 해당 없음

실패(X) 항목은 비고 란에 증상을 간단히 적어주세요.
예: "코 있음", "여백 부족", "물레 형태 다름"

기입 완료되면 "기입 완료" 라고 알려주세요.
```

---

## QA 체크 항목 정의 (9개)

| ID | 항목 | 카테고리 | 확인 내용 | 실패 시 수정 대상 |
|---|------|---------|---------|----------------|
| A | 연출 의도 | `INTENT` | creative_intent에 기술된 장면이 표현되었는가 | 05 creative_intent / 06 flow_prompt |
| B | 스타일 일관성 | `STYLE` | Sempé 잉크 스타일 유지, 포토리얼/3D 이탈 없음 | visual-director art_style |
| C | 배경색 | `BG` | 순백 배경, 색 번짐 없음 | visual-director background 고정값 |
| D | 캐릭터 일관성 | `CHARACTER` | 체형·의상·색상이 ANCHOR/레퍼런스와 일치 | ANCHOR Layer 2+4 / costume refs |
| E | 구도/여백 | `COMPOSITION` | 지정된 구도·여백 비율 준수, 가장자리 침범 없음 | 06 composition + constraints |
| F | 소품 정확도 | `PROP` | 소품 형태가 ANCHOR/레퍼런스와 일치 | ANCHOR Layer 2 / prop refs |
| G | 얼굴 규칙 | `FACE` | 코 없음, 점 눈, 표현적 입 | ANCHOR face_constraint |
| H | 레퍼런스 반영 | `REF` | 레퍼런스 이미지가 결과에 반영됨 | generate_images.py ref 로직 |
| I | 생성 오류 | `ARTIFACT` | 텍스트 삽입, 패널 분할, 왜곡 등 | NB2 constraints 강화 |

### 카테고리 → 수정 대상 매핑 (근원적 해결 원칙)

```
개별 shot 이슈 (1~2개):
  → 해당 05_visual_direction shot 파일 수정 → 이미지 재생성

반복 이슈 (3개 이상 동일 카테고리):
  INTENT    → shot-composer creative_intent 가이드 강화
  STYLE     → visual-director art_style 고정값 수정
  BG        → visual-director background 고정값 수정
  CHARACTER → ANCHOR Layer 4 appearance 정의 수정
  COMPOSITION → visual-director composition 규칙 추가
  PROP      → ANCHOR Layer 1 텍스트 묘사구 수정
  FACE      → ANCHOR face_constraint + visual-director constraints
  REF       → generate_images.py 레퍼런스 로직 수정
  ARTIFACT  → visual-director constraints 템플릿 강화
```

---

## PHASE 2 — User Review (사용자 기입)

사용자가 QA_SHEET.md를 열어 각 Shot 이미지를 확인하고 판정(O/X/-)을 기입한다.
Claude는 이 단계에서 대기하며 "기입 완료" 신호를 기다린다.

---

## PHASE 3 — Analysis (패턴 분석)

사용자가 "기입 완료"를 알리면:

1. QA_SHEET.md를 읽어 X(실패) 항목을 집계한다
2. 카테고리별 실패 빈도를 계산한다
3. 아래 형식으로 분석 보고한다

### 보고 형식

실패 요약 테이블 (카테고리 | 실패 수 | 비율 | 대표 증상) + 개별 이슈 목록 (Shot | 실패 항목 | 비고) + 시스템 레벨 수정 제안 (3개+ 반복 시) + 개별 Shot 수정 제안 형태로 출력한다.

사용자 승인 후 PHASE 4로 진행.

---

## PHASE 4 — Fix (수정 적용)

사용자 승인 후:
1. 시스템 레벨 수정 먼저 적용 (에이전트/스킬 파일)
2. 개별 Shot 파일 수정 (05_visual_direction)
3. 수정된 Shot 이미지 재생성:
   ```bash
   python $GI/generate_images.py --project {PROJECT_CODE} --shots {실패 shot 번호} --overwrite
   ```
4. 재병합:
   ```bash
   python $RD/merge_records.py --project {PROJECT_CODE} --render
   ```

---

## PHASE 5 — Archive + Report

QA 결과를 `issues/{YYYY-MM-DD}/qa_{PROJECT_CODE}_{RUN_ID}_R{N}.md`에 영구 저장한다.

포함 내용: 검수 결과 통계 + 카테고리별 실패 분포 + 시스템/개별 수정 이력 + 재생성 결과.

### 최종 보고
```
✅ QA 완료 — {PROJECT_CODE} {RUN_ID} Round {N}
검수: {N}개 | 통과: {N}개 | 수정: {N}개 | 미해결: {N}개
{미해결 → Round {N+1} 권장 | 전량 통과 → 편집 진행 가능}
```

---

## 재검수 (Round 2+)

수정 후 재검수가 필요하면:
```bash
python $QA/generate_qa_sheet.py --project {PROJECT_CODE} --round 2
```
→ `QA_SHEET_R2.md` 생성. 이전 라운드에서 실패한 shot만 자동 표시 (향후 구현).
