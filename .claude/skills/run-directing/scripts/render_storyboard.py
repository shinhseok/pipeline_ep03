"""
render_storyboard.py
====================
07_shot_records/ (병합 완성본) → 08_storyboard/ 마크다운 렌더링.
LLM 호출 없이 코드로 스토리보드를 생성한다.

사용법:
  python scripts/render_storyboard.py --project CH01
  python scripts/render_storyboard.py --project CH01 --version v1

매니페스트 모드 (version_manifest.yaml 존재 시):
  python scripts/render_storyboard.py --project CH02              ← current_run 자동 해상도
  python scripts/render_storyboard.py --project CH01 --version v5 ← 레거시 강제 지정
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


# ── YAML 파싱 ──────────────────────────────────────────

def parse_yaml_fields(content: str) -> dict:
    """YAML 파일에서 모든 필드를 추출."""
    yaml_match = re.search(r"```yaml\n(.*?)```", content, re.DOTALL)
    text = yaml_match.group(1) if yaml_match else content

    text = re.sub(r"^---\s*\n", "", text)
    text = re.sub(r"\n---\s*$", "", text)

    fields = {}
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^\s*#", line):
            i += 1
            continue

        m = re.match(r"^([a-zA-Z_]+):\s*(.*)", line)
        if m:
            key = m.group(1)
            value = m.group(2).strip()
            if value == "|":
                multiline_parts = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.startswith("  ") or next_line.strip() == "":
                        multiline_parts.append(next_line)
                        i += 1
                    else:
                        break
                while multiline_parts and multiline_parts[-1].strip() == "":
                    multiline_parts.pop()
                fields[key] = "\n".join(multiline_parts)
            else:
                fields[key] = value
                i += 1
        else:
            i += 1

    return fields


def dedent_multiline(value: str) -> str:
    """멀티라인 값의 2-space 들여쓰기 제거."""
    return "\n".join(
        line[2:] if line.startswith("  ") else line
        for line in value.split("\n")
    ).strip()


# ── 스토리보드 렌더링 ──────────────────────────────────────────

def extract_creative_intent_props_line(creative_intent: str) -> str:
    """creative_intent에서 [소품] 라인을 발췌. 없으면 첫 줄 반환."""
    clean = dedent_multiline(creative_intent)
    for line in clean.split("\n"):
        if line.strip().startswith("[소품]"):
            return line.strip()
    # [소품] 없으면 첫 줄
    first = clean.split("\n")[0].strip()
    return first if first else "(시각 요약 없음)"


def extract_bgm_short(bgm: str) -> str:
    """bgm 필드에서 EL: 이전까지만 발췌."""
    bgm = bgm.strip().strip('"')
    el_idx = bgm.find("| EL:")
    if el_idx > 0:
        return bgm[:el_idx].strip()
    return bgm


def extract_sfx_short(sfx: str) -> str:
    """sfx 필드에서 EL: 이전까지만 발췌. None이면 None 반환."""
    sfx = sfx.strip().strip('"')
    if sfx.lower() in ("none", "~", "null", ""):
        return "None"
    el_idx = sfx.find("| EL:")
    if el_idx > 0:
        return sfx[:el_idx].strip()
    return sfx


def render_shot(fields: dict, version: str) -> str:
    """단일 Shot Record → 스토리보드 마크다운."""
    shot_id = fields.get("shot_id", "0")
    section = fields.get("section", "")
    local_id = fields.get("local_id", "0")
    emotion_tag = fields.get("emotion_tag", "")
    duration_est = fields.get("duration_est", "")

    # el_narration
    el_narration = fields.get("el_narration", "")
    if el_narration and el_narration not in ("~", "null"):
        narration_text = dedent_multiline(el_narration)
    else:
        narration_text = "(없음)"

    # 시각 요약
    creative_intent = fields.get("creative_intent", "")
    line_of_action = fields.get("line_of_action", "")
    if creative_intent and creative_intent not in ("~", "null"):
        visual_summary = extract_creative_intent_props_line(creative_intent)
        if line_of_action and line_of_action not in ("~", "null"):
            visual_summary += f" ({line_of_action})"
    else:
        visual_summary = "(시각 요약 없음)"

    flow_ref = f"05_visual_direction/{version}/{section}/shot{int(shot_id):02d}.md"

    # 오디오
    bgm = fields.get("bgm", "")
    volume_mix = fields.get("volume_mix", "")

    bgm_short = extract_bgm_short(bgm) if bgm and bgm not in ("~", "null") else ""
    vol_text = volume_mix.strip().strip('"') if volume_mix and volume_mix not in ("~", "null") else ""

    asset_path = fields.get("asset_path", "")
    status = fields.get("status", "⏳")

    # iv_prompt
    iv_prompt = fields.get("iv_prompt", "")
    if iv_prompt and iv_prompt not in ("~", "null"):
        iv_prompt_text = dedent_multiline(iv_prompt)
    else:
        iv_prompt_text = "(없음)"

    try:
        local_id_fmt = f"{int(local_id):02d}"
    except (ValueError, TypeError):
        local_id_fmt = str(local_id)

    return f"""### Shot {shot_id} | {section} Shot {local_id_fmt} | [{emotion_tag}] | {duration_est}

