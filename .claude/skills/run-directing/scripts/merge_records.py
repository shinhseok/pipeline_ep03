"""
merge_records.py
================
04 base + 05 delta + 06 audio delta → shot_id 기준 매칭 → 완성 Shot Record + 07_ALL.txt

사용법:
  python scripts/merge_records.py --project CH01
  python scripts/merge_records.py --project CH01 --section SECTION01
  python scripts/merge_records.py --project CH01 --version v1

매니페스트 모드 (version_manifest.yaml 존재 시):
  python scripts/merge_records.py --project CH02              ← current_run 자동 해상도
  python scripts/merge_records.py --project CH01 --version v5 ← 레거시 강제 지정
"""

import re
import sys
import yaml
import argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).parent
WORKSPACE_ROOT = SCRIPT_DIR.parents[3]  # scripts/ → run-directing/ → skills/ → .claude/ → workspace root

SECTION_ORDER = [
    "TITLECARD",
    "SECTION00_HOOK",
    "SECTION01",
    "SECTION02",
    "SECTION03",
    "SECTION04_OUTRO",
]

# ── YAML 파싱 유틸 ──────────────────────────────────────────

def parse_yaml_fields(content: str) -> dict:
    """YAML 파일에서 모든 필드를 추출 (단순 라인 + 멀티라인 지원).

    ```yaml ... ``` 코드블록 감싸기와 --- 구분자를 자동 처리.
    """
    # 코드블록 안의 내용 추출
    yaml_match = re.search(r"```yaml\n(.*?)```", content, re.DOTALL)
    text = yaml_match.group(1) if yaml_match else content

    # 선행/후행 --- 제거
    text = re.sub(r"^---\s*\n", "", text)
    text = re.sub(r"\n---\s*$", "", text)

    fields = {}
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # 주석 라인 스킵
        if re.match(r"^\s*#", line):
            i += 1
            continue

        # 필드: 값 매칭 (브라켓 태그 지원: image_prompt[start], image_prompt[end] 등)
        m = re.match(r"^([a-zA-Z_]+(?:\[\w+\])?):\s*(.*)", line)
        if m:
            key = m.group(1)
            value = m.group(2).strip()

            if value == "|":
                # 멀티라인 값
                multiline_parts = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.startswith("  ") or next_line.strip() == "":
                        multiline_parts.append(next_line)
                        i += 1
                    else:
                        break
                # 후행 빈 줄 제거
                while multiline_parts and multiline_parts[-1].strip() == "":
                    multiline_parts.pop()
                fields[key] = "\n".join(multiline_parts)
            elif value == "" and i + 1 < len(lines) and re.match(r"^\s+-\s+", lines[i + 1]):
                # YAML 리스트 값 (ref_images:\n  - item1\n  - item2)
                list_parts = []
                i += 1
                while i < len(lines) and re.match(r"^\s+-\s+", lines[i]):
                    list_parts.append(lines[i])
                    i += 1
                fields[key] = "\n".join(list_parts)
            else:
                fields[key] = value
                i += 1
        else:
            i += 1

    return fields


def get_shot_id(fields: dict) -> int | None:
    """shot_id 정수 반환."""
    val = fields.get("shot_id")
    if val is None:
        return None
    try:
        return int(val)
    except ValueError:
        return None


# ── 파일 탐색 ──────────────────────────────────────────

def collect_shot_files(base_dir: Path, section_filter: str | None = None) -> dict[int, Path]:
    """디렉토리에서 shot 파일을 수집하여 {shot_id: path} 반환."""
    result = {}
    if not base_dir.exists():
        return result

    pattern = "**/*.md" if not section_filter else f"{section_filter}/*.md"
    for f in sorted(base_dir.glob(pattern)):
        if f.name in ("ANCHOR.md", "index.md", "anchor_research.md"):
            continue
        content = f.read_text(encoding="utf-8")
        fields = parse_yaml_fields(content)
        sid = get_shot_id(fields)
        if sid is not None:
            result[sid] = f
    return result


# ── 병합 로직 ──────────────────────────────────────────

