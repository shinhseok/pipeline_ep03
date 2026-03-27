"""실험 Q — 전체 캐릭터(4) + 소품(9) 복합 씬 생성"""
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
P_DIR = Path(__file__).resolve().parents[1] / "P_prop_turnaround"
STYLE_REF = ANCHOR_DIR / "style_ref.png"

# 턴어라운드 시트 경로
SHEETS = {
    # 캐릭터
    "main":           O_DIR / "O_sheet_v2.png",
    "artisan":        OUT_DIR / "sheet_artisan.png",
    "factory_worker": OUT_DIR / "sheet_factory_worker.png",
    "postman":        OUT_DIR / "sheet_postman.png",
    # 소품 (복잡 구조 — 시트)
    "spinning_wheel": P_DIR / "P_spinning_wheel_sheet.png",
    "spinning_jenny": OUT_DIR / "sheet_spinning_jenny.png",
    "power_loom":     OUT_DIR / "sheet_power_loom.png",
    "fence_post":     OUT_DIR / "sheet_fence_post.png",
}

# 단순 소품 (단일 뷰)
REF_DIR = Path(__file__).resolve().parents[3] / "projects/CH02E2/09_assets/reference"
SIMPLE_PROPS = {
    "gear":            REF_DIR / "props/run002/gear.jpeg",
    "guitar":          REF_DIR / "props/run002/guitar.jpeg",
    "laptop":          REF_DIR / "props/run002/laptop.jpeg",
    "ink_drop":        REF_DIR / "props/run002/ink_drop.jpeg",
    "factory_chimney": REF_DIR / "props/run002/factory_chimney.jpeg",
}

PROMPT = """THIS style의 드로잉 스타일로, 유튜브 교육 영상에 사용할
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

하나의 장면만 그려줘."""


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
    print("=== 250년의 교차로 — 전체 캐릭터 + 소품 복합 씬 ===\n")

    contents = []

    # style ref
    print(f"style: {STYLE_REF.name}")
    contents.append("THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:")
    contents.append(read_image(STYLE_REF))

    # 캐릭터 시트 (4종)
    for name, path in SHEETS.items():
        if name in ("main", "artisan", "factory_worker", "postman"):
            label = f"THIS {name} — 이 캐릭터의 턴어라운드 시트야. 외형만 따라 그려줘:"
            print(f"char: {name} <- {path.name}")
            contents.append(label)
            contents.append(read_image(path))

    # 소품 시트 (4종)
    for name, path in SHEETS.items():
        if name not in ("main", "artisan", "factory_worker", "postman"):
            label = f"THIS {name} — 이 소품의 턴어라운드 시트야. 형태만 따라 그려줘:"
            print(f"prop sheet: {name} <- {path.name}")
            contents.append(label)
            contents.append(read_image(path))

    # 단순 소품 (5종)
    for name, path in SIMPLE_PROPS.items():
        label = f"THIS {name} — 이 소품의 형태만 따라 그려줘:"
        print(f"prop single: {name} <- {path.name}")
        contents.append(label)
        contents.append(read_image(path))

    # 프롬프트
    contents.append(PROMPT)

    print(f"\n총 ref 이미지: {sum(1 for c in contents if hasattr(c, 'inline_data') or (hasattr(c, 'data') if hasattr(c, 'data') else False))}장")
    print("생성 중...\n")
    gen("Q_full_scene", contents)
