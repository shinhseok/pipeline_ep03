# O-scene — shot12 대조군 vs 실험군

## 목적
동일한 프롬프트(shot12 장면)에서 단일 3/4뷰 ref vs 4뷰 턴어라운드 시트 ref의 차이 비교.

## 대조군 (control) — 단일 3/4뷰 ref

```
THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:
```
`<style4_no_character.png>`
```
THIS main — 이 캐릭터의 외형만 따라 그려줘:
```
`<characters/run002/main.jpeg>` (단일 3/4뷰)
```
THIS gear — 이 소품의 형태만 따라 그려줘:
```
`<props/run002/gear.jpeg>`

## 실험군 (experiment) — 4뷰 턴어라운드 시트 ref

```
THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:
```
`<style4_no_character.png>`
```
THIS main — 이 캐릭터의 턴어라운드 시트야. 외형만 따라 그려줘:
```
`<O_sheet_v2.png>` (정면/3/4/측면/후면 4뷰)
```
THIS gear — 이 소품의 형태만 따라 그려줘:
```
`<props/run002/gear.jpeg>`

## 공통 flow_prompt

```
THIS style의 드로잉 스타일로, 유튜브 교육 영상에 사용할
서사적인 삽화 한 장을 그려줘.

배경은 순백의 빈 공간이되, 바닥선이 희미하게 암시되어 있어.

먼저 화면 좌측 상단을 보면 — 거대한 실타래 블록이 THIS main 키의
5배 높이로 솟아 있어. 꼭대기가 프레임 밖으로 잘릴 정도야. 실타래를
쌓아올린 듯한 추상적 블록 형태야. 그 옆 우측 하단에 작은 블록이
THIS main 키의 0.3배 크기로 놓여 있어. 두 블록 사이 아래, 화면 하단
중앙에 THIS main이
전체 화면의 약 10%, 거대한 블록의 5분의 1 크기로, 마치 산 앞에
선 개미처럼 뒤로 크게 젖히며 팔을 쭈욱 뻗어 올린 채 올려다보고
있어. 고개가 다 올라갔는데도 블록의 꼭대기가 보이지 않는 바로 그
찰나에 멈춰 있어. 눈이 동그랗게 커지고 입이 살짝 벌어진 표정이야.

반드시 거대 블록에만 deep amber 워시를 입혀줘 — 이것이 이 그림의 유일한 색이야.
하나의 장면만 그려줘. 정확히 THIS main 1명과 블록 2개만 그려줘.
```

## 설정
- model: gemini-3.1-flash-image-preview
- thinking_level: HIGH

## 결과
(생성 후 기록)
