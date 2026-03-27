# P-scene — shot09 대조군 vs 실험군

## 목적
소품 ref를 단일 뷰 vs 턴어라운드 시트로 교체했을 때 차이 비교.
캐릭터 ref는 둘 다 턴어라운드 시트(O_sheet_v2)로 통일 — 소품 ref만 변수.

## 대조군 (control) — 소품 단일 뷰

```
THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:
```
`<assets/reference/anchor/style_ref.png>`
```
THIS main — 이 캐릭터의 턴어라운드 시트야. 외형만 따라 그려줘:
```
`<O_multiview_ref/O_sheet_v2.png>` (캐릭터 4뷰 시트)
```
THIS spinning_wheel — 이 소품의 형태만 따라 그려줘:
```
`<props/run002/spinning_wheel.jpeg>` (단일 뷰)

## 실험군 (experiment) — 소품 턴어라운드 시트

```
THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:
```
`<assets/reference/anchor/style_ref.png>`
```
THIS main — 이 캐릭터의 턴어라운드 시트야. 외형만 따라 그려줘:
```
`<O_multiview_ref/O_sheet_v2.png>` (캐릭터 4뷰 시트)
```
THIS spinning_wheel — 이 소품의 턴어라운드 시트야. 형태만 따라 그려줘:
```
`<P_prop_turnaround/P_spinning_wheel_sheet.png>` (소품 4뷰: 정면/측면/상면/3/4)

## 공통 flow_prompt

```
THIS style의 드로잉 스타일로, 유튜브 교육 영상에 사용할
서사적인 삽화 한 장을 그려줘.

배경은 순백의 빈 공간이되, 바닥선이 희미하게 암시되어 있어.

화면 좌측에 THIS main이 전체 화면의 약 13%, THIS spinning_wheel보다
약간 작게 서 있어. 약한 C자 곡선으로 어깨가 축 늘어진 채 한 발을
앞으로 내놓고 한 손에 작은 급료 주머니를 들고 내려다보며 반쪽 미소를
짓고 있어 — '이만하면 됐지 뭐'라는 나른한 만족의 순간이야.

배경 좌측 멀리에 THIS spinning_wheel이 THIS main의 절반 크기로
놓여 있어 — 먼지가 쌓인 듯 가느다란 거미줄 해칭 한 줄이 바퀴에
걸려 있어.

반드시 급료 주머니에만 warm gold 워시를 입혀줘 — 유일한 색이야.
하나의 장면만 그려줘. 정확히 THIS main 1명과 THIS spinning_wheel 1개만 그려줘.
```

## 설정
- model: gemini-3.1-flash-image-preview
- thinking_level: HIGH

## 결과

| 기준 | 대조군 (소품 단일 뷰) | 실험군 (소품 턴어라운드 시트) |
|------|-------------------|------------------------|
| 물레 구조 정확도 | 바퀴+방추+다리 있으나 비율 불균형 | 바퀴+실패 거치대+다리 — 구조가 더 정확 |
| 거미줄 디테일 | 없음 | 바퀴에 거미줄 해칭 보임 |
| 물레 크기 비율 | 캐릭터의 ~60% | 캐릭터의 ~50% (프롬프트 의도에 더 가까움) |
| 캐릭터 넥커치프 색 | sage-green 없음 | sage-green 워시 있음 |

소품 턴어라운드 시트가 구조 정확도와 프롬프트 디테일 반영률 모두 향상.
