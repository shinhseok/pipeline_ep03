"""
validate_shot_records.py
Shot Record YAML 필드 검증 스크립트

사용법:
  python scripts/validate_shot_records.py                         # 07_shot_records/v1/ 전체
  python scripts/validate_shot_records.py --source 06            # 05_visual_direction/v1/ (delta)
  python scripts/validate_shot_records.py --source 07_audio      # 06_audio_narration/v1/ (delta)
  python scripts/validate_shot_records.py --section SECTION01    # 특정 Section만
  python scripts/validate_shot_records.py --strict               # 경고도 오류로 처리

매니페스트 모드:
  python scripts/validate_shot_records.py --project CH02                      # current_run 자동
  python scripts/validate_shot_records.py --project CH02 --run run001         # 특정 run 지정
  python scripts/validate_shot_records.py --project CH01 --source 06          # 레거시 (매니페스트 없음)
"""

import sys
import re
import yaml
import argparse
from pathlib import Path

# 프로젝트 루트 자동 탐지
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parents[3]  # scripts/ → run-directing/ → skills/ → .claude/ → workspace root

# STEP별 필수 필드 정의
REQUIRED_FIELDS = {
    "04": [
        "shot_id", "section", "local_id", "duration_est", "emotion_tag",
        "scene_type", "has_human", "narration_span", "creative_intent",
    ],
    "05": [
        "shot_id", "image_prompt", "has_human",
    ],
    "06_audio": [
        "shot_id", "scene_id", "el_narration", "bgm", "volume_mix",
    ],
    "06": [
        "shot_id", "section", "local_id", "duration_est", "emotion_tag",
        "scene_type", "has_human", "narration_span", "creative_intent",
        "image_prompt", "el_narration", "bgm", "volume_mix",
        "asset_path", "status",
    ],
}

# 허용 값 정의
VALID_STATUS = {"pending", "done", "skip"}
VALID_SCENE_TYPES = {
    "Doodle-Illust", "Doodle-Animation", "Text-Motion",
    "Doodle-Character", "Doodle-Diagram", "Whiteboard-Reveal",
}
VALID_HAS_HUMAN = {"main", "anonym", "none"}

# NB2 품질 접미사 금지 키워드
BANNED_NB2_KEYWORDS = ["4k", "masterpiece", "HD", "high quality", "ultra realistic", "photorealistic"]

# Hook 관련 허용 값
VALID_HOOK_TYPES = {"standard", "song"}
VALID_HOOK_MEDIA_TYPES = {"image", "video"}
VALID_VIDEO_ENGINES = {"veo3", "kling"}

# Suno Metatag 검증용
SUNO_REQUIRED_METATAGS = {"[Verse]", "[Hook]", "[End]"}

# 마커 관련 패턴
MARKER_PATTERN = re.compile(r"\{\{[A-Z_]+\}\}")


def parse_yaml_field(content: str, field: str) -> str | None:
    """YAML 파일에서 특정 필드값 추출 (단순 라인 기반)."""
    pattern = re.compile(rf"^{re.escape(field)}:\s*(.+)$", re.MULTILINE)
    match = pattern.search(content)
    return match.group(1).strip() if match else None


def parse_multiline_field(content: str, field: str) -> str | None:
    """멀티라인 필드 (image_prompt 등) 추출. 빈 줄 포함 허용."""
    pattern = re.compile(
        rf"^{re.escape(field)}:\s*\|\n((?:(?:  .*|)\n)*)", re.MULTILINE
    )
    match = pattern.search(content)
    return match.group(1) if match else None


