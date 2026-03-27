"""
generate_videos.py
==================
05_visual_direction의 iv_prompt + asset_path(시작 이미지)로
Veo 2 I2V(Image-to-Video) API를 호출하여 영상 클립을 생성합니다.

실행 방법:
  python scripts/generate_videos.py --project CH02
  python scripts/generate_videos.py --project CH02 --section SECTION01
  python scripts/generate_videos.py --project CH02 --shots 7,8,9
  python scripts/generate_videos.py --project CH02 --overwrite
  python scripts/generate_videos.py --project CH02 --duration 5

매니페스트 모드 (version_manifest.yaml 존재 시):
  python scripts/generate_videos.py --project CH02              ← current_run 자동 해상도
  python scripts/generate_videos.py --project CH01 --version v5 ← 레거시 강제 지정

출력 경로:
  09_assets/videos/{RUN_ID}/shot{NN}.mp4

사전 조건:
  - 09_assets/images/{RUN_ID}/shot{NN}.png 존재 (generate_images.py 먼저 실행)
  - .env에 VERTEX_PROJECT 설정 + gcloud auth application-default login 완료
  - pip install google-genai
"""

import os
import re
import sys
import time
import yaml
import textwrap
import argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("[ERROR] google-genai 패키지가 없습니다. 아래 명령을 실행하세요:")
    print("  pip install google-genai")
    sys.exit(1)


SCRIPT_DIR = Path(__file__).parent
WORKSPACE_ROOT = SCRIPT_DIR.parents[3]  # scripts/ → generate-videos/ → skills/ → .claude/ → workspace root

# Veo 3 모델 (SFX+Ambient 오디오 내장 생성)
VEO_MODEL = "veo-3.0-generate-001"

SECTION_ORDER = [
    "TITLECARD",
    "SECTION00_HOOK",
    "SECTION01",
    "SECTION02",
    "SECTION03",
    "SECTION04_OUTRO",
]


# ── iv_prompt 파싱 ──────────────────────────────────────────

def parse_iv_prompt(raw: str) -> tuple[str, int | None]:
    """iv_prompt 원문에서 [thinking:] 접두어를 제거하고 Duration 값을 추출.

    반환: (정제된 프롬프트 텍스트, duration_seconds or None)
    """
    lines = raw.strip().splitlines()
    clean_lines = []
    duration = None

    for line in lines:
        stripped = line.strip()
        # [thinking: high/low] 제거
        if re.match(r"^\[thinking:\s*(high|low)\]", stripped, re.IGNORECASE):
            continue
        # "Duration: Ns" 파싱 후 제거
        m_dur = re.search(r"Duration:\s*(\d+(?:\.\d+)?)\s*s", stripped, re.IGNORECASE)
        if m_dur:
            duration = int(float(m_dur.group(1)))
            # Duration 문장 전체를 제거하지 않고 텍스트는 유지 (Veo가 duration 힌트로 쓸 수 있음)
        clean_lines.append(line)

    # 후행 --- 제거
    while clean_lines and clean_lines[-1].strip() in ("---", ""):
        clean_lines.pop()

    return "\n".join(clean_lines).strip(), duration


# ── YAML 파싱 ──────────────────────────────────────────

def parse_shot_record(text: str) -> dict | None:
    """05_visual_direction 파일에서 shot_id, iv_prompt, asset_path를 추출."""
    yaml_match = re.search(r"```yaml\n(.*?)```", text, re.DOTALL)
    content = yaml_match.group(1) if yaml_match else text

    # shot_id
    m_id = re.search(r"^shot_id:\s*(\S+)", content, re.MULTILINE)
    if not m_id:
        return None

    # asset_path
    m_path = re.search(r"^asset_path:\s*(.+)", content, re.MULTILINE)
    if not m_path:
        return None

    # iv_prompt (멀티라인)
    m_iv = re.search(
        r"^iv_prompt:\s*\|\s*\n(.*?)(?=\n[a-zA-Z#]|\Z)",
        content, re.MULTILINE | re.DOTALL
    )
    if not m_iv:
        return None

    iv_raw = textwrap.dedent(m_iv.group(1)).strip()
    if not iv_raw or iv_raw in ("~", "null"):
        return None

    return {
        "shot_id": m_id.group(1),
        "asset_path": m_path.group(1).strip(),
        "iv_prompt_raw": iv_raw,
    }


# ── 비디오 경로 계산 ──────────────────────────────────────────

