"""실험 P — shot09 대조군(단일 소품 ref) vs 실험군(소품 턴어라운드 시트)"""
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
ANCHOR_DIR = Path(__file__).resolve().parents[3] / "assets/reference/anchor"
REF_DIR = Path(__file__).resolve().parents[3] / "projects/CH02E2/09_assets/reference"
O_DIR = Path(__file__).resolve().parents[1] / "O_multiview_ref"

STYLE_REF = ANCHOR_DIR / "style_ref.png"
CHAR_SHEET = O_DIR / "O_sheet_v2.png"                          # 캐릭터 턴어라운드 (둘 다 동일)
PROP_SINGLE = REF_DIR / "props/run002/spinning_wheel.jpeg"     # 대조군: 단일 뷰
PROP_SHEET = OUT_DIR / "P_spinning_wheel_sheet.png"            # 실험군: 턴어라운드 시트

# shot09 프롬프트 — 최적화 버전 (외형/스타일 텍스트 제거, THIS 네이밍)
PROMPT = """THIS style의 드로잉 스타일로, 유튜브 교육 영상에 사용할
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
하나의 장면만 그려줘. 정확히 THIS main 1명과 THIS spinning_wheel 1개만 그려줘."""


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
        print("[P-control] 대조군 — 캐릭터 시트 + 소품 단일 뷰")
        contents = [
            "THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:",
            read_image(STYLE_REF),
            "THIS main — 이 캐릭터의 턴어라운드 시트야. 외형만 따라 그려줘:",
            read_image(CHAR_SHEET),
            "THIS spinning_wheel — 이 소품의 형태만 따라 그려줘:",
            read_image(PROP_SINGLE),
            PROMPT,
        ]
        gen("P_scene_control", contents)

    elif args.run == "experiment":
        print("[P-experiment] 실험군 — 캐릭터 시트 + 소품 턴어라운드 시트")
        contents = [
            "THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:",
            read_image(STYLE_REF),
            "THIS main — 이 캐릭터의 턴어라운드 시트야. 외형만 따라 그려줘:",
            read_image(CHAR_SHEET),
            "THIS spinning_wheel — 이 소품의 턴어라운드 시트야. 형태만 따라 그려줘:",
            read_image(PROP_SHEET),
            PROMPT,
        ]
        gen("P_scene_experiment", contents)
