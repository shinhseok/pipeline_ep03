# Style Definition Files

채널 비주얼 스타일을 정의하는 YAML 파일.
모든 에이전트(visual-director, shot-composer)와 스킬(nb2-template-reference)이 이 파일을 단일 소스로 참조한다.

## 현재 스타일

| 파일 | 이름 | 설명 |
|------|------|------|
| `sempe-ink.yaml` | Sempé Fine Ink | 기본 스타일 — 떨림 잉크, 파스텔 워시, 넉넉한 여백 |

## 사용 방법

1. **ANCHOR.md 헤더**에 `STYLE: sempe-ink` 기재
2. 에이전트는 `assets/reference/style/{STYLE}.yaml`을 읽어 스타일 값 적용
3. 새 스타일 추가 시 이 폴더에 YAML 파일 생성 후 ANCHOR에서 선택

## YAML 구조

```yaml
name: "스타일 이름"
version: N

# A. 씬 이미지용 (STEP 06)
art_style: "..."           # image_prompt JSON art_style 필드
background_default: "..."   # 기본 배경
background_variants: {...}  # 환경 암시 확장
redraw_constraint: "..."    # REDRAW constraint
face_constraint: "..."      # 얼굴 constraint

# B. ANCHOR Phase 1용 (STEP 05)
anchor_anti_text: "..."     # 안티-텍스트
anchor_canvas: "..."        # 캔버스 배경
anchor_body_style: "..."    # 캐릭터 스타일
anchor_prop_style: "..."    # 소품 스타일
```

## 주의사항

- 스타일 변경 시 이 파일 1개만 수정하면 전체 파이프라인에 반영됨
- `art_style`, `redraw_constraint`는 NB2 이미지 품질에 직접 영향 — 신중히 수정
- 새 스타일 테스트 시 1~2개 Shot으로 먼저 검증 후 전체 적용 권장