def image_path_to_video_path(asset_path: str) -> str:
    """09_assets/images/{RUN_ID}/shot{N}.png → 09_assets/videos/{RUN_ID}/shot{N}.mp4"""
    return re.sub(
        r"09_assets/images/([^/]+)/(shot\d+)\.png",
        r"09_assets/videos/\1/\2.mp4",
        asset_path,
    )


# ── Veo 2 I2V 호출 ──────────────────────────────────────────

def generate_video(
    client,
    image_path: Path,
    prompt_text: str,
    duration_seconds: int = 4,
    aspect_ratio: str = "16:9",
    poll_interval: int = 15,
) -> bytes:
    """이미지 + 텍스트 프롬프트로 I2V 비디오를 생성하여 bytes 반환.

    Veo 2는 장시간 작업(Long-Running Operation)을 사용하므로 polling이 필요합니다.
    """
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    suffix = image_path.suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(
        suffix, "image/png"
    )

    print(f"   > Veo 2 I2V 요청 중... (duration: {duration_seconds}s)")

    operation = client.models.generate_video(
        model=VEO_MODEL,
        prompt=prompt_text,
        config=types.GenerateVideoConfig(
            image=types.Image(image_bytes=image_bytes, mime_type=mime),
            aspect_ratio=aspect_ratio,
            duration_seconds=duration_seconds,
            number_of_videos=1,
            generate_audio=True,   # Veo 3: SFX+Ambient 오디오 자동 생성 (iv_prompt [AUDIO] 섹션 기반)
            enhance_prompt=False,  # 정밀하게 작성된 프롬프트이므로 자동 보정 비활성화
        ),
    )

    # Polling
    elapsed = 0
    while not operation.done:
        time.sleep(poll_interval)
        elapsed += poll_interval
        operation = client.operations.get(operation)
        print(f"   > 대기 중... ({elapsed}s)")

    if operation.error:
        raise RuntimeError(f"Veo 2 API 오류: {operation.error.message}")

    # 영상 데이터 추출
    for video in operation.result.generated_videos:
        if hasattr(video, "video") and hasattr(video.video, "video_bytes"):
            return video.video.video_bytes
        if hasattr(video, "video_bytes"):
            return video.video_bytes

    raise RuntimeError("API 응답에 비디오 데이터가 없습니다.")


# ── 파일 처리 ──────────────────────────────────────────

def process_file(
    client,
    filepath: Path,
    project_root: Path,
    default_duration: int,
    overwrite: bool,
    target_shot_ids: set = None,
) -> tuple[int, int]:
    text = filepath.read_text(encoding="utf-8")

    shot = parse_shot_record(text)
    if not shot:
        print(f"   [WARN] iv_prompt 또는 asset_path를 찾을 수 없습니다: {filepath.name}")
        return 0, 0

    shot_id = shot["shot_id"]

    if target_shot_ids is not None:
        try:
            if int(shot_id) not in target_shot_ids:
                return 0, 0
        except ValueError:
            return 0, 0

    image_rel = shot["asset_path"]
    video_rel = image_path_to_video_path(image_rel)

    out_path = project_root / video_rel
    if out_path.exists() and not overwrite:
        print(f"   [Shot {shot_id}] 이미 존재 → 스킵 ({video_rel})")
        return 0, 1

    # 시작 이미지 확인
    image_path = project_root / image_rel
    if not image_path.exists():
        print(f"   [Shot {shot_id}] ❌ 시작 이미지 없음: {image_rel}")
        print(f"   > generate_images.py를 먼저 실행하세요.")
        return 0, 0

    # iv_prompt 정제
    prompt_text, extracted_duration = parse_iv_prompt(shot["iv_prompt_raw"])
    duration = extracted_duration if extracted_duration else default_duration

    print(f"   [Shot {shot_id}] 🎬 생성 중... ({video_rel})")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        video_bytes = generate_video(client, image_path, prompt_text, duration)
        out_path.write_bytes(video_bytes)
        print(f"   ✅ 저장: {video_rel}")
        time.sleep(2)
        return 1, 0
    except Exception as e:
        print(f"   ❌ 오류 [Shot {shot_id}]: {e}")
        return 0, 0


# ── Video Hook 처리 ──────────────────────────────────────────

