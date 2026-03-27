"""실험 O — 턴어라운드 시트를 참조하여 역동적인 포즈 8개 생성"""
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
SHEET_REF = OUT_DIR / "O_sheet_v2.png"

PROMPT = """이 턴어라운드 시트의 캐릭터를 참고해서, 역동적인 포즈 8개를 한 화면에 그려줘.

2줄 × 4열 그리드로 배치:
1행: 달리기 | 점프 | 앉아서 생각 | 뒤돌아보기
2행: 팔 벌려 환호 | 웅크리기 | 한 손 가리키기 | 걷기

모든 포즈에서:
- 턴어라운드 시트와 동일한 캐릭터 — 같은 체형, 같은 넥커치프, 같은 드로잉 스타일
- 각 포즈마다 다양한 앵글 (정면, 측면, 3/4, 뒷모습 등 섞어서)
- 넥커치프의 sage-green 워시만 유일한 색
- 포즈 사이에 여백

순백 배경. 텍스트, 라벨, 화살표, 주석은 넣지 마."""


def gen(name, ref_path, prompt):
    contents = [
        "THIS main — 이 캐릭터의 턴어라운드 시트야. 외형과 드로잉 스타일을 따라 그려줘:",
    ]
    with open(ref_path, "rb") as f:
        contents.append(types.Part.from_bytes(data=f.read(), mime_type="image/png"))
    contents.append(prompt)

    response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=contents,
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
    print(f"ref: {SHEET_REF.name} (exists: {SHEET_REF.exists()})")
    print("\n[O-poses] 역동적 포즈 8개 생성")
    gen("O_poses_8", SHEET_REF, PROMPT)
