"""실험 O — 다각도 레퍼런스 시트 생성 + 씬 이미지 비교"""
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

REF_DIR = Path(__file__).resolve().parents[3] / "projects/CH02E2/09_assets/reference"
STYLE_REF = Path(__file__).resolve().parents[1] / "style4_no_character.png"
OUT_DIR = Path(__file__).parent
MAIN_REF = REF_DIR / "characters/run002/main.jpeg"


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


def read_image(path, mime=None):
    if mime is None:
        mime = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    with open(path, "rb") as f:
        return types.Part.from_bytes(data=f.read(), mime_type=mime)


# ─── STEP 1: 다각도 시트 생성 ───
SHEET_PROMPT = """이 캐릭터의 정면, 후면, 좌측면, 우측면을 한 이미지에 나란히 그려줘.
4개의 뷰를 수평으로 배치하고, 각 뷰 사이에 여백을 넣어줘.
모든 뷰에서 동일한 캐릭터 — 같은 체형, 같은 넥커치프, 같은 드로잉 스타일.
순백 배경. 텍스트나 라벨은 넣지 마."""

# ─── STEP 2: 씬 생성 (대조군 — 현행 3/4뷰 단일 ref) ───
SCENE_PROMPT = """THIS style의 드로잉 스타일로, 유튜브 교육 영상에 사용할
서사적인 삽화 한 장을 그려줘.

배경은 순백의 빈 공간이되, 바닥선이 희미하게 암시되어 있어.

화면 중앙에 THIS main이 전체 화면의 약 20%로 서 있어.
뒷모습 — 관객에게 등을 보이고, 고개를 살짝 돌려 좌측 어깨 너머로
뒤를 돌아보는 자세야. 넥커치프 매듭이 등 쪽에서 보여야 해.
한 손은 자연스럽게 내리고, 다른 손은 살짝 올려 앞쪽을 가리키고 있어.

반드시 THIS main의 넥커치프에만 sage-green 워시를 입혀줘 — 유일한 색이야.
하나의 장면만 그려줘. 정확히 캐릭터 1명만 그려줘."""


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", required=True, choices=["sheet", "control", "experiment"])
    args = parser.parse_args()

    if args.step == "sheet":
        print("[O-sheet] 다각도 레퍼런스 시트 생성")
        contents = [
            "THIS main — 이 캐릭터의 외형만 따라 그려줘:",
            read_image(MAIN_REF),
            SHEET_PROMPT,
        ]
        gen("O_multiview_sheet", contents)

    elif args.step == "control":
        print("[O-control] 대조군 — 현행 3/4뷰 단일 ref로 뒷모습 씬")
        contents = [
            "THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:",
            read_image(STYLE_REF),
            "THIS main — 이 캐릭터의 외형만 따라 그려줘:",
            read_image(MAIN_REF),
            SCENE_PROMPT,
        ]
        gen("O_control_back", contents)

    elif args.step == "experiment":
        sheet_path = OUT_DIR / "O_multiview_sheet.png"
        if not sheet_path.exists():
            print("ERROR: 먼저 --step sheet 실행 필요")
            sys.exit(1)
        print("[O-experiment] 실험군 — 다각도 시트 ref로 뒷모습 씬")
        contents = [
            "THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:",
            read_image(STYLE_REF),
            "THIS main — 이 캐릭터의 다각도 레퍼런스야. 외형만 따라 그려줘:",
            read_image(sheet_path),
            SCENE_PROMPT,
        ]
        gen("O_experiment_back", contents)
