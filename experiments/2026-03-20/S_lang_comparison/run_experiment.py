"""실험 S — 한글 vs 영문 프롬프트 비교 (토큰 수 + 이미지 품질)"""
import sys, os, time
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from google import genai
from google.genai import types

_env_path = Path(__file__).resolve().parents[3] / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

client = genai.Client(
    vertexai=True,
    project=os.environ["VERTEX_PROJECT"],
    location=os.environ.get("VERTEX_LOCATION", "us-central1"),
)
OUT_DIR = Path(__file__).parent
ANCHOR_DIR = Path(__file__).resolve().parents[3] / "assets/reference/anchor"
O_DIR = Path(__file__).resolve().parents[1] / "O_multiview_ref"

STYLE_REF = ANCHOR_DIR / "style_ref.png"
MAIN_SHEET = O_DIR / "O_sheet_v2.png"


def read_image(path):
    mime = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    with open(path, "rb") as f:
        return types.Part.from_bytes(data=f.read(), mime_type=mime)


PROMPT_KO = """THIS style의 드로잉 스타일로, 유튜브 교육 영상에 사용할
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

반드시 거대 블록에만 deep amber 워시를 입혀줘 — 유일한 색이야."""

PROMPT_EN = """Draw a single narrative illustration in THIS style's drawing style,
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

Apply deep amber wash ONLY to the massive block — the only color."""


def gen(name, prompt):
    contents = [
        "THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:",
        read_image(STYLE_REF),
        "THIS main — 이 대상의 형태만 따라 그려줘:",
        read_image(MAIN_SHEET),
        prompt,
    ]

    start = time.time()
    response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["image", "text"],
            thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.HIGH),
        ),
    )
    elapsed = time.time() - start

    # 토큰 사용량
    usage = response.usage_metadata if hasattr(response, 'usage_metadata') else None
    if usage:
        print(f"  입력 토큰: {usage.prompt_token_count}")
        print(f"  출력 토큰: {usage.candidates_token_count}")
        print(f"  총 토큰: {usage.total_token_count}")
    print(f"  생성 시간: {elapsed:.1f}초")

    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            out_path = OUT_DIR / f"{name}.png"
            out_path.write_bytes(part.inline_data.data)
            print(f"  OK {name}.png")
            return usage, elapsed
    print(f"  FAIL {name}")
    return usage, elapsed


if __name__ == "__main__":
    # 토큰 수 사전 측정 (텍스트만)
    print("=== 프롬프트 길이 비교 ===")
    print(f"한글: {len(PROMPT_KO)}자 / {len(PROMPT_KO.encode('utf-8'))}바이트")
    print(f"영문: {len(PROMPT_EN)}자 / {len(PROMPT_EN.encode('utf-8'))}바이트")

    print("\n[S1] 한글 프롬프트")
    usage_ko, time_ko = gen("S1_korean", PROMPT_KO)

    time.sleep(3)

    print("\n[S2] 영문 프롬프트")
    usage_en, time_en = gen("S2_english", PROMPT_EN)

    print("\n=== 비교 요약 ===")
    if usage_ko and usage_en:
        print(f"한글 입력 토큰: {usage_ko.prompt_token_count} / 영문: {usage_en.prompt_token_count}")
        print(f"한글 총 토큰: {usage_ko.total_token_count} / 영문: {usage_en.total_token_count}")
    print(f"한글 시간: {time_ko:.1f}초 / 영문: {time_en:.1f}초")
