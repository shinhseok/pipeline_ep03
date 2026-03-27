"""실험 Q — 전체 캐릭터/소품 턴어라운드 시트 일괄 생성"""
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
MAIN_REF = ANCHOR_DIR / "main.jpeg"
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


# ─── 캐릭터 시트 (main.jpeg를 스타일+체형 레퍼런스로) ───

CHAR_TEMPLATE = """THIS main의 드로잉 스타일과 체형을 기반으로,
{description} 캐릭터의 턴어라운드 시트를 그려줘.

수평 한 줄로 4개 뷰를 나란히 배치:
1. 정면 (Front) — 얼굴이 정면을 향해
2. 3/4뷰 (Front 3/4) — 약간 우측으로 돌린 자세
3. 측면 (Side) — 완전한 우측 프로필
4. 후면 (Back) — 완전한 뒷모습, 얼굴 안 보임, 엉덩이 라인 살짝

모든 뷰에서:
- THIS main과 동일한 콩 체형 — 같은 머리/몸 비율
- 똑바로 선 자세 (자연스러운 차렷)
- 머리/어깨/발 높이 정렬
{costume_detail}

순백 배경. 텍스트, 라벨, 화살표, 주석은 넣지 마."""

CHARACTERS = {
    "artisan": {
        "description": "거친 리넨 작업복에 소매를 걷어올리고, 허리에 가죽 앞치마를 두르고, 머리에 부드러운 천 모자를 쓴",
        "costume_detail": "- 캐릭터 구분 포인트: 모자(warm-ochre 워시 유일한 색) + 앞치마\n- 앞: 앞치마 매듭, 뒤: 앞치마 끈이 등 뒤로",
    },
    "factory_worker": {
        "description": "너덜너덜한 작업복에 패치가 보이고, 머리에 먼지 묻은 두건을 쓰고, 그을린 앞치마를 두른",
        "costume_detail": "- 캐릭터 구분 포인트: 두건(gray-blue 워시 유일한 색) + 패치 달린 작업복\n- 앞: 작업복 앞면+패치, 뒤: 두건 뒷매듭+앞치마 끈",
    },
    "postman": {
        "description": "풍성한 웨이브 머리카락을 옆으로 넘기고, 심플한 캐주얼 재킷에 오픈 칼라 셔츠를 입은",
        "costume_detail": "- 캐릭터 구분 포인트: 웨이브 머리(dark-brown 워시 유일한 색) + 재킷\n- 안경 없음. 넓은 미소와 보이는 이빨\n- 앞: 재킷 앞여밈+셔츠 칼라, 뒤: 웨이브 머리 뒷모습+재킷 등판",
    },
}

# ─── 소품 시트 (style_ref.png를 스타일 레퍼런스로) ───

PROP_TEMPLATE = """THIS style의 드로잉 스타일로, {description}의
소품 턴어라운드 시트를 그려줘.

수평 한 줄로 4개 뷰를 나란히 배치:
1. 정면 (Front) — {front_detail}
2. 측면 (Side) — {side_detail}
3. 상면 (Top-down) — 위에서 내려다본 구조
4. 3/4뷰 — 약간 위에서 비스듬히, 입체감과 전체 구조

모든 뷰에서:
- 동일한 소품 — 같은 형태, 같은 비율
- 높이 정렬
- 채색 없이 잉크 라인만

순백 배경. 텍스트, 라벨, 화살표, 주석은 넣지 마."""

PROPS = {
    "spinning_jenny": {
        "description": "하그리브스 방적기(spinning jenny) — 사람 키만한 수평 목제 프레임, 8개 수직 방추, 우측 크랭크 바퀴, 레일 위 캐리지",
        "front_detail": "8개 방추가 일렬로 보이게, 크랭크 바퀴가 우측에",
        "side_detail": "캐리지와 레일 구조, 프레임 깊이",
    },
    "power_loom": {
        "description": "증기 역직기(power loom) — 사람 키 2배 높이의 주철 프레임, 노출된 기어와 구동 벨트, 넓은 직조 빔, 셔틀 메커니즘, 하단 증기관",
        "front_detail": "넓은 직조 빔이 정면으로, 셔틀 메커니즘 보이게",
        "side_detail": "기어+구동벨트+증기관 구조, 프레임 높이",
    },
    "fence_post": {
        "description": "거친 목재 울타리 — 참나무 기둥 3개, 수평 레일, 밧줄 이음새, 풍화된 회색 목재",
        "front_detail": "기둥 3개와 수평 레일이 정면으로",
        "side_detail": "기둥 두께와 레일 깊이",
    },
}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True, choices=["chars", "props", "all"])
    args = parser.parse_args()

    if args.type in ("chars", "all"):
        print(f"캐릭터 시트 생성 (스타일 ref: {MAIN_REF.name})")
        for name, info in CHARACTERS.items():
            prompt = CHAR_TEMPLATE.format(**info)
            print(f"\n[{name}] 턴어라운드 시트 생성 중...")
            contents = [
                "THIS main — 이 캐릭터의 체형과 드로잉 스타일을 기반으로 그려줘:",
                read_image(MAIN_REF),
                prompt,
            ]
            gen(f"sheet_{name}", contents)
            time.sleep(2)

    if args.type in ("props", "all"):
        print(f"\n소품 시트 생성 (스타일 ref: {STYLE_REF.name})")
        for name, info in PROPS.items():
            prompt = PROP_TEMPLATE.format(**info)
            print(f"\n[{name}] 턴어라운드 시트 생성 중...")
            contents = [
                "THIS style — 이 이미지의 드로잉 스타일로 장면 전체를 그려줘:",
                read_image(STYLE_REF),
                prompt,
            ]
            gen(f"sheet_{name}", contents)
            time.sleep(2)

    print("\n완료!")
