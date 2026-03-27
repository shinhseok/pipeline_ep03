"""다각도 레퍼런스 시트 생성 — 업계 표준 4뷰 (Front → 3/4 → Side → Back)"""
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
MAIN_REF = Path(__file__).resolve().parents[3] / "assets/reference/anchor/main.jpeg"
OUT_DIR = Path(__file__).parent

PROMPT = """이 캐릭터의 캐릭터 턴어라운드 시트를 그려줘.

수평 한 줄로 4개 뷰를 나란히 배치:
1. 정면 (Front) — 얼굴이 정면을 향해, 넥커치프 앞 매듭이 가슴 앞에 보이게
2. 3/4뷰 (Front 3/4) — 약간 우측으로 돌린 자세, 얼굴과 몸의 볼륨감
3. 측면 (Side) — 완전한 우측 프로필, 체형 실루엣과 넥커치프 드레이핑
4. 후면 (Back) — 완전한 뒷모습, 얼굴 안 보임. 엉덩이 부분에 살짝 갈라진 라인이 보여 뒷모습임을 알 수 있게

앞뒤 구분 규칙:
- 앞에서 보면: 얼굴 + 넥커치프 매듭
- 뒤에서 보면: 얼굴 없음 + 엉덩이 라인이 살짝 보임

모든 뷰에서:
- 동일한 캐릭터 — 같은 체형, 같은 넥커치프, 같은 비율
- 똑바로 선 자세 (T포즈 아님, 자연스러운 차렷 자세)
- 머리 높이, 어깨 높이, 발 위치가 4개 뷰 모두 수평 정렬
- 이 캐릭터의 드로잉 스타일을 그대로 유지

순백 배경. 텍스트, 라벨, 화살표, 주석은 절대 넣지 마."""

def gen(name):
    contents = [
        "THIS main — 이 캐릭터의 외형과 드로잉 스타일을 따라 그려줘:",
    ]
    with open(MAIN_REF, "rb") as f:
        contents.append(types.Part.from_bytes(data=f.read(), mime_type="image/jpeg"))
    contents.append(PROMPT)

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
    print(f"ref: {MAIN_REF.name}")
    print("[O-sheet] 4뷰 턴어라운드 시트 생성 (Front → 3/4 → Side → Back)")
    gen("O_sheet_v2")
