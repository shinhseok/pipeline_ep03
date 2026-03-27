"""실험 P — 소품 턴어라운드 시트 (스타일 ref 참조) + 씬 비교"""
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
STYLE_REF = ANCHOR_DIR / "style_ref.png"


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


SHEET_PROMPT = """THIS style의 드로잉 스타일로, 18세기 목제 물레(spinning wheel)의
소품 턴어라운드 시트를 그려줘.

수평 한 줄로 4개 뷰를 나란히 배치:
1. 정면 (Front) — 큰 구동 바퀴가 정면으로 보이게, 발 디딤판이 아래에
2. 측면 (Side) — 완전한 우측 측면, 바퀴의 두께와 방추 장치가 보이게
3. 상면 (Top-down) — 위에서 내려다본 모습, 바퀴 원형과 프레임 구조
4. 3/4뷰 — 약간 위에서 비스듬히 본 모습, 입체감과 전체 구조

물레 특징:
- 큰 구동 바퀴(10개 얇은 살)
- 발 디딤판(treadle)
- 수평 방추 장치
- 실패 거치대(distaff)
- 참나무 색조 목제 프레임

모든 뷰에서:
- 동일한 물레 — 같은 형태, 같은 비율
- 높이 정렬 (정면/측면/3/4는 바닥선 맞춤)
- 채색 없이 잉크 라인만

순백 배경. 텍스트, 라벨, 화살표, 주석은 넣지 마."""


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", required=True, choices=["sheet"])
    args = parser.parse_args()

    if args.step == "sheet":
        print(f"style_ref: {STYLE_REF.name} (exists: {STYLE_REF.exists()})")
        print("\n[P-sheet] 물레 소품 턴어라운드 시트 생성 (정면 → 측면 → 상면 → 3/4)")
        contents = [
            "THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:",
            read_image(STYLE_REF),
            SHEET_PROMPT,
        ]
        gen("P_spinning_wheel_sheet", contents)
