#!/usr/bin/env python3
"""check_status.py — Pipeline progress dashboard.

Usage:
    python check_status.py --project CH02
    python check_status.py              # lists all projects
"""

import argparse
import io
import re
import sys
from pathlib import Path

# Windows cp949 encoding fix
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    import yaml
except ImportError:
    yaml = None

WORKSPACE = Path(__file__).resolve().parents[4]
PROJECTS_DIR = WORKSPACE / "projects"

STEPS = [
    ("01", "자료수집", "01_research"),
    ("02", "분석·기획", "02_planning"),
    ("03", "대본 초안", "03_script_final"),
    ("03", "대본 각색", "03_script_final"),
    ("04", "Shot 구성", "04_shot_composition"),
    ("05", "비주얼 디렉팅", "05_visual_direction"),
    ("06", "Shot Record Build", "07_shot_records"),
    ("09", "에셋 생성", "09_assets"),
    ("10", "편집", None),
]

MODEL_TABLE = """| Agent | 모델 | 적용 단계 |
|-------|------|-----------|
| content-planner | sonnet | STEP 02 |
| script-director | opus | STEP 03 |
| shot-composer | opus | STEP 04 |
| visual-director | opus | STEP 05 |
| audio-director | haiku | STEP 06 |"""


def list_projects():
    if not PROJECTS_DIR.exists():
        sys.exit("ERROR: projects/ directory not found.")
    dirs = sorted(d.name for d in PROJECTS_DIR.iterdir() if d.is_dir() and (d / "_meta.md").exists())
    if not dirs:
        sys.exit("No projects found with _meta.md.")
    print("📂 Available projects:\n")
    for d in dirs:
        meta = parse_meta(d)
        topic = meta.get("TOPIC", "—")
        print(f"  {d:12s}  {topic}")
    print(f"\nUsage: python check_status.py --project {dirs[0]}")


def parse_meta(project: str) -> dict:
    meta_path = PROJECTS_DIR / project / "_meta.md"
    if not meta_path.exists():
        return {}
    text = meta_path.read_text(encoding="utf-8")
    result = {}
    for key in ["PROJECT_CODE", "TOPIC", "LAST_UPDATED", "VOICE_ID"]:
        m = re.search(rf"{key}:\s*(.+)", text)
        if m:
            result[key] = m.group(1).strip()

    # Parse status table
    status_map = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("|") and "STEP" not in line and "---" not in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 5:
                step_num = parts[1].strip() if len(parts) > 1 else ""
                status_val = parts[4].strip() if len(parts) > 4 else ""
                if step_num and step_num.isdigit():
                    status_map[step_num.zfill(2)] = status_val
    result["status_map"] = status_map
    return result


def detect_files(project: str, folder: str) -> list[str]:
    d = PROJECTS_DIR / project / folder
    if not d.exists():
        return []
    files = []
    for f in sorted(d.rglob("*")):
        if f.is_file() and not f.name.startswith("."):
            files.append(str(f.relative_to(PROJECTS_DIR / project)))
    return files


def get_version_info(project: str) -> str:
    manifest = PROJECTS_DIR / project / "version_manifest.yaml"
    if not manifest.exists():
        return "매니페스트 없음 (레거시 v1/ 모드)"
    if yaml is None:
        return "매니페스트 존재 (PyYAML 없어 파싱 불가)"
    with open(manifest, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    current = data.get("current_run", "?")
    total = len(data.get("runs", []))
    return f"current_run: {current} ({total}개 run)"


def show_status(project: str):
    meta = parse_meta(project)
    topic = meta.get("TOPIC", "—")
    updated = meta.get("LAST_UPDATED", "—")
    voice = meta.get("VOICE_ID", "미정")
    status_map = meta.get("status_map", {})

    print(f"\n## 📋 PROJECT STATUS: {project}")
    print(f"TOPIC: {topic}")
    print(f"LAST UPDATED: {updated}")
    print(f"VOICE_ID: {voice}")
    print(f"VERSION: {get_version_info(project)}")

    print(f"\n## 🤖 모델 배정")
    print(MODEL_TABLE)

    print(f"\n## 📊 파이프라인 현황")
    print(f"| STEP | 작업명 | 파일 수 | 상태 |")
    print(f"|------|--------|---------|------|")

    blocked_items = []
    for step_num, step_name, folder in STEPS:
        status = status_map.get(step_num, "⏳ PENDING")
        if folder:
            files = detect_files(project, folder)
            file_count = f"{len(files)}개" if files else "—"
        else:
            file_count = "—"
        print(f"| {step_num} | {step_name} | {file_count} | {status} |")
        if "BLOCKED" in status:
            blocked_items.append((step_num, step_name))

    if blocked_items:
        print(f"\n## ⚠️ BLOCKED 항목")
        for num, name in blocked_items:
            print(f"  - STEP {num} ({name}): 선행 단계 파일 확인 필요")

    # Next action suggestion
    print(f"\n## 🔜 다음 액션")
    for step_num, step_name, folder in STEPS:
        status = status_map.get(step_num, "")
        if "DONE" not in status and "✅" not in status:
            suggestions = {
                "01": "/run-planning (자료 수집부터 시작)",
                "02": "/run-planning (기획 실행)",
                "03": "/run-directing (대본 작성)",
                "03": "/run-directing (대본 각색)",
                "04": "/run-directing (Shot 구성)",
                "05": "/run-directing (비주얼 디렉팅)",
                "06": "/run-directing (Shot Record 빌드)",
                "09": "/generate-images (에셋 생성)",
                "10": "CapCut 편집 후 업로드",
            }
            print(f"  → {suggestions.get(step_num, f'STEP {step_num} 진행')}")
            break
    else:
        print("  🎬 모든 단계 완료. CapCut 편집 후 업로드하세요.")


def main():
    parser = argparse.ArgumentParser(description="Pipeline status dashboard")
    parser.add_argument("--project", default=None, help="PROJECT_CODE")
    args = parser.parse_args()

    if not args.project:
        list_projects()
    else:
        show_status(args.project)


if __name__ == "__main__":
    main()
