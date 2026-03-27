# Q — "250년의 교차로" 전체 캐릭터+소품 복합 씬

## 목적
4 캐릭터 + 9 소품을 모두 THIS 네이밍으로 참조했을 때,
각 대상이 정확히 구분되어 배치되고 제어되는지 검증.
모든 캐릭터와 복잡 소품은 턴어라운드 시트를 사용.

## API에 전달된 content 배열 (순서대로)

```
THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:
```
`<assets/reference/anchor/style_ref.png>`

**캐릭터 턴어라운드 시트 4종:**
```
THIS main — 이 캐릭터의 턴어라운드 시트야. 외형만 따라 그려줘:
```
`<O_sheet_v2.png>`
```
THIS artisan — 이 캐릭터의 턴어라운드 시트야. 외형만 따라 그려줘:
```
`<sheet_artisan.png>`
```
THIS factory_worker — 이 캐릭터의 턴어라운드 시트야. 외형만 따라 그려줘:
```
`<sheet_factory_worker.png>`
```
THIS postman — 이 캐릭터의 턴어라운드 시트야. 외형만 따라 그려줘:
```
`<sheet_postman.png>`

**소품 턴어라운드 시트 4종:**
```
THIS spinning_wheel — 이 소품의 턴어라운드 시트야. 형태만 따라 그려줘:
```
`<P_spinning_wheel_sheet.png>`
```
THIS spinning_jenny — 이 소품의 턴어라운드 시트야. 형태만 따라 그려줘:
```
`<sheet_spinning_jenny.png>`
```
THIS power_loom — 이 소품의 턴어라운드 시트야. 형태만 따라 그려줘:
```
`<sheet_power_loom.png>`
```
THIS fence_post — 이 소품의 턴어라운드 시트야. 형태만 따라 그려줘:
```
`<sheet_fence_post.png>`

**단순 소품 단일 뷰 5종:**
```
THIS gear — 이 소품의 형태만 따라 그려줘:
```
`<gear.jpeg>`
```
THIS guitar — 이 소품의 형태만 따라 그려줘:
```
`<guitar.jpeg>`
```
THIS laptop — 이 소품의 형태만 따라 그려줘:
```
`<laptop.jpeg>`
```
THIS ink_drop — 이 소품의 형태만 따라 그려줘:
```
`<ink_drop.jpeg>`
```
THIS factory_chimney — 이 소품의 형태만 따라 그려줘:
```
`<factory_chimney.jpeg>`

**flow_prompt:**
```
THIS style의 드로잉 스타일로, 유튜브 교육 영상에 사용할
서사적인 파노라마 삽화 한 장을 그려줘.

"250년의 교차로" — 하나의 구불구불한 길 위에 네 캐릭터가 시간 순서로 서 있어.
좌측이 과거, 우측이 현재. 배경은 순백의 빈 공간이되, 바닥에 길이 이어져 있어.

화면 좌측 (수공예 시대):
THIS artisan이 전체 화면의 약 10%로, THIS spinning_wheel 옆에 앉아
실을 잣고 있어. 발 옆에 THIS guitar가 기대어 놓여 있어 — 일이 끝나면
연주할 것 같은 여유. THIS artisan은 편안한 미소.

그 오른쪽에 THIS fence_post가 길을 가로질러 — 시대의 경계.

화면 중앙 좌측 (산업혁명):
THIS factory_worker가 전체 화면의 약 10%로, THIS spinning_jenny 앞에
서 있어 — 어깨가 축 처지고 고개를 숙인 채. 뒤로 THIS power_loom이
캐릭터 키의 2배로 우뚝 솟아 있고, 그 위에 THIS factory_chimney가
연기를 내뿜고 있어. THIS gear가 power_loom 옆 바닥에 작게 놓여 있어.

화면 중앙에 THIS ink_drop이 공중에 떠 있어 — 시대의 전환점.
잉크가 떨어지는 순간.

화면 우측 (현대):
THIS postman이 전체 화면의 약 10%로, THIS laptop을 옆구리에 끼고
한 손을 앞으로 내밀며 관객을 향해 말하는 자세. 넓은 미소.

화면 맨 우측:
THIS main이 전체 화면의 약 12%로, 약간 높은 곳에서
전체 장면을 내려다보며 서 있어 — 고개를 살짝 갸우뚱 기울인 채
반쪽 미소. 모든 시대를 관통하는 관찰자.

채색:
- THIS artisan 모자에만 warm ochre 워시
- THIS factory_worker 두건에만 gray-blue 워시
- THIS postman 머리카락에만 dark brown 워시
- THIS main 넥커치프에만 sage-green 워시
- THIS ink_drop에만 crimson 워시
- 나머지는 모두 잉크 라인만

하나의 장면만 그려줘.
```

## 설정
- model: gemini-3.1-flash-image-preview
- thinking_level: HIGH
- 총 ref 이미지: 14장 (style 1 + 캐릭터 시트 4 + 소품 시트 4 + 단순 소품 5)

## 평가 기준
1. 4 캐릭터가 각각 구분되어 배치되는가 (의상/액세서리로 식별 가능)
2. 9 소품이 올바른 캐릭터 옆에 배치되는가
3. 시간 순서 (좌→우: 과거→현재) 유지되는가
4. 채색 — 각 캐릭터별 고유 색 1곳씩 정확한가
5. 14장의 ref_image를 NB2가 처리할 수 있는가 (용량 한계)

## 결과

14장 ref + THIS 네이밍으로 4캐릭터 + 9소품 동시 제어 **성공**.

| 기준 | 결과 |
|------|------|
| artisan (좌, 모자+앞치마) | ✅ warm ochre, 물레 옆 앉아서 |
| guitar (artisan 발 옆) | ✅ 기대어 놓임 |
| spinning_wheel | ✅ 물레 구조 |
| fence_post (시대 경계) | ✅ 길 위 울타리 |
| factory_worker (중앙, 두건) | ✅ gray-blue, 고개 숙임 |
| spinning_jenny + power_loom | ✅ 큰 기계 구조물 |
| factory_chimney | ✅ 굴뚝+연기 |
| gear | ✅ 바닥에 작게 |
| ink_drop (중앙 공중) | ✅ crimson |
| postman (우측, 웨이브머리) | ✅ dark brown, 넓은 미소, laptop |
| laptop | ✅ postman이 들고 있음 |
| main (맨 우측, 넥커치프) | ✅ sage-green, 높은 곳에서 관망 |
| 시간 순서 좌→우 | ✅ |
| 캐릭터 4명 즉시 식별 | ✅ |
