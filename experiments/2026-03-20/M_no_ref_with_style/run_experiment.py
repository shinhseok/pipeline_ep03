"""실험 M — ref_image 없는 shot에 style_ref를 적용하는 실험"""
import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from pathlib import Path
from google import genai
from google.genai import types

# .env 파일에서 API 키 로드
_env_path = Path(__file__).parent.parent.parent.parent / ".env"
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

STYLE_REF = Path(__file__).parent.parent / "style3_ref.png"
OUT_DIR = Path(__file__).parent

SHOTS = {
    14: """제공된 참조 이미지의 드로잉 스타일로, 유튜브 교육 영상에 사용할
서사적인 삽화 한 장을 그려줘.

배경은 아무런 색이나 질감이 없는 순백의 빈 공간으로 남겨둬.

화면 중앙에 물레에서 나온 실 한 올이 수직으로 늘어져 있어 —
전체 화면의 약 10%, 중간에서 가늘어지다 끊어진 채 끝이 아래로
힘없이 축 늘어져 있어. 끊어진 실의 아래쪽 끝이 바닥을 향해
힘없이 떨어지는 순간이야. 나머지 화면은 순백의 여백이야.

반드시 실에만 faded blue 워시를 입혀줘 — 이것이 이 그림의 유일한 색이야.
하나의 장면만 그려줘. 정확히 끊어진 실 한 올만 그려줘.""",

    27: """제공된 참조 이미지의 드로잉 스타일로, 유튜브 교육 영상에 사용할
서사적인 삽화 한 장을 그려줘.

배경은 아무런 색이나 질감이 없는 순백의 빈 공간으로 남겨둬.

화면 하단 중앙에 바닥에 놓인 작은 실타래 하나가 전체 화면의 약
5%로 있어. 실타래에서 실 한 올이 짧게 이어지다 끊어져 있어 —
끊어진 실 끝이 바닥에 가만히 놓여 있는 평온이야. 나머지 화면은
순백의 여백 88%야.

반드시 실타래에만 warm cream 워시를 입혀줘 — 이것이 이 그림의 유일한 색이야.
하나의 장면만 그려줘. 정확히 실타래 1개만 그려줘.""",

    40: """제공된 참조 이미지의 드로잉 스타일로, 유튜브 교육 영상에 사용할
서사적인 삽화 한 장을 그려줘.

배경은 아무런 색이나 질감이 없는 순백의 빈 공간으로 남겨둬.

화면 중앙 하단에 빈 의자 하나가 전체 화면의 약 10%로 놓여 있어
— 누군가 앉아 있었으나 지금은 비어 있는 부재의 상징이야. 의자
위에 아무것도 없어. 나머지는 순백의 여백 85%야.

채색은 없어.
하나의 장면만 그려줘. 정확히 빈 의자 1개만 그려줘.""",

    47: """제공된 참조 이미지의 드로잉 스타일로, 유튜브 교육 영상에 사용할
서사적인 삽화 한 장을 그려줘.

배경은 아무런 색이나 질감이 없는 순백의 빈 공간으로 남겨둬.

화면 중앙에 모니터 빛의 잔상만 남은 듯한 희미한 직사각형 윤곽(5%)
이 있어 — 사라져가는 빛이야. 나머지 85%는 순백 여백이야.

채색은 없어.
하나의 장면만 그려줘. 정확히 빛 잔상 윤곽만 그려줘.""",
}

def generate(shot_id, prompt):
    contents = []

    # style ref
    contents.append("THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:")
    with open(STYLE_REF, "rb") as f:
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
            out_path = OUT_DIR / f"shot{shot_id:02d}.png"
            out_path.write_bytes(part.inline_data.data)
            print(f"  ✅ shot{shot_id:02d}.png 저장")
            return
    print(f"  ❌ shot{shot_id:02d} — 이미지 없음")

if __name__ == "__main__":
    print(f"스타일 참조: {STYLE_REF.name} (exists: {STYLE_REF.exists()})")
    for shot_id, prompt in SHOTS.items():
        print(f"\n[Shot {shot_id}] 생성 중...")
        try:
            generate(shot_id, prompt)
        except Exception as e:
            print(f"  ❌ 오류: {e}")