나레이션
{narration_text}

시각 요약
{visual_summary}
Flow 참조: {flow_ref}

I2V
{iv_prompt_text}

오디오
BGM: {bgm_short}
볼륨: {vol_text}
※ SFX+Ambient: Veo 3 영상에 내장

에셋: {asset_path} | {status}"""


def render_shot_file(fields: dict, version: str, date_str: str) -> str:
    """전체 Shot 파일 내용."""
    shot_id = fields.get("shot_id", "0")
    section = fields.get("section", "")

    header = f"""# shot{int(shot_id):02d}.md
SECTION: {section}
SHOT_ID: {shot_id}
MODEL: render_storyboard.py
CREATED: {date_str}

---

"""
    return header + render_shot(fields, version)


# ── 인덱스 생성 ──────────────────────────────────────────

def render_index(section_stats: dict, all_records: list[dict],
                 version: str, date_str: str, project_code: str) -> str:
    """index.md 생성."""
    total_shots = sum(s["count"] for s in section_stats.values())
    total_duration = sum(s["duration"] for s in section_stats.values())
    avg_duration = total_duration / total_shots if total_shots > 0 else 0

    # 섹션 테이블
    section_rows = []
    for sec in SECTION_ORDER:
        if sec not in section_stats:
            continue
        stats = section_stats[sec]
        shot_range = f"Shot {stats['min_id']}~{stats['max_id']}" if stats["min_id"] != stats["max_id"] else f"Shot {stats['min_id']}"
        section_rows.append(
            f"| {sec} | {shot_range} | {stats['count']}개 | {stats['duration']}s |"
        )
    section_rows.append(f"| **합계** | Shot {section_stats[SECTION_ORDER[0]]['min_id'] if SECTION_ORDER[0] in section_stats else 0}~{max(s['max_id'] for s in section_stats.values())} | **{total_shots}개** | **{total_duration}s ({total_duration/60:.1f}분)** |")

    section_table = "\n".join(section_rows)

    # 매핑 테이블
    mapping_rows = []
    for rec in all_records:
        sid = rec.get("shot_id", "0")
        sec = rec.get("section", "")
        lid = rec.get("local_id", "0")
        try:
            lid_fmt = f"{int(lid):02d}"
        except (ValueError, TypeError):
            lid_fmt = str(lid)
        mapping_rows.append(
            f"| {sid} | {sec} | {lid_fmt} | `08_storyboard/{version}/{sec}/shot{int(sid):02d}.md` |"
        )
    mapping_table = "\n".join(mapping_rows)

    return f"""# index.md
TOPIC: {project_code}
TOTAL_SECTIONS: {len(section_stats)}
TOTAL_SHOTS: {total_shots}
ESTIMATED_DURATION: {total_duration}s
AVG_SHOT_DURATION: {avg_duration:.1f}s
MODEL: render_storyboard.py
CREATED: {date_str}

---

## 스토리보드 인덱스 — {project_code} {version}

| 섹션 | Shot 범위 | Shot 수 | 예상 시간 |
|------|----------|---------|----------|
{section_table}

---

## 전역 Shot 매핑 테이블