# STEP 04 base 필드 (shot-composer가 작성)
BASE_FIELDS = [
    "shot_id", "section", "local_id", "duration_est", "emotion_tag",
    "emotion_nuance", "pose_archetype",
    "narration_span", "scene_type", "creative_intent", "line_of_action",
    "silhouette_note", "prop_refs", "costume_refs", "secondary_chars",
    "has_human", "asset_path", "status",
    # Hook 확장 필드 (STEP 04 — SECTION00_HOOK에만 존재)
    "hook_type", "hook_media_type", "video_duration", "video_engine",
]

# STEP 05 delta 필드
DELTA_06_FIELDS = ["image_prompt", "iv_prompt", "has_human", "asset_path", "video_prompt",
                   "ref_images", "thinking_level"]

# STEP 06 audio delta 필드 (sfx 제거 — Veo 3 iv_prompt [AUDIO]에서 영상에 직접 생성)
DELTA_07_FIELDS = ["scene_id", "el_narration", "bgm", "volume_mix"]

# STEP 06 Song Hook 전용 필드 (hook_type: song일 때만 존재)
DELTA_07_SONG_FIELDS = ["suno_style", "suno_lyrics", "suno_params"]


def merge_shot(base_fields: dict, delta06_fields: dict | None, delta07_fields: dict | None) -> dict:
    """04 base + 05 delta + 06 delta → 완성 Shot Record 딕셔너리."""
    merged = dict(base_fields)

    # 05 delta: has_human + asset_path 덮어쓰기, image_prompt + iv_prompt + video_prompt 추가
    if delta06_fields:
        if "has_human" in delta06_fields:
            merged["has_human"] = delta06_fields["has_human"]
        if "asset_path" in delta06_fields:
            merged["asset_path"] = delta06_fields["asset_path"]
        # image_prompt: 단일 또는 image_prompt[start]/[end] 브라켓 형식 처리
        if "image_prompt" in delta06_fields:
            merged["image_prompt"] = delta06_fields["image_prompt"]
        elif "image_prompt[start]" in delta06_fields:
            # Video Hook: image_prompt[start] + image_prompt[end] → 개별 필드로 병합
            merged["image_prompt[start]"] = delta06_fields["image_prompt[start]"]
            merged["image_prompt[end]"] = delta06_fields.get("image_prompt[end]", "~")
        if "iv_prompt" in delta06_fields:
            merged["iv_prompt"] = delta06_fields["iv_prompt"]
        if "video_prompt" in delta06_fields:
            merged["video_prompt"] = delta06_fields["video_prompt"]
        # v3 필드: ref_images, thinking_level (pass-through)
        if "ref_images" in delta06_fields:
            merged["ref_images"] = delta06_fields["ref_images"]
        if "thinking_level" in delta06_fields:
            merged["thinking_level"] = delta06_fields["thinking_level"]
        # video_start_image, video_end_image (Video Hook 전용)
        if "video_start_image" in delta06_fields:
            merged["video_start_image"] = delta06_fields["video_start_image"]
        if "video_end_image" in delta06_fields:
            merged["video_end_image"] = delta06_fields["video_end_image"]

    # 06 delta: scene_id, el_narration, bgm, volume_mix 추가
    if delta07_fields:
        for key in DELTA_07_FIELDS:
            if key in delta07_fields:
                merged[key] = delta07_fields[key]
        # Song Hook 필드 (hook_type: song일 때만 존재)
        for key in DELTA_07_SONG_FIELDS:
            if key in delta07_fields:
                merged[key] = delta07_fields[key]

    # 모든 필수 필드가 있으면 status: done
    # Song Hook Shot: el_narration 대신 suno_style + suno_lyrics 필요
    is_song_hook = merged.get("hook_type") == "song"
    is_video_hook = merged.get("hook_media_type") == "video"
    if is_song_hook:
        # Video Hook: image_prompt[start] 대체 가능
        fp_key = "image_prompt[start]" if is_video_hook and "image_prompt[start]" in merged else "image_prompt"
        required = [fp_key, "iv_prompt", "suno_style", "suno_lyrics"]
    else:
        required = ["image_prompt", "iv_prompt", "el_narration", "bgm", "volume_mix"]
    all_present = all(
        merged.get(k) and merged[k] not in ("~", "null", "None", "")
        for k in required
    )
    if all_present:
        merged["status"] = "done"

    return merged