def validate_shot_file(path: Path, step: str, strict: bool = False) -> list[dict]:
    """단일 Shot 파일 검증. 오류/경고 목록 반환."""
    issues = []
    content = path.read_text(encoding="utf-8")

    def add_issue(level: str, field: str, message: str):
        issues.append({"level": level, "field": field, "message": message, "file": str(path)})

    required = REQUIRED_FIELDS.get(step, [])

    # 필수 필드 존재 여부
    for field in required:
        value = parse_yaml_field(content, field)
        if value is None:
            # image_prompt는 멀티라인일 수 있음
            if field == "image_prompt":
                value = parse_multiline_field(content, field)
            if value is None:
                add_issue("ERROR", field, f"필수 필드 누락: {field}")

    # shot_id 타입 검증
    shot_id_val = parse_yaml_field(content, "shot_id")
    if shot_id_val is not None:
        try:
            int(shot_id_val)
        except ValueError:
            add_issue("ERROR", "shot_id", f"shot_id가 정수가 아님: '{shot_id_val}'")

    # duration_est 범위 검증 ({N}s 형식 또는 숫자 모두 허용)
    dur_val = parse_yaml_field(content, "duration_est")
    if dur_val is not None:
        dur_str = re.sub(r"s$", "", dur_val.strip(), flags=re.IGNORECASE)
        try:
            dur = float(dur_str)
            section_val = parse_yaml_field(content, "section") or ""
            is_titlecard = section_val.strip().upper() == "TITLECARD"
            if dur == 0 and is_titlecard:
                pass  # TITLECARD는 나레이션 없으므로 0s 정상
            elif dur <= 0 or dur > 30:
                add_issue("WARNING", "duration_est", f"duration_est 범위 이상: {dur}초 (권장 1~30)")
        except ValueError:
            add_issue("ERROR", "duration_est", f"duration_est가 숫자가 아님: '{dur_val}'")

    # has_human 값 검증 (3값: main/anonym/none)
    has_human_val = parse_yaml_field(content, "has_human")
    if has_human_val is not None:
        if has_human_val.lower() not in {"main", "anonym", "none", "true", "false"}:
            add_issue("ERROR", "has_human", f"has_human은 main/anonym/none만 허용: '{has_human_val}'")
        elif has_human_val.lower() in {"true", "false"}:
            add_issue("WARNING", "has_human", f"has_human 레거시 값 '{has_human_val}' → main/anonym/none으로 전환 필요")

    # status 값 검증
    status_val = parse_yaml_field(content, "status")
    if status_val is not None and status_val not in VALID_STATUS:
        add_issue("WARNING", "status", f"알 수 없는 status: '{status_val}'")

    # scene_type 검증
    scene_type_val = parse_yaml_field(content, "scene_type")
    if scene_type_val is not None and scene_type_val not in VALID_SCENE_TYPES:
        add_issue("WARNING", "scene_type", f"알 수 없는 scene_type: '{scene_type_val}'")

    # NB2 image_prompt 검증 (05, 07 단계)
    if step in ("05", "06"):
        image_prompt = parse_multiline_field(content, "image_prompt")
        if image_prompt is None:
            image_prompt = parse_yaml_field(content, "image_prompt") or ""

        if image_prompt:
            # 품질 접미사 금지어 검사
            for kw in BANNED_NB2_KEYWORDS:
                if kw.lower() in image_prompt.lower():
                    add_issue("ERROR", "image_prompt", f"NB2 금지 키워드 사용: '{kw}'")

            # v3 감지: ref_images YAML 필드 존재 → v3 (순수 한국어), 없으면 v2 (구조적 태그)
            is_v3 = parse_yaml_field(content, "ref_images") is not None or \
                    "ref_images:" in content

            if not is_v3:
                # v2 전용: [SOURCE REFERENCES] 블록 존재 여부
                if "[SOURCE REFERENCES]" not in image_prompt:
                    add_issue("WARNING", "image_prompt", "[SOURCE REFERENCES] 블록 없음 (v2)")

                # v2 전용: costume_refs 있는데 [CHARACTER SOURCE] 없음
                costume_refs_val = parse_yaml_field(content, "costume_refs")
                if costume_refs_val and costume_refs_val not in {"[]", "null", "~", ""}:
                    if "[CHARACTER SOURCE" not in image_prompt:
                        add_issue("WARNING", "image_prompt", "costume_refs 있으나 [CHARACTER SOURCE] 없음 (v2)")

    # Hook 확장 필드 검증 (SECTION00_HOOK Shot에만 적용)
    section_val = parse_yaml_field(content, "section") or ""
    is_hook_section = "HOOK" in section_val.upper()

    if is_hook_section and step in ("04", "05", "06"):
        # hook_type 검증
        hook_type_val = parse_yaml_field(content, "hook_type")
        if hook_type_val and hook_type_val not in VALID_HOOK_TYPES:
            add_issue("ERROR", "hook_type", f"알 수 없는 hook_type: '{hook_type_val}' (허용: {VALID_HOOK_TYPES})")

        # hook_media_type 검증
        hook_media_val = parse_yaml_field(content, "hook_media_type")
        if hook_media_val and hook_media_val not in VALID_HOOK_MEDIA_TYPES:
            add_issue("ERROR", "hook_media_type", f"알 수 없는 hook_media_type: '{hook_media_val}' (허용: {VALID_HOOK_MEDIA_TYPES})")

        # Video Hook: video_duration, video_engine 필수
        if hook_media_val == "video":
            video_dur = parse_yaml_field(content, "video_duration")
            if not video_dur:
                add_issue("ERROR", "video_duration", "hook_media_type: video인데 video_duration 누락")
            else:
                try:
                    dur_int = int(video_dur)
                    if dur_int < 1 or dur_int > 16:
                        add_issue("WARNING", "video_duration", f"video_duration 범위 이상: {dur_int}s (권장 1~16)")
                except ValueError:
                    add_issue("ERROR", "video_duration", f"video_duration이 정수가 아님: '{video_dur}'")

            video_eng = parse_yaml_field(content, "video_engine")
            if video_eng and video_eng not in VALID_VIDEO_ENGINES:
                add_issue("WARNING", "video_engine", f"알 수 없는 video_engine: '{video_eng}' (권장: {VALID_VIDEO_ENGINES})")

    # Song Hook Suno 필드 검증 (STEP 06 audio / 07 merged)
    if is_hook_section and step in ("06_audio", "06"):
        hook_type_val = parse_yaml_field(content, "hook_type")
        if hook_type_val == "song":
            suno_style = parse_yaml_field(content, "suno_style")
            if not suno_style:
                suno_style = parse_multiline_field(content, "suno_style")
            if not suno_style:
                add_issue("ERROR", "suno_style", "hook_type: song인데 suno_style 누락")

            suno_lyrics = parse_multiline_field(content, "suno_lyrics")
            if not suno_lyrics:
                suno_lyrics = parse_yaml_field(content, "suno_lyrics")
            if not suno_lyrics:
                add_issue("ERROR", "suno_lyrics", "hook_type: song인데 suno_lyrics 누락")
            elif suno_lyrics:
                # Suno Metatag 검증
                for tag in SUNO_REQUIRED_METATAGS:
                    if tag not in suno_lyrics:
                        add_issue("WARNING", "suno_lyrics", f"Suno 필수 Metatag 누락: {tag}")

    return issues


