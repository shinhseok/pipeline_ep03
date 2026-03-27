# S — 한글 vs 영문 프롬프트 비교

## 목적
동일한 장면(shot12)을 한글/영문으로 각각 작성하여 토큰 사용량과 이미지 품질 비교.

## 공통 API content

```
THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:
```
`<style_ref.png>`
```
THIS main — 이 대상의 형태만 따라 그려줘:
```
`<O_sheet_v2.png>`

(라벨은 한글로 유지 — NB2 라벨은 한글이 확인됨)

## S1 — 한글 프롬프트

```
THIS style의 드로잉 스타일로, 유튜브 교육 영상에 사용할
서사적인 삽화 한 장을 그려줘.

배경은 순백의 빈 공간이되, 바닥선이 희미하게 암시되어 있어.

먼저 화면 좌측 상단을 보면 — 거대한 실타래 블록이 THIS main 키의
5배 높이로 솟아 있어. 꼭대기가 프레임 밖으로 잘릴 정도야. 실타래를
쌓아올린 듯한 추상적 블록 형태야. 그 옆 우측 하단에 작은 블록이
THIS main 키의 0.3배 크기로 놓여 있어. 두 블록 사이 아래, 화면 하단
중앙에 THIS main이 전체 화면의 약 10%, 거대한 블록의 5분의 1 크기로,
마치 산 앞에 선 개미처럼 뒤로 크게 젖히며 팔을 쭈욱 뻗어 올린 채
올려다보고 있어. 고개가 다 올라갔는데도 블록의 꼭대기가 보이지 않는
바로 그 찰나에 멈춰 있어. 눈이 동그랗게 커지고 입이 살짝 벌어진
표정이야.

반드시 거대 블록에만 deep amber 워시를 입혀줘 — 유일한 색이야.
```

## S2 — 영문 프롬프트

```
Draw a single narrative illustration in THIS style's drawing style,
for a YouTube educational video.

Background is bare white canvas with a faint floor line hinted.

Upper left of the frame — a massive yarn block towers 5x the height of
THIS main. Its top is cropped beyond the frame edge. Stacked yarn skeins
in an abstract block form. To its lower right, a small block sits at
0.3x THIS main's height. Between the two blocks below, at bottom center,
THIS main stands at about 10% of the frame, 1/5 the size of the massive
block, like an ant before a mountain — leaning far back with arms
stretched upward, looking up. Frozen at the exact moment when the head
is fully tilted back yet the top of the block is still not visible.
Eyes wide open, mouth slightly agape.

Apply deep amber wash ONLY to the massive block — the only color.
```

## 설정
- model: gemini-3.1-flash-image-preview
- thinking_level: HIGH

## 평가 기준
1. 입력 토큰 수 비교
2. 총 토큰 수 비교
3. 생성 시간 비교
4. 이미지 품질 (구도, 캐릭터 외형, 채색, 스타일)

## 결과

### 토큰/시간 비교

| 지표 | S1 한글 | S2 영문 | 차이 |
|------|--------|--------|------|
| 프롬프트 길이 | 472자 / 1,034B | 834자 / 840B | 한글이 짧음 |
| 입력 토큰 | 831 | 747 | 영문 ▼10% |
| 총 토큰 | 4,290 | 3,631 | 영문 ▼15% |
| 생성 시간 | 32.9초 | 48.2초 | 한글 ▼32% 빠름 |

### 이미지 품질 비교

| 기준 | S1 한글 | S2 영문 |
|------|--------|--------|
| 캐릭터 외형 | 넥커치프 ✅ | 넥커치프 ✅ |
| 블록 크기 대비 | 거대, 프레임 벗어남 ✅ | 거대, 프레임 벗어남 ✅ |
| 포즈 | 뒤로 젖히며 올려다봄 ✅ | 올려다봄 ✅ |
| 채색 제어 | amber만 ✅ 깔끔 | amber + **검은 잉크 얼룩 발생** ❌ |
| 배경 | 순백 ✅ | 검은 잉크 스플래시 ❌ |

### 결론: 한글 프롬프트가 품질+속도 모두 우세

영문이 토큰 15% 절감되지만, 한글이 생성 시간 32% 빠르고 이미지 품질이 더 깔끔.

**한글 우위 분석:**
1. **의미 밀도** — 한글 472자가 영문 834자보다 짧으면서 동일 의미 전달. 조사가 단어에 붙어 의미 밀도가 높음
2. **채색 제약 표현** — "유일한 색이야" (종결형 단정) vs "the only color" (명사구). 한국어 종결형이 NB2에 더 강한 제약으로 작용
3. **대화체 지시** — "~있어", "~거야" 등 자연스러운 대화형 지시가 NB2에 효과적
4. **영문 부작용** — "the only color" 제약이 약해서 의도하지 않은 검은 잉크 얼룩 발생

**파이프라인 확정: 한글 프롬프트 유지. 영문 전환 불필요.**