# ── YAML 출력 ──────────────────────────────────────────

def format_yaml_value(key: str, value: str) -> str:
    """YAML 필드 → 문자열 출력."""
    if value is None or value in ("~", "null"):
        return f"{key}: ~"

    # 멀티라인 값 (들여쓰기로 시작하거나 개행 포함)
    if "\n" in value or value.startswith("  "):
        return f"{key}: |\n{value}"

    return f"{key}: {value}"


def render_merged_shot(merged: dict, date_str: str, voice_id: str = "") -> str:
    """병합된 Shot Record를 파일 전체 내용으로 렌더링."""
    shot_id = merged.get("shot_id", "00")
    section = merged.get("section", "")
    section_bgm_map = {
        "TITLECARD": "ambient solo piano | BPM 78 | Low-Mid",
        "SECTION00_HOOK": "ambient solo piano | BPM 78 | Low-Mid",
        "SECTION01": "ambient strings | BPM 72 | Low",
        "SECTION02": "acoustic folk piano | BPM 82 | Mid",
        "SECTION03": "post-rock strings | BPM 90 | Mid-High",
        "SECTION04_OUTRO": "ambient pad | BPM 65 | Low",
    }
    section_bgm = section_bgm_map.get(section, "")

    # 헤더
    header = f"""# shot{int(shot_id):02d}.md
SECTION: {section}
SHOT_ID: {shot_id}
INPUT_REF: 05 + 06 + 07 merge
MODEL: merge_records.py
ELEVENLABS_MODEL: Eleven v3
VOICE_ID: {voice_id}
SECTION_BGM: {section_bgm}
CREATED: {date_str}

---

```yaml
---"""

    # YAML 필드
    yaml_lines = []

    # 기본 필드
    for key in ["shot_id", "section", "local_id", "duration_est", "emotion_tag",
                 "emotion_nuance", "pose_archetype"]:
        val = merged.get(key)
        if key in ("emotion_nuance", "pose_archetype") and not val:
            continue  # 선택 필드 — 없으면 출력 생략
        yaml_lines.append(format_yaml_value(key, val if val else "~"))

    yaml_lines.append("")
    yaml_lines.append("# [STEP 04 shot-composer]")

    for key in ["narration_span", "scene_type", "creative_intent", "line_of_action",
                 "silhouette_note", "prop_refs", "costume_refs", "secondary_chars", "has_human"]:
        yaml_lines.append(format_yaml_value(key, merged.get(key, "~")))

    # Hook 확장 필드 (SECTION00_HOOK에만 존재 — 있을 때만 출력)
    hook_type = merged.get("hook_type")
    hook_media_type = merged.get("hook_media_type")
    if hook_type or hook_media_type:
        yaml_lines.append("")
        yaml_lines.append("# [Hook 확장 필드]")
        if hook_type:
            yaml_lines.append(format_yaml_value("hook_type", hook_type))
        if hook_media_type:
            yaml_lines.append(format_yaml_value("hook_media_type", hook_media_type))
        if merged.get("video_duration"):
            yaml_lines.append(format_yaml_value("video_duration", merged["video_duration"]))
        if merged.get("video_engine"):
            yaml_lines.append(format_yaml_value("video_engine", merged["video_engine"]))

    yaml_lines.append("")
    yaml_lines.append("# [STEP 05 visual-director]")
    # v3 필드: ref_images, thinking_level (있을 때만 출력)
    if merged.get("ref_images"):
        ref_val = merged["ref_images"]
        # 멀티라인 YAML 리스트 출력
        if "\n" in ref_val or ref_val.strip().startswith("-"):
            yaml_lines.append(f"ref_images:\n{ref_val}")
        else:
            yaml_lines.append(format_yaml_value("ref_images", ref_val))
    if merged.get("thinking_level"):
        yaml_lines.append(format_yaml_value("thinking_level", merged["thinking_level"]))
    # Video Hook: image_prompt[start] + image_prompt[end] 또는 단일 image_prompt
    if "image_prompt[start]" in merged:
        yaml_lines.append(format_yaml_value("image_prompt[start]", merged["image_prompt[start]"]))
        yaml_lines.append(format_yaml_value("image_prompt[end]", merged.get("image_prompt[end]", "~")))
    else:
        yaml_lines.append(format_yaml_value("image_prompt", merged.get("image_prompt", "~")))
    yaml_lines.append(format_yaml_value("iv_prompt", merged.get("iv_prompt", "~")))
    if merged.get("video_prompt"):
        yaml_lines.append(format_yaml_value("video_prompt", merged["video_prompt"]))
    if merged.get("video_start_image"):
        yaml_lines.append(format_yaml_value("video_start_image", merged["video_start_image"]))
    if merged.get("video_end_image"):
        yaml_lines.append(format_yaml_value("video_end_image", merged["video_end_image"]))

    yaml_lines.append("")
    yaml_lines.append("# [STEP 06 audio-narration-builder]")
    for key in DELTA_07_FIELDS:
        yaml_lines.append(format_yaml_value(key, merged.get(key, "~")))
    yaml_lines.append("# sfx: Veo 3 iv_prompt [AUDIO]에서 영상에 직접 생성 (별도 필드 없음)")

    # Song Hook Suno 필드 (hook_type: song일 때만)
    if hook_type == "song":
        yaml_lines.append("")
        yaml_lines.append("# [Song Hook — Suno]")
        for key in DELTA_07_SONG_FIELDS:
            yaml_lines.append(format_yaml_value(key, merged.get(key, "~")))

    yaml_lines.append("")
    yaml_lines.append(format_yaml_value("asset_path", merged.get("asset_path", "~")))
    yaml_lines.append(format_yaml_value("status", merged.get("status", "⏳")))

    yaml_lines.append("---")

    yaml_body = "\n".join(yaml_lines)

    return f"{header}\n{yaml_body}\n```\n"


