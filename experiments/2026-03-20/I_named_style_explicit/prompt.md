# I — Gemini API 최종 전달 content

## 목적
H에서 style_ref를 style2_ref.png(섬세한 연필 스케치 + 회색 워시)로 교체하고,
flow_prompt 안에 "THIS style의 드로잉 스타일로 그려줘"를 명시적으로 추가.
프롬프트 텍스트에서 THIS style을 직접 참조하면 스타일 적용이 되는지 검증.

## API에 전달된 content 배열 (순서대로)

```
THIS style — 이 이미지의 드로잉 스타일(선의 질감, 음영, 채색 기법)로 장면 전체를 그려줘:
```
`<style2_ref.png>` (섬세한 연필 스케치 + 회색 수채 워시, 사실적인 손)
```
THIS artisan — 이 캐릭터의 외형을 따라 그려줘:
```
`<artisan.jpeg>`
```
THIS gear — 이 소품의 형태를 따라 그려줘:
```
`<gear.jpeg>`
```
THIS style의 드로잉 스타일로 장면 전체를 그려줘.
THIS artisan과 THIS gear의 외형을 참조해서, 유튜브 교육 영상에 사용할
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

## H 대비 변경점
- style_ref: style_ref.png → style2_ref.png (연필 스케치 + 회색 워시)
- flow_prompt 첫 줄에 "THIS style의 드로잉 스타일로 장면 전체를 그려줘" 명시 추가

## 결과
style2_ref의 "섬세한 연필 스케치 + 회색 워시" 스타일이 적용되지 않음.
여전히 artisan.jpeg의 카툰 Sempé 스타일이 지배.
라벨 네이밍 + 프롬프트 내 명시적 참조를 해도 ref_image 스타일을 override 불가.