def validate_directory(source_dir: Path, step: str, section_filter: str | None, strict: bool) -> None:
    """디렉토리 내 Shot 파일 전체 검증."""
    if not source_dir.exists():
        print(f"[오류] 경로가 존재하지 않습니다: {source_dir}")
        sys.exit(1)

    pattern = "**/*.md" if not section_filter else f"{section_filter}/*.md"
    shot_files = sorted(source_dir.glob(pattern))

    if not shot_files:
        print(f"[경고] Shot 파일을 찾지 못했습니다: {source_dir}/{pattern}")
        return

    all_issues = []
    for shot_path in shot_files:
        if shot_path.name in ("ANCHOR.md", "index.md"):
            continue
        issues = validate_shot_file(shot_path, step, strict)
        all_issues.extend(issues)

    # 결과 출력
    errors = [i for i in all_issues if i["level"] == "ERROR"]
    warnings = [i for i in all_issues if i["level"] == "WARNING"]

    print(f"\n=== Shot Record 검증 결과 ===")
    print(f"대상 경로: {source_dir}")
    print(f"검증 단계: STEP {step}")
    print(f"총 파일 수: {len(shot_files)}개")
    print(f"오류: {len(errors)}건 | 경고: {len(warnings)}건\n")

    if errors:
        print("--- 오류 (ERROR) ---")
        for issue in errors:
            rel = Path(issue["file"]).relative_to(PROJECT_ROOT)
            print(f"  [{rel}] {issue['field']}: {issue['message']}")

    if warnings:
        print("\n--- 경고 (WARNING) ---")
        for issue in warnings:
            rel = Path(issue["file"]).relative_to(PROJECT_ROOT)
            print(f"  [{rel}] {issue['field']}: {issue['message']}")

    if not all_issues:
        print("모든 Shot Record 정상 [OK]")

    if errors or (strict and warnings):
        sys.exit(1)


