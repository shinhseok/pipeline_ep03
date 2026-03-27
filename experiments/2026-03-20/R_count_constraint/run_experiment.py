"""실험 R — 카운트 제약의 필요성 검증"""
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


def gen(name, contents_list):
    response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=contents_list,
        config=types.GenerateContentConfig(
            response_modalities=["image", "text"],
            thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.HIGH),
        ),
    )
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            out_path = OUT_DIR / f"{name}.png"
            out_path.write_bytes(part.inline_data.data)
            print(f"  OK {name}.png")
            return True
    print(f"  FAIL {name}")
    return False


# 확정 템플릿 적용 — 통일된 라벨, style_ref 항상 포함
def build_base_contents():
    contents = [
        "THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:",
        read_image(STYLE_REF),
        "THIS main — 이 대상의 형태만 따라 그려줘:",
        read_image(MAIN_SHEET),
    ]
    return contents


# 공통 프롬프트 (마지막 줄만 다름)
PROMPT_BASE = """THIS style의 드로잉 스타일로, 유튜브 교육 영상에 사용할
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

반드시 거대 블록에만 deep amber 워시를 입혀줘 — 이것이 이 그림의 유일한 색이야."""

VARIANTS = {
    "R1_full_count": PROMPT_BASE + "\n하나의 장면만 그려줘. 정확히 THIS main 1명과 블록 2개만 그려줘.",
    "R2_scene_guard_only": PROMPT_BASE + "\n하나의 장면만 그려줘.",
    "R3_no_guard": PROMPT_BASE,
}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, choices=list(VARIANTS.keys()) + ["all"])
    args = parser.parse_args()

    targets = VARIANTS if args.run == "all" else {args.run: VARIANTS[args.run]}

    for name, prompt in targets.items():
        print(f"\n[{name}]")
        contents = build_base_contents()
        contents.append(prompt)
        gen(name, contents)
        time.sleep(2)