# ── 07_ALL.txt 생성 ──────────────────────────────────────────

def generate_07_all(merged_records: list[dict], voice_id: str = "") -> str:
    """07_ALL.txt 생성: el_narration 전체 연결."""
    header = f"""// ElevenLabs 전체 나레이션 통합본 (입력 전 // 주석 줄 삭제)
// 모델: Eleven v3 | 언어: 한국어
// 보이스: {voice_id}
// Stability: 0.5 | Style: 0.4
// 총 Section: HOOK + SECTION01 + SECTION02 + SECTION03 + OUTRO"""

    sections_content = {}
    for rec in merged_records:
        section = rec.get("section", "")
        # TITLECARD 제외
        if section == "TITLECARD":
            continue

        # Song Hook Shot은 el_narration 대신 Suno 음원 사용 — 07_ALL.txt에서 제외
        if rec.get("hook_type") == "song":
            continue

        el_narration = rec.get("el_narration", "")
        # (없음) 제외
        if not el_narration or el_narration.strip() in ("~", "(없음)", "null", "(Song Hook", ""):
            continue

        # 멀티라인 값에서 들여쓰기 제거
        narration_clean = "\n".join(
            line[2:] if line.startswith("  ") else line
            for line in el_narration.split("\n")
        ).strip()

        if section not in sections_content:
            sections_content[section] = []
        sections_content[section].append({
            "scene_id": rec.get("scene_id", "0"),
            "text": narration_clean,
        })

    lines = [header, ""]

    for section in SECTION_ORDER:
        if section == "TITLECARD":
            continue
        if section not in sections_content:
            continue

        lines.append(f"// ─── {section} ───────────────────────────")

        entries = sections_content[section]
        prev_scene_id = None
        for entry in entries:
            scene_id = entry["scene_id"]
            if prev_scene_id is not None and scene_id != prev_scene_id:
                lines.append("")  # scene 경계에 빈 줄
            lines.append(entry["text"])
            prev_scene_id = scene_id

        lines.append("")

    return "\n".join(lines)


# ── 메인 ──────────────────────────────────────────