def _read_manifest(project_root):
    """version_manifest.yaml에서 current_run과 섹션 정보를 읽는다."""
    manifest_path = project_root / "version_manifest.yaml"
    if not manifest_path.exists():
        return None, None
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    current_run = manifest.get("current_run")
    runs = manifest.get("runs", {})
    # dict 형식 (run001: {...}) 또는 list 형식 ([{...}]) 모두 지원
    if isinstance(runs, dict):
        run_data = runs.get(current_run, {})
        sections = run_data.get("sections", None)
    elif isinstance(runs, list) and runs:
        sections = runs[-1].get("sections", None)
    else:
        sections = None
    return current_run, sections


def main():
    parser = argparse.ArgumentParser(description="Shot Record YAML 필드 검증")
    parser.add_argument(
        "--source",
        choices=["04", "05", "06_audio", "06"],
        default="06",
        help="검증할 단계 (기본: 07 — shot_records)",
    )
    parser.add_argument("--section", default=None, help="특정 Section만 검증 (예: SECTION01)")
    parser.add_argument("--strict", action="store_true", help="경고도 오류로 처리 (exit code 1)")
    parser.add_argument("--project", default=None, help="프로젝트 코드 (매니페스트 모드)")
    parser.add_argument("--run", default=None, help="특정 run ID (매니페스트 모드)")
    args = parser.parse_args()

    step = args.source

    # 매니페스트 모드 vs 레거시 모드
    stage_map = {
        "04": "04_shot_composition",
        "05": "05_visual_direction",
        "06_audio": "06_audio_narration",
        "06": "07_shot_records",
    }

    if args.project:
        workspace_root = SCRIPT_DIR.parents[3]  # scripts/ → run-directing/ → skills/ → .claude/ → workspace root
        project_root = workspace_root / "projects" / args.project
        current_run, _ = _read_manifest(project_root)

        if current_run:
            run_id = args.run or current_run
            stage_dir = stage_map[step]
            source_dir = project_root / stage_dir / run_id
        else:
            # 프로젝트 지정이지만 매니페스트 없음 → 레거시
            source_dir = project_root / stage_map[step] / "v1"
    else:
        # 레거시 (PROJECT_ROOT 기준)
        source_map = {
            "04": PROJECT_ROOT / "04_shot_composition" / "v1",
            "05": PROJECT_ROOT / "05_visual_direction" / "v1",
            "06_audio": PROJECT_ROOT / "06_audio_narration" / "v1",
            "06": PROJECT_ROOT / "07_shot_records" / "v1",
        }
        source_dir = source_map[step]

    validate_directory(source_dir, step, args.section, args.strict)


if __name__ == "__main__":
    main()
