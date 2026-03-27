"""실험 N — shot30 기반, 복수 ref 라벨 네이밍 제어 검증"""
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
STYLE_REF = Path(__file__).resolve().parents[1] / "style3_ref.png"
OUT_DIR = Path(__file__).parent

REFS = {
    "main":             REF_DIR / "characters/run002/main.jpeg",
    "gear":             REF_DIR / "props/run002/gear.jpeg",
    "factory_chimney":  REF_DIR / "props/run002/factory_chimney.jpeg",
}

# shot30: 메인 캐릭터가 양손 벌려 좌(기어+굴뚝)와 우(실루엣 군중)를 가리킴
PROMPT = """THIS style의 드로잉 스타일로, 유튜브 교육 영상에 사용할
서사적인 삽화 한 장을 그려줘.

배경은 순백의 빈 공간이되, 바닥선이 희미하게 암시되어 있어.

화면 중앙에 THIS main이 전체 화면의 약 15%로 서 있어.
고개를 살짝 갸우뚱 기울인 채 반쪽 미소를 머금고 양손을 벌려
양쪽을 가리키고 있어 — '이쪽에서 보면 혁명이지만...'이라는
아이러니의 순간이야.

좌측에 THIS gear와 THIS factory_chimney 아이콘 그룹이 프레임의
15%로 배치 — 역사의 눈(생산성 상징).
우측에 작은 콩 캐릭터 실루엣 5~6명(각 5%)이 — 둥근 머리와 짧은
팔다리, 얼굴 없는 실루엣이야 — 사람의 눈(희생).

반드시 THIS main의 넥커치프에만 sage-green 워시를 입혀줘 — 유일한 색이야.
하나의 장면만 그려줘. 정확히 캐릭터 1명, 실루엣 5~6명, 소품 2개만 그려줘."""


def generate(name, prompt, ref_names):
    contents = []

    contents.append("THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:")
    with open(STYLE_REF, "rb") as f:
        contents.append(types.Part.from_bytes(data=f.read(), mime_type="image/png"))

    for ref_name in ref_names:
        ref_path = REFS[ref_name]
        contents.append(f"THIS {ref_name} — 이 대상의 외형만 따라 그려줘:")
        with open(ref_path, "rb") as f:
            data = f.read()
        mime = "image/jpeg" if ref_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
        contents.append(types.Part.from_bytes(data=data, mime_type=mime))

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
            return
    print(f"  FAIL {name}")


if __name__ == "__main__":
    STYLE_REF_4 = Path(__file__).resolve().parents[1] / "style4_no_character.png"

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default="N2")
    args = parser.parse_args()

    if args.run == "N1":
        print(f"style: {STYLE_REF.name}")
        print("\n[N1] shot30 — style3_ref (캐릭터 포함)")
        generate("N1_shot30", PROMPT, ["main", "gear", "factory_chimney"])

    elif args.run == "N2":
        STYLE_REF = STYLE_REF_4
        print(f"style: {STYLE_REF.name} (캐릭터 없음)")
        print("\n[N2] shot30 — style4_no_character (캐릭터 없는 style_ref)")
        generate("N2_shot30", PROMPT, ["main", "gear", "factory_chimney"])
