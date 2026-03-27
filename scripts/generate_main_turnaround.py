"""
채널 공통 캐릭터 턴어라운드 시트 생성 (독립 실행)

character_reference.jpeg를 참조하여 2종 턴어라운드 시트를 생성한다:
  1. main_turnaround.jpeg — 해빛 메인 캐릭터 (넥커치프)
  2. crowd_turnaround.jpeg — 익명 캐릭터 (군중용, 의상/액세서리 없음)

실행:
  python scripts/generate_main_turnaround.py [--overwrite] [--target main|crowd|all]
"""

import os
import sys
import time
import argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("[ERROR] google-genai 패키지가 없습니다: pip install google-genai pillow")
    sys.exit(1)


WORKSPACE = Path(__file__).parent.parent.absolute()
STYLE_DIR = WORKSPACE / "assets" / "reference" / "style"
CHAR_REF = STYLE_DIR / "character_reference.jpeg"

# ── 생성 대상 정의 ──
TARGETS = {
    "main": {
        "output": STYLE_DIR / "main_turnaround.jpeg",
        "label": "THIS main — 이 캐릭터의 체형과 드로잉 스타일을 기반으로 그려줘:",
        "prompt": """\
THIS main의 드로잉 스타일과 체형을 기반으로,
해빛 메인 캐릭터의 턴어라운드 시트를 그려줘.

수평 한 줄로 4개 뷰를 나란히 배치:
1. 정면 (Front) — 얼굴이 정면을 향해, 넥커치프 매듭이 정면 중앙에 보여
2. 3/4뷰 (Front 3/4) — 약간 우측으로 돌린 자세, 넥커치프가 목을 감싸는 형태
3. 측면 (Side) — 완전한 우측 프로필, 넥커치프 끝자락이 뒤로 살짝 나부낌
4. 후면 (Back) — 완전한 뒷모습, 얼굴 안 보임, 넥커치프 매듭 뒷면과 엉덩이 라인 살짝

모든 뷰에서:
- THIS main과 동일한 콩 체형 — 같은 둥근 머리, 통통한 몸통, 짧은 팔다리 비율
- 똑바로 선 자세 (자연스러운 차렷)
- 머리/어깨/발 높이 정렬
- 캐릭터 구분 포인트: 머트 세이지 그린 넥커치프 (유일한 색)
- 앞: 넥커치프가 앞에서 매듭으로 묶여 있고, 작은 점 눈과 작은 미소
- 뒤: 넥커치프 끝자락이 뒤로 살짝 늘어지고, 엉덩이 라인이 살짝 보임

순백 배경. 텍스트, 라벨, 화살표, 주석은 넣지 마.""",
        "description": "메인 캐릭터 (넥커치프)",
    },
    "crowd": {
        "output": STYLE_DIR / "crowd_turnaround.jpeg",
        "label": "THIS main — 이 캐릭터의 체형과 드로잉 스타일을 기반으로 그려줘:",
        "prompt": """\
THIS main의 드로잉 스타일과 체형을 기반으로,
의상이나 액세서리가 전혀 없는 순수한 콩 캐릭터의 턴어라운드 시트를 그려줘.
이 캐릭터는 군중 장면에서 익명의 배경 캐릭터로 사용될 거야.

수평 한 줄로 4개 뷰를 나란히 배치:
1. 정면 (Front) — 얼굴이 정면을 향해, 작은 점 눈과 무표정에 가까운 중립적 입
2. 3/4뷰 (Front 3/4) — 약간 우측으로 돌린 자세
3. 측면 (Side) — 완전한 우측 프로필
4. 후면 (Back) — 완전한 뒷모습, 얼굴 안 보임, 엉덩이 라인 살짝

모든 뷰에서:
- THIS main과 동일한 콩 체형 — 같은 둥근 머리, 통통한 몸통, 짧은 팔다리 비율
- 똑바로 선 자세 (자연스러운 차렷)
- 머리/어깨/발 높이 정렬
- 넥커치프, 모자, 안경 등 어떤 의상이나 액세서리도 없음
- 전체가 순수 잉크 라인만 — 채색 없음
- 메인 캐릭터보다 약간 단순한 선 — 디테일 최소화

순백 배경. 텍스트, 라벨, 화살표, 주석은 넣지 마.""",
        "description": "익명 캐릭터 (군중용)",
    },
}


def generate_one(client, target_key: str, overwrite: bool) -> bool:
    """단일 턴어라운드 시트 생성. 성공 시 True."""
    target = TARGETS[target_key]
    output = target["output"]
    desc = target["description"]

    if output.exists() and not overwrite:
        print(f"   [{desc}] 이미 존재 → 스킵 ({output.name})")
        return False

    print(f"\n🎨 {desc} 턴어라운드 시트 생성")
    print(f"   참조: {CHAR_REF.name}")
    print(f"   출력: {output.relative_to(WORKSPACE)}")

    contents = []
    contents.append(target["label"])
    with open(CHAR_REF, "rb") as f:
        ref_bytes = f.read()
    contents.append(types.Part.from_bytes(data=ref_bytes, mime_type="image/jpeg"))
    contents.append(target["prompt"])

    print("   생성 중...")
    response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="16:9"),
            thinking_config=types.ThinkingConfig(
                thinking_level=types.ThinkingLevel.HIGH
            )
        )
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            output.write_bytes(part.inline_data.data)
            print(f"   ✅ 저장 완료: {output.relative_to(WORKSPACE)}")
            return True

    for part in response.candidates[0].content.parts:
        if part.text:
            print(f"   API Text: {part.text}")
    print(f"   ❌ 이미지 생성 실패")
    return False


def main():
    parser = argparse.ArgumentParser(description="채널 공통 캐릭터 턴어라운드 시트 생성")
    parser.add_argument("--overwrite", action="store_true", help="기존 파일 덮어쓰기")
    parser.add_argument("--target", default="all", choices=["main", "crowd", "all"],
                        help="생성 대상 (기본: all)")
    args = parser.parse_args()

    if not CHAR_REF.exists():
        print(f"[ERROR] 캐릭터 참조 이미지 없음: {CHAR_REF}")
        sys.exit(1)

    # .env 로드
    env_path = WORKSPACE / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

    vertex_project = os.environ.get("VERTEX_PROJECT")
    if not vertex_project:
        print("[ERROR] VERTEX_PROJECT 환경변수가 설정되지 않았습니다.")
        sys.exit(1)
    vertex_location = os.environ.get("VERTEX_LOCATION", "us-central1")

    client = genai.Client(vertexai=True, project=vertex_project, location=vertex_location)

    targets = list(TARGETS.keys()) if args.target == "all" else [args.target]
    generated = 0

    for key in targets:
        if generate_one(client, key, args.overwrite):
            generated += 1
            if key != targets[-1]:
                time.sleep(2)

    print(f"\n✅ 완료 — {generated}개 생성")


if __name__ == "__main__":
    main()
