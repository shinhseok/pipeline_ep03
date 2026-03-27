# N — Gemini API 최종 전달 content

## 목적
복수 ref_image(캐릭터 1 + 소품 2)에 THIS 네이밍을 적용했을 때
각 대상이 정확히 구분되어 제어되는지 검증. shot30 기반.

## API에 전달된 content 배열 (순서대로)

```
THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:
```
`<style3_ref.png>`
```
THIS main — 이 대상의 외형만 따라 그려줘:
```
`<main.jpeg>`
```
THIS gear — 이 대상의 외형만 따라 그려줘:
```
`<gear.jpeg>`
```
THIS factory_chimney — 이 대상의 외형만 따라 그려줘:
```
`<factory_chimney.jpeg>`
```
THIS style의 드로잉 스타일로, 유튜브 교육 영상에 사용할
서사적인 삽화 한 장을 그려줘.

배경은 순백의 빈 공간이되, 바닥선이 희미하게 암시되어 있어.

화면 중앙에 THIS main이 전체 화면의 약 15%로 서 있어.
고개를 살짝 갸우뚱 기울인 채 반쪽 미소를 머금고 양손을 벌려
양쪽을 가리키고 있어 — '이쪽에서 보면 혁명이지만...'이라는
아이러니의 순간이야.

좌측에 THIS gear와 THIS factory_chimney 아이콘 그룹이 프레임의
15%로 배치 — 역사의 눈(생산성 상징).
우측에 작은 콩 캐릭터 실루엣 5~6명(각 5%)이 — 둥근 머리와 짧은
팔다리, 얼굴 없는 실루엣이야 — 사람의 눈(희생).

반드시 THIS main의 넥커치프에만 sage-green 워시를 입혀줘 — 유일한 색이야.
하나의 장면만 그려줘. 정확히 캐릭터 1명, 실루엣 5~6명, 소품 2개만 그려줘.
```

## 설정
- model: gemini-3.1-flash-image-preview
- thinking_level: HIGH

## 평가 기준
1. THIS main — 넥커치프 캐릭터가 중앙에 정확히 배치되는가
2. THIS gear — 기어가 좌측에 배치되는가 (우측에 가지 않는가)
3. THIS factory_chimney — 굴뚝이 기어와 함께 좌측에 배치되는가
4. 실루엣 군중 — 우측에 배치되는가
5. 채색 — 넥커치프에만 sage-green
6. 스타일 — style3_ref 스타일이 반영되는가 (ref_image 있으므로 실험 2에서 효과 없었음)

## N1 결과 (style3_ref — 캐릭터 포함 씬)
- 배치/포즈/채색 모두 정확
- **문제: main 캐릭터에 모자가 추가됨** — style3_ref에 모자 쓴 캐릭터가 있어서 외형 오염 발생

## N2 결과 (style4_no_character — 캐릭터 없는 이미지)
- 배치/포즈/채색 모두 정확
- **모자 사라짐** — main.jpeg의 원본 외형(넥커치프만) 정확히 재현
- 모든 THIS 네이밍 참조가 정확히 작동

## 실험 4 핵심 발견

**THIS 네이밍 복수 ref 제어:**
- 캐릭터 1 + 소품 2 + 실루엣 군중이 모두 정확히 제어됨 ✅
- 서수 참조("첫 번째/두 번째 이미지의")보다 명확하고 직관적

**style_ref 이미지 선정 규칙:**
- style_ref에 캐릭터가 포함되면 **캐릭터 외형이 오염**됨 (N1에서 확인)
- style_ref는 반드시 **캐릭터가 없는 순수 배경/소품/패턴 이미지**를 사용해야 함
- 소품 단독 shot(기어, 물레 등)이 style_ref로 적합

### 파이프라인 반영
- **generate_images.py**: ref_images: [] shot에 자동 첨부하는 style_ref는 캐릭터 없는 이미지로 선정
- **ANCHOR.md**: `## Style Anchor Image` 섹션에 "캐릭터 미포함" 제약 조건 명시
- **visual-director**: THIS 네이밍 도입 시 서수 참조 대신 이름 참조로 전환 가능