| Shot ID | 섹션 | Local ID | 파일 |
|---------|------|----------|------|
{mapping_table}

---

## 검증 결과
- [x] 전체 Shot 수: {total_shots}개
- [x] AVG_SHOT_DURATION: {avg_duration:.1f}s
"""


# ── 메인 ──────────────────────────────────────────

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
        sections = run_data.get("sections", None)  # None = 전체
    elif isinstance(runs, list) and runs:
        last_run = runs[-1]
        sections = last_run.get("sections", None)
    else:
        sections = None
    return current_run, sections


def main():
    parser = argparse.ArgumentParser(description="07_shot_records → 08_storyboard 렌더링")
    parser.add_argument("--project", required=True, help="프로젝트 코드 (예: CH01)")
    parser.add_argument("--version", default=None, help="버전 (레거시: v1 등. 생략 시 매니페스트 자동)")
    parser.add_argument("--dry-run", action="store_true", help="파일 쓰기 없이 결과만 출력")
    args = parser.parse_args()

    project_root = WORKSPACE_ROOT / "projects" / args.project
    if not project_root.exists():
        print(f"[ERROR] 프로젝트 폴더를 찾을 수 없습니다: {project_root}")
        sys.exit(1)

    # 매니페스트 모드 vs 레거시 모드 결정
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

    dir_input = project_root / "07_shot_records" / version
    dir_output = project_root / "08_storyboard" / version

    if not dir_input.exists():
        print(f"[ERROR] 07_shot_records/{version} 폴더가 없습니다: {dir_input}")
        sys.exit(1)

    from datetime import date
    date_str = date.today().isoformat()

    print(f"\n🎬 render_storyboard.py 시작 (Project: {args.project}, Version: {version})")

    # Shot 파일 수집 (Section별 정렬)
    all_records = []
    section_stats = {}

    for section in SECTION_ORDER:
        section_dir = dir_input / section
        if not section_dir.exists():
            continue

        shot_files = sorted(section_dir.glob("shot*.md"))
        if not shot_files:
            continue

        section_records = []
        for f in shot_files:
            content = f.read_text(encoding="utf-8")
            fields = parse_yaml_fields(content)
            section_records.append(fields)

        # shot_id 기준 정렬
        section_records.sort(key=lambda r: int(r.get("shot_id", 0)))

        # 섹션 통계
        durations = []
        shot_ids = []
        for rec in section_records:
            dur_str = rec.get("duration_est", "0s").rstrip("s")
            try:
                durations.append(float(dur_str))
            except ValueError:
                durations.append(0)
            try:
                shot_ids.append(int(rec.get("shot_id", 0)))
            except ValueError:
                shot_ids.append(0)

        section_stats[section] = {
            "count": len(section_records),
            "duration": int(sum(durations)),
            "min_id": min(shot_ids) if shot_ids else 0,
            "max_id": max(shot_ids) if shot_ids else 0,
        }

        # 스토리보드 파일 생성
        if not args.dry_run:
            out_section_dir = dir_output / section
            out_section_dir.mkdir(parents=True, exist_ok=True)

            for rec in section_records:
                shot_id = int(rec.get("shot_id", 0))
                out_path = out_section_dir / f"shot{shot_id:02d}.md"
                rendered = render_shot_file(rec, version, date_str)
                out_path.write_text(rendered, encoding="utf-8")

        all_records.extend(section_records)
        label = "[DRY-RUN]" if args.dry_run else "✅"
        print(f"   {label} {section}: {len(section_records)}개 Shot")

    if not all_records:
        print("[ERROR] Shot Record 파일이 없습니다.")
        sys.exit(1)

    # 인덱스 생성
    index_content = render_index(section_stats, all_records, version, date_str, args.project)
    if not args.dry_run:
        index_path = dir_output / "index.md"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(index_content, encoding="utf-8")
    label = "[DRY-RUN]" if args.dry_run else "✅"
    print(f"   {label} index.md 생성")

    total = len(all_records)
    total_dur = sum(s["duration"] for s in section_stats.values())
    print(f"\n   완료: {total}개 Shot / {total_dur}s ({total_dur/60:.1f}분)")



if __name__ == "__main__":
    main()