def parse_hook_video_fields(text: str) -> dict | None:
    """Shot 파일에서 Video Hook 필드를 추출.

    필수: hook_media_type: video, video_prompt, video_duration
    선택: video_engine (기본 veo3)
    """
    yaml_match = re.search(r"```yaml\n(.*?)```", text, re.DOTALL)
    content = yaml_match.group(1) if yaml_match else text

    m_media = re.search(r"^hook_media_type:\s*(\S+)", content, re.MULTILINE)
    if not m_media or m_media.group(1) != "video":
        return None

    m_id = re.search(r"^shot_id:\s*(\S+)", content, re.MULTILINE)
    if not m_id:
        return None

    m_prompt = re.search(
        r"^video_prompt:\s*\|\s*\n(.*?)(?=\n[a-zA-Z_#]|\Z)",
        content, re.MULTILINE | re.DOTALL
    )
    if not m_prompt:
        return None

    prompt_raw = textwrap.dedent(m_prompt.group(1)).strip()
    if not prompt_raw or prompt_raw in ("~", "null"):
        return None

    m_duration = re.search(r"^video_duration:\s*(\d+)", content, re.MULTILINE)
    m_engine = re.search(r"^video_engine:\s*(\S+)", content, re.MULTILINE)

    return {
        "shot_id": m_id.group(1),
        "prompt": prompt_raw,
        "duration": int(m_duration.group(1)) if m_duration else 6,
        "engine": m_engine.group(1) if m_engine else "veo3",
    }


def process_hook_file(
    client,
    filepath: Path,
    project_root: Path,
    run_id: str,
    overwrite: bool,
) -> tuple[int, int]:
    """Video Hook Shot에서 start 이미지 + video_prompt로 영상을 생성."""
    text = filepath.read_text(encoding="utf-8")
    hook = parse_hook_video_fields(text)
    if not hook:
        return 0, 0

    shot_id = hook["shot_id"]
    shot_num = int(shot_id)

    # start 이미지 경로 (Phase 0에서 생성된 것)
    start_image = project_root / "09_assets" / "images" / run_id / f"shot{shot_num:02d}_start.png"
    if not start_image.exists():
        print(f"   [Hook Shot {shot_id}] ❌ Start 이미지 없음: {start_image.relative_to(project_root)}")
        print(f"   > generate_images.py --phase 0 을 먼저 실행하세요.")
        return 0, 0

    # 출력 경로
    out_dir = project_root / "09_assets" / "videos" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"shot{shot_num:02d}_hook.mp4"

    if out_path.exists() and not overwrite:
        print(f"   [Hook Shot {shot_id}] 이미 존재 → 스킵")
        return 0, 1

    print(f"   [Hook Shot {shot_id}] 🎬 생성 중... (engine: {hook['engine']}, duration: {hook['duration']}s)")

    try:
        video_bytes = generate_video(
            client,
            start_image,
            hook["prompt"],
            hook["duration"],
        )
        out_path.write_bytes(video_bytes)
        print(f"   ✅ 저장: 09_assets/videos/{run_id}/shot{shot_num:02d}_hook.mp4")
        time.sleep(2)
        return 1, 0
    except Exception as e:
        print(f"   ❌ 오류 [Hook Shot {shot_id}]: {e}")
        return 0, 0


# ── 매니페스트 유틸 ──────────────────────────────────────────

def _read_manifest(project_root):
    """version_manifest.yaml에서 current_run과 섹션 정보를 읽는다."""
    manifest_path = project_root / "version_manifest.yaml"
    if not manifest_path.exists():
        return None, None
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    current_run = manifest.get("current_run")
    last_run = manifest.get("runs", [{}])[-1]
    sections = last_run.get("sections", None)  # None = 전체
    return current_run, sections


def _resolve_path(project_root, stage, run_id, section):
    """stage/run_id/section 경로를 반환한다."""
    return project_root / stage / run_id / section


def _collect_manifest_files(project_root, current_run: str, section_filter: str = None) -> list[Path]:
    target_sections = [section_filter] if section_filter else SECTION_ORDER
    files = []
    for section in target_sections:
        section_dir = _resolve_path(project_root, "05_visual_direction", current_run, section)
        if section_dir and section_dir.exists():
            files.extend(sorted(section_dir.glob("shot*.md")))
    return files


def _collect_legacy_files(visual_dir: Path, section_filter: str = None) -> list[Path]:
    files = []
    for section in SECTION_ORDER:
        if section_filter and section_filter.upper() not in section:
            continue
        sec_dir = visual_dir / section
        if sec_dir.exists():
            files.extend(sorted(sec_dir.glob("shot*.md")))
    return files