def _read_manifest(project_root):
    """version_manifest.yaml에서 current_run, base_run, 섹션 정보를 읽는다.

    base_run: STEP 04 base 파일을 다른 run에서 가져올 때 지정.
    생략 시 current_run과 동일.
    """
    manifest_path = project_root / "version_manifest.yaml"
    if not manifest_path.exists():
        return None, None, None
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    current_run = manifest.get("current_run")
    runs = manifest.get("runs", {})
    if isinstance(runs, dict):
        run_data = runs.get(current_run, {})
        sections = run_data.get("sections", None)
        base_run = run_data.get("base_run", current_run)
    elif isinstance(runs, list) and runs:
        last_run = runs[-1]
        sections = last_run.get("sections", None)
        base_run = last_run.get("base_run", current_run)
    else:
        sections = None
        base_run = current_run
    return current_run, base_run, sections


def _resolve_path(project_root, stage, run_id, section):
    """stage/run_id/section 경로를 반환한다."""
    return project_root / stage / run_id / section


def main():
    parser = argparse.ArgumentParser(description="04 base + 05 delta + 06 delta → 완성 Shot Record 병합")
    parser.add_argument("--project", required=True, help="프로젝트 코드 (예: CH01)")
    parser.add_argument("--section", default=None, help="특정 Section만 병합 (예: SECTION01)")
    parser.add_argument("--version", default=None, help="버전 (레거시: v1 등. 생략 시 매니페스트 자동)")
    parser.add_argument("--dry-run", action="store_true", help="파일 쓰기 없이 병합 결과만 출력")
    args = parser.parse_args()

    project_root = WORKSPACE_ROOT / "projects" / args.project
    if not project_root.exists():
        print(f"[ERROR] 프로젝트 폴더를 찾을 수 없습니다: {project_root}")
        sys.exit(1)

    # 매니페스트 모드 vs 레거시 모드 결정
    if args.version:
        version = args.version
        base_run = args.version
        run_sections = None
        use_manifest = False
    else:
        version, base_run, run_sections = _read_manifest(project_root)
        use_manifest = version is not None
        if not use_manifest:
            print("[ERROR] --version 미지정 + version_manifest.yaml 없음. --version v1 등으로 지정하세요.")
            sys.exit(1)

    if use_manifest:
        # 매니페스트 모드: Section별로 resolve
        current_run = version
        dir_output = project_root / "07_shot_records" / current_run
        target_sections = [args.section] if args.section else (run_sections if run_sections else SECTION_ORDER)

        if base_run != current_run:
            print(f"\n🔄 merge_records.py 시작 (Project: {args.project}, Run: {current_run}, 04 base: {base_run}, 매니페스트 모드)")
        else:
            print(f"\n🔄 merge_records.py 시작 (Project: {args.project}, Run: {current_run}, 매니페스트 모드)")

        base_files = {}
        delta06_files = {}
        delta07_files = {}

        for section in target_sections:
            dir_05_sec = _resolve_path(project_root, "04_shot_composition", base_run, section)
            dir_06_sec = _resolve_path(project_root, "05_visual_direction", current_run, section)
            dir_07_sec = _resolve_path(project_root, "06_audio_narration", current_run, section)

            if dir_05_sec and dir_05_sec.exists():
                base_files.update(collect_shot_files(dir_05_sec))
            if dir_06_sec and dir_06_sec.exists():
                delta06_files.update(collect_shot_files(dir_06_sec))
            if dir_07_sec and dir_07_sec.exists():
                delta07_files.update(collect_shot_files(dir_07_sec))
    else:
        # 레거시 모드
        dir_05 = project_root / "04_shot_composition" / version
        dir_06 = project_root / "05_visual_direction" / version
        dir_07_audio = project_root / "06_audio_narration" / version
        dir_output = project_root / "07_shot_records" / version

        if not dir_05.exists():
            print(f"[ERROR] 04_shot_composition/{version} 폴더가 없습니다: {dir_05}")
            sys.exit(1)

        print(f"\n🔄 merge_records.py 시작 (Project: {args.project}, Version: {version})")
        base_files = collect_shot_files(dir_05, args.section)
        delta06_files = collect_shot_files(dir_06, args.section)
        delta07_files = collect_shot_files(dir_07_audio, args.section)

    print(f"   04 base: {len(base_files)}개")
    print(f"   05 delta: {len(delta06_files)}개")
    print(f"   06 audio delta: {len(delta07_files)}개")

    if not base_files:
        print("[ERROR] 04 base 파일이 없습니다.")
        sys.exit(1)

    # 정합성 경고: base ≠ delta 수 불일치
    _merge_warnings = []
    if delta06_files and len(base_files) != len(delta06_files):
        msg = f"04 base({len(base_files)}개) ≠ 05 delta({len(delta06_files)}개) — base_run 설정 확인 필요"
        print(f"   ⚠️ {msg}")
        _merge_warnings.append(msg)
    if delta07_files and len(base_files) != len(delta07_files):
        msg = f"04 base({len(base_files)}개) ≠ 06 delta({len(delta07_files)}개) — 누락 Shot 확인 필요"
        print(f"   ⚠️ {msg}")
        _merge_warnings.append(msg)

    # _meta.md에서 VOICE_ID 추출
    voice_id = ""
    meta_path = project_root / "_meta.md"
    if meta_path.exists():
        meta_content = meta_path.read_text(encoding="utf-8")
        m = re.search(r"VOICE_ID\s*\|\s*(\S+)", meta_content)
        if m:
            voice_id = m.group(1)

    # 날짜
    from datetime import date
    date_str = date.today().isoformat()

    # 병합
    all_merged = []
    for shot_id in sorted(base_files.keys()):
        base_content = base_files[shot_id].read_text(encoding="utf-8")
        base = parse_yaml_fields(base_content)

        d06 = None
        if shot_id in delta06_files:
            d06_content = delta06_files[shot_id].read_text(encoding="utf-8")
            d06 = parse_yaml_fields(d06_content)

        d07 = None
        if shot_id in delta07_files:
            d07_content = delta07_files[shot_id].read_text(encoding="utf-8")
            d07 = parse_yaml_fields(d07_content)

        merged = merge_shot(base, d06, d07)
        all_merged.append(merged)

        # 출력 파일 저장
        section = merged.get("section", "UNKNOWN")
        out_dir = dir_output / section
        out_path = out_dir / f"shot{int(shot_id):02d}.md"

        if not args.dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)
            rendered = render_merged_shot(merged, date_str, voice_id)
            out_path.write_text(rendered, encoding="utf-8")

    if args.dry_run:
        print(f"\n   [DRY-RUN] 병합 대상: {len(all_merged)}개 Shot Record → {dir_output}")
    else:
        print(f"\n   ✅ 병합 완료: {len(all_merged)}개 Shot Record → {dir_output}")

    # 07_ALL.txt 생성
    all_txt = generate_07_all(all_merged, voice_id)
    all_path = dir_output / "07_ALL.txt"
    if not args.dry_run:
        all_path.parent.mkdir(parents=True, exist_ok=True)
        all_path.write_text(all_txt, encoding="utf-8")
        print(f"   ✅ 07_ALL.txt 생성: {all_path}")
    else:
        print(f"   [DRY-RUN] 07_ALL.txt 생성 예정: {all_path}")

    # 통계
    done_count = sum(1 for m in all_merged if m.get("status") == "done")
    pending_count = len(all_merged) - done_count
    print(f"\n   상태: done={done_count} / pending={pending_count}")

    # 피드백 파일 저장 (경고가 있을 때만)
    if _merge_warnings and not args.dry_run:
        from datetime import datetime
        run_id = version if use_manifest else "v1"
        feedback_dir = project_root / "feedback" / run_id
        feedback_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%dT%H%M")
        feedback_path = feedback_dir / f"merge-records_{ts}.md"
        lines = [
            "---",
            "from: merge-records",
            "to: system",
            f"run_id: {run_id}",
            f"created: {datetime.now().isoformat()}",
            f"warning_count: {len(_merge_warnings)}",
            "",
            "items:",
        ]
        for i, w in enumerate(_merge_warnings, 1):
            lines.append(f"  - id: MR-{i:03d}")
            lines.append(f"    severity: FLAG")
            lines.append(f"    type: COUNT_MISMATCH")
            lines.append(f"    detail: |")
            lines.append(f"      {w}")
        lines.append("---")
        feedback_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"\n📋 피드백 저장: {feedback_path.relative_to(project_root)}")



if __name__ == "__main__":
    main()
