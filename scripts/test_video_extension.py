"""
Video Extension 테스트 — Hook 30초를 Veo 3.1 Video Extension으로 생성

방식: KF1 이미지 → 첫 8초 영상 → 7초씩 연장 × 3회 = ~29초
캐릭터 일관성·카메라 연속성이 자동 유지됨.
"""

import os
import sys
import io
import time

# Windows cp949 인코딩 문제 방지
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from google import genai
from google.genai import types

# 환경 설정
workspace_root = Path(__file__).parents[1].absolute()
env_path = workspace_root / ".env"
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

# 프로젝트 설정
project = "CH03"
run_id = "run002"
project_root = workspace_root / "projects" / project
image_dir = project_root / "09_assets" / "images" / run_id
output_dir = project_root / "09_assets" / "videos"
output_dir.mkdir(parents=True, exist_ok=True)

# KF1 이미지 (시작 프레임)
kf1_path = image_dir / "shot01.png"
if not kf1_path.exists():
    print(f"[ERROR] KF1 이미지를 찾을 수 없습니다: {kf1_path}")
    sys.exit(1)

# 캐릭터 reference 이미지
style_dir = workspace_root / "assets" / "reference" / "style"
main_turnaround = style_dir / "main_turnaround.jpeg"
char_ref = style_dir / "character_reference.jpeg"

print(f"🎬 Video Extension 테스트 시작")
print(f"   KF1: {kf1_path.name}")
print(f"   출력: {output_dir}")

# ── STEP 1: 첫 영상 생성 (KF1 이미지 → 8초) ──
print(f"\n📹 STEP 1: 첫 영상 생성 (KF1 → 8초)")

prompt_1 = """Cinematic drone-style tracking shot in pen-and-ink doodle style on pure white background.

A small bean-shaped character walks rightward along a simple platform. Camera moves alongside at walking pace. The character's steps quicken gradually, transitioning from a walk to a jog.

Steam wisps begin appearing from the right. The character looks up, noticing something approaching. The walking pace increases to running.

The character must remain visible and centered in frame throughout. Pen-and-ink sketch style with trembling hand-drawn lines."""

kf1_image = types.Image.from_file(location=str(kf1_path))

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt_1,
    image=kf1_image,
    config=types.GenerateVideosConfig(
        aspect_ratio="16:9",
    ),
)

print("   > 생성 중...")
while not operation.done:
    time.sleep(10)
    operation = client.operations.get(operation)
    print("   > ...")

video_1 = operation.response.generated_videos[0].video
client.files.download(file=video_1)
out_1 = output_dir / "hook_ext_step1.mp4"
video_1.save(str(out_1))
print(f"   ✅ 저장: {out_1.name}")

# ── STEP 2: 연장 1 (달리기 + 기차 도착 + 환호) ──
print(f"\n📹 STEP 2: 연장 1 — 달리기 + 기차 + 환호 (7초)")

prompt_2 = """The character runs faster rightward. A large steam locomotive enters from the right side of frame, filling the background. Small crowd silhouettes appear around the character.

The character slows and raises both arms in celebration. Crowd figures wave. Steam fills the air. Camera begins orbiting slightly around the character.

The character must remain visible in frame throughout. Same pen-and-ink sketch style."""

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    video=video_1,
    prompt=prompt_2,
    config=types.GenerateVideosConfig(
        resolution="720p"
    ),
)

print("   > 연장 중...")
while not operation.done:
    time.sleep(10)
    operation = client.operations.get(operation)
    print("   > ...")

video_2 = operation.response.generated_videos[0].video
client.files.download(file=video_2)
out_2 = output_dir / "hook_ext_step2.mp4"
video_2.save(str(out_2))
print(f"   ✅ 저장: {out_2.name}")

# ── STEP 3: 연장 2 (넓어진 세상 + 팔 벌림) ──
print(f"\n📹 STEP 3: 연장 2 — 넓어진 세상 (7초)")

prompt_3 = """Camera continues orbiting around the character. The crowd silhouettes drift out of frame. The locomotive recedes rightward, shrinking.

The background opens up into a vast empty landscape. The character slowly spreads arms wide, turning to face the open world. Camera pulls back gradually.

The character must remain visible in frame throughout. Same pen-and-ink sketch style."""

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    video=video_2,
    prompt=prompt_3,
    config=types.GenerateVideosConfig(
        resolution="720p"
    ),
)

print("   > 연장 중...")
while not operation.done:
    time.sleep(10)
    operation = client.operations.get(operation)
    print("   > ...")

video_3 = operation.response.generated_videos[0].video
client.files.download(file=video_3)
out_3 = output_dir / "hook_ext_step3.mp4"
video_3.save(str(out_3))
print(f"   ✅ 저장: {out_3.name}")

# ── STEP 4: 연장 3 (멈춤 + 고요) ──
print(f"\n📹 STEP 4: 연장 3 — 멈춤, 고요 (7초)")

prompt_4 = """Camera continues pulling back slowly. The character lowers arms to sides and stands completely still. The landscape is vast and empty. Only two parallel rail lines stretch to the right.

Everything is quiet. The character is a small figure in a vast white space. Complete stillness.

The character must remain visible in frame throughout. Same pen-and-ink sketch style."""

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    video=video_3,
    prompt=prompt_4,
    config=types.GenerateVideosConfig(
        resolution="720p"
    ),
)

print("   > 연장 중...")
while not operation.done:
    time.sleep(10)
    operation = client.operations.get(operation)
    print("   > ...")

video_4 = operation.response.generated_videos[0].video
client.files.download(file=video_4)
out_4 = output_dir / "hook_ext_step4.mp4"
video_4.save(str(out_4))
print(f"   ✅ 저장: {out_4.name}")

print(f"\n🎬 완료! 4개 영상 생성:")
print(f"   Step 1 (8s): {out_1}")
print(f"   Step 2 (연장 7s): {out_2}")
print(f"   Step 3 (연장 7s): {out_3}")
print(f"   Step 4 (연장 7s): {out_4}")
print(f"\n   총 ~29초. 편집에서 30초로 조정.")
