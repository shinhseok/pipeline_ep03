"""실험 O — shot12 씬을 턴어라운드 시트 ref vs 단일 뷰 ref로 비교"""
import sys, os
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
REF_DIR = Path(__file__).resolve().parents[3] / "projects/CH02E2/09_assets/reference"
STYLE_REF = Path(__file__).resolve().parents[1] / "style4_no_character.png"

SINGLE_REF = REF_DIR / "characters/run002/main.jpeg"
SHEET_REF = OUT_DIR / "O_sheet_v2.png"
GEAR_REF = REF_DIR / "props/run002/gear.jpeg"

# shot12 프롬프트 — L_final_optimized 기준 (외형/스타일 텍스트 제거)
PROMPT = """THIS style의 드로잉 스타일로, 유튜브 교육 영상에 사용할
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
하나의 장면만 그려줘. 정확히 THIS main 1명과 블록 2개만 그려줘."""


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


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, choices=["control", "experiment"])
    args = parser.parse_args()

    if args.run == "control":
        print("[O-control] 대조군 — 단일 3/4뷰 ref")
        contents = [
            "THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:",
            read_image(STYLE_REF),
            "THIS main — 이 캐릭터의 외형만 따라 그려줘:",
            read_image(SINGLE_REF),
            "THIS gear — 이 소품의 형태만 따라 그려줘:",
            read_image(GEAR_REF),
            PROMPT,
        ]
        gen("O_scene_control", contents)

    elif args.run == "experiment":
        print("[O-experiment] 실험군 — 4뷰 턴어라운드 시트 ref")
        contents = [
            "THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:",
            read_image(STYLE_REF),
            "THIS main — 이 캐릭터의 턴어라운드 시트야. 외형만 따라 그려줘:",
            read_image(SHEET_REF),
            "THIS gear — 이 소품의 형태만 따라 그려줘:",
            read_image(GEAR_REF),
            PROMPT,
        ]
        gen("O_scene_experiment", contents)
