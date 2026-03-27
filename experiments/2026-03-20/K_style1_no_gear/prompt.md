# K — Gemini API 최종 전달 content

## 목적
J와 동일 구성이나 style_ref를 style2_ref.png → style_ref.png(굵은 해칭)로 교체.
ref_image 1장(artisan만) + style_ref 1장 구성에서 style_ref 효과 재확인.

## API에 전달된 content 배열 (순서대로)

```
THIS style — 이 이미지의 드로잉 스타일(선의 질감, 음영, 채색 기법)로 장면 전체를 그려줘:
```
`<style_ref.png>` (굵은 해칭, 검은 실루엣, 강한 대비)
```
THIS artisan — 이 캐릭터의 외형만 따라 그려줘:
```
`<artisan.jpeg>`
```
THIS style의 드로잉 스타일로 장면 전체를 그려줘.
THIS artisan의 외형만 참조해서, 유튜브 교육 영상에 사용할
서사적인 삽화 한 장을 그려줘.

배경은 순백의 빈 공간이되, 바닥선이 희미하게 암시되어 있어.

먼저 화면 좌측 상단을 보면 — 거대한 실타래 블록이 THIS artisan 키의
5배 높이로 솟아 있어. 꼭대기가 프레임 밖으로 잘릴 정도야. 실타래를
쌓아올린 듯한 추상적 블록 형태야. 그 옆 우측 하단에 작은 블록이
THIS artisan 키의 0.3배 크기로 놓여 있어. 두 블록 사이 아래, 화면 하단
중앙에 THIS artisan이
전체 화면의 약 10%, 거대한 블록의 5분의 1 크기로, 마치 산 앞에
선 개미처럼 뒤로 크게 젖히며 팔을 쭈욱 뻗어 올린 채 올려다보고
있어. 고개가 다 올라갔는데도 블록의 꼭대기가 보이지 않는 바로 그
찰나에 멈춰 있어. 눈이 동그랗게 커지고 입이 살짝 벌어진 표정이야.

반드시 거대 블록에만 deep amber 워시를 입혀줘 — 이것이 이 그림의 유일한 색이야.
하나의 장면만 그려줘. 정확히 THIS artisan 1명과 블록 2개만 그려줘.
```

## 설정
- model: gemini-3.1-flash-image-preview
- thinking_level: HIGH
- style_ref 전달 확인: 로그에 "스타일 참조 이미지: style_ref.png" 출력됨

## 결과
style_ref 스타일 적용 안 됨. artisan.jpeg 카툰 스타일이 여전히 지배.
API에 이미지는 전달되고 있으나, NB2가 style_ref의 스타일 지시를 무시함.