# ── 메인 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="iv_prompt 기반 Veo 2 I2V 비디오 생성기")
    parser.add_argument("--project", required=True, help="프로젝트 코드 (예: CH02)")
    parser.add_argument("--section", help="처리할 섹션 (예: SECTION01). 생략 시 전체")
    parser.add_argument("--overwrite", action="store_true", help="기존 파일 덮어쓰기")
    parser.add_argument("--shots", help="처리할 Shot ID 목록 (쉼표 구분, 예: 7,8,9)")
    parser.add_argument("--duration", type=int, default=4, help="기본 영상 길이(초). iv_prompt에 Duration: Ns 있으면 그 값 우선 (기본: 4)")
    parser.add_argument("--version", default=None, help="버전 (레거시: v1 등. 생략 시 매니페스트 자동)")
    parser.add_argument("--hook", action="store_true", help="Video Hook 영상만 생성 (SECTION00_HOOK, hook_media_type: video)")
    args = parser.parse_args()

    target_shot_ids = None
    if args.shots:
        target_shot_ids = {int(s.strip()) for s in args.shots.split(",") if s.strip().isdigit()}

    project_root = WORKSPACE_ROOT / "projects" / args.project
    if not project_root.exists():
        print(f"[ERROR] 프로젝트 폴더를 찾을 수 없습니다: {project_root}")
        sys.exit(1)

    # .env 로드
    env_path = WORKSPACE_ROOT / ".env"
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
    print(f"\n🚀 generate_videos.py 시작 (Project: {args.project}, Model: {VEO_MODEL})")
    if args.overwrite:
        print("   > 덮어쓰기 모드 활성화")

    # 매니페스트 vs 레거시
    if args.version:
        version = args.version
        run_sections = None
        use_manifest = False
    else:
        version, run_sections = _read_manifest(project_root)
        use_manifest = version is not None
        if not use_manifest:
            print("[ERROR] --version 미지정 + version_manifest.yaml 없음. --version v1 등으로 지정하세요.")
            sys.exit(1)

    current_run = version if use_manifest else (args.version or "v1")

    # --hook: Video Hook 영상 전용 모드
    if args.hook:
        print(f"   > Video Hook 모드 (--hook)")
        hook_dir = project_root / "05_visual_direction" / current_run / "SECTION00_HOOK"
        if not hook_dir.exists():
            print(f"[ERROR] SECTION00_HOOK 폴더 없음: {hook_dir}")
            sys.exit(1)

        hook_files = sorted(hook_dir.glob("shot*.md"))
        if not hook_files:
            print("[ERROR] SECTION00_HOOK에 Shot 파일 없음")
            sys.exit(1)

        print(f"   > 대상 파일: {len(hook_files)}개\n")

        total_generated = 0
        total_skipped = 0

        for f in hook_files:
            print(f"\n📄 {f.name}")
            gen, skip = process_hook_file(client, f, project_root, current_run, args.overwrite)
            total_generated += gen
            total_skipped += skip

        print(f"\n✅ Hook 영상 완료 — 생성: {total_generated}개 / 스킵: {total_skipped}개")
        print(f"   저장 위치: projects/{args.project}/09_assets/videos/{current_run}/")
        return

    if use_manifest:
        print(f"   > 매니페스트 모드 (Run: {current_run})")
        target_files = _collect_manifest_files(project_root, current_run, args.section)
    else:
        visual_dir = project_root / "05_visual_direction" / version
        if not visual_dir.exists():
            print(f"[ERROR] 05_visual_direction 폴더가 없습니다: {visual_dir}")
            sys.exit(1)
        target_files = _collect_legacy_files(visual_dir, args.section)

    if not target_files:
        section_msg = f"섹션 '{args.section}'" if args.section else "전체"
        print(f"[ERROR] 처리할 파일이 없습니다 ({section_msg})")
        sys.exit(1)

    print(f"   > 대상 파일: {len(target_files)}개\n")

    total_generated = 0
    total_skipped = 0

    for f in target_files:
        print(f"\n📄 {f.name}")
        gen, skip = process_file(client, f, project_root, args.duration, args.overwrite, target_shot_ids)
        total_generated += gen
        total_skipped += skip

    print(f"\n✅ 완료 — 생성: {total_generated}개 / 스킵: {total_skipped}개")
    print(f"   저장 위치: projects/{args.project}/09_assets/videos/")


if __name__ == "__main__":
    main()
