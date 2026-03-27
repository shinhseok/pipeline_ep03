"""
generate_qa_sheet.py
====================
Shot Record에서 QA 체크시트를 자동 생성합니다.

실행:
  python scripts/generate_qa_sheet.py --project CH02E1
  python scripts/generate_qa_sheet.py --project CH02E1 --section SECTION01
  python scripts/generate_qa_sheet.py --project CH02E1 --round 2   ← 재검수 라운드

출력:
  projects/{PROJECT_CODE}/09_assets/images/{RUN_ID}/QA_SHEET.md
"""

import os
import re
import sys
import yaml
import argparse
from pathlib import Path
from datetime import date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE = Path(__file__).resolve().parents[4]  # AML_PL1/
SECTION_ORDER = [
    "TITLECARD", "SECTION00_HOOK", "SECTION01",
    "SECTION02", "SECTION03", "SECTION04_OUTRO",
]

# QA 체크 항목 정의
# (id, 한국어 라벨, 영문 카테고리, 수정 대상 파일)
QA_ITEMS = [
    ("A", "연출 의도", "INTENT", "05 creative_intent / 06 image_prompt"),
    ("B", "스타일 일관성", "STYLE", "visual-director art_style"),
    ("C", "배경색", "BG", "visual-director background"),
    ("D", "캐릭터 일관성", "CHARACTER", "ANCHOR Layer 2+4 / costume refs"),
    ("E", "구도/여백", "COMPOSITION", "06 composition + constraints"),
    ("F", "소품 정확도", "PROP", "ANCHOR Layer 2 / prop refs"),
    ("G", "얼굴 규칙", "FACE", "ANCHOR face_constraint"),
    ("H", "레퍼런스 반영", "REF", "generate_images.py ref 로직"),
    ("I", "생성 오류", "ARTIFACT", "NB2 모델 한계 / constraints 강화"),
]


def resolve_run_id(project_root: Path) -> str:
    manifest = project_root / "version_manifest.yaml"
    if manifest.exists():
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        return data.get("current_run", "run001")
    # legacy
    dirs = sorted(
        [d for d in (project_root / "07_shot_records").iterdir() if d.is_dir()],
        key=lambda x: x.name,
    )
    return dirs[-1].name if dirs else "v1"


def load_shots(project_root: Path, run_id: str, section_filter: str = None):
    """07_shot_records에서 shot 메타 정보를 로드."""
    records_dir = project_root / "07_shot_records" / run_id
    shots = []

    for section in SECTION_ORDER:
        if section_filter and section != section_filter:
            continue
        section_dir = records_dir / section
        if not section_dir.exists():
            continue
        for f in sorted(section_dir.glob("shot*.md")):
            text = f.read_text(encoding="utf-8")
            # YAML 블록 파싱
            m = re.search(r"```yaml\s*\n---\s*\n(.*?)---\s*\n```", text, re.DOTALL)
            if not m:
                continue
            try:
                data = yaml.safe_load(m.group(1))
            except yaml.YAMLError:
                continue
            if not data:
                continue

            shot_id = data.get("shot_id", 0)
            shots.append({
                "shot_id": shot_id,
                "section": section,
                "local_id": data.get("local_id", ""),
                "scene_type": data.get("scene_type", ""),
                "emotion_tag": data.get("emotion_tag", ""),
                "has_human": data.get("has_human", False),
                "duration_est": data.get("duration_est", ""),
                "costume_refs": data.get("costume_refs", []),
                "prop_refs": data.get("prop_refs", []),
                "asset_path": data.get("asset_path", ""),
            })

    return sorted(shots, key=lambda x: x["shot_id"])


def generate_sheet(
    project_code: str,
    run_id: str,
    shots: list,
    qa_round: int,
    output_path: Path,
):
    today = date.today().isoformat()
    total = len(shots)

    lines = []
    lines.append(f"# QA Sheet — {project_code} {run_id} (Round {qa_round})")
    lines.append(f"DATE: {today}")
    lines.append(f"TOTAL: {total}개")
    lines.append(f"PATH: 09_assets/images/{run_id}/")
    lines.append("")

    # 사용법
    lines.append("> **사용법**: 실패 항목에 `[x]` 체크 → 옆에 증상 메모")
    lines.append("> 체크 없음 = 통과. 기입 완료 후 \"기입 완료\" 입력.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 범례
    lines.append("## 체크 항목 범례")
    lines.append("")
    lines.append("| ID | 항목 | 카테고리 | 실패 시 수정 대상 |")
    lines.append("|---|------|---------|----------------|")
    for item_id, label, cat, target in QA_ITEMS:
        lines.append(f"| {item_id} | {label} | `{cat}` | {target} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section별 체크박스 검수
    current_section = None
    for shot in shots:
        if shot["section"] != current_section:
            current_section = shot["section"]
            lines.append(f"## {current_section}")
            lines.append("")

        sid = shot["shot_id"]
        st = shot["scene_type"]
        em = shot["emotion_tag"]
        _hh_val = str(shot.get("has_human", "none")).lower()
        hh = {"main": "M", "anonym": "A", "none": "N", "true": "M", "false": "N"}.get(_hh_val, _hh_val[0].upper())

        # refs 요약
        refs = []
        if shot["costume_refs"]:
            refs.extend(shot["costume_refs"])
        if shot["prop_refs"]:
            refs.extend(shot["prop_refs"])
        ref_str = ", ".join(refs) if refs else "-"

        # Shot 헤더
        lines.append(
            f"### shot{sid:02d} | {st} | {em} | human:{hh} | refs: {ref_str}"
        )

        # 체크박스 — 실패 항목에 체크
        for item_id, label, cat, _ in QA_ITEMS:
            lines.append(f"- [ ] **{item_id}** {label}")
        lines.append(f"- 비고: ")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 패턴 분석 섹션
    lines.append("## 패턴 분석")
    lines.append("")
    lines.append("### 반복 이슈 (3개 이상 동일 항목 실패 시 기록)")
    lines.append("")
    lines.append("| 카테고리 | 발생 Shot 수 | 대표 증상 | 근원 수정 대상 | 수정 내용 |")
    lines.append("|---------|------------|---------|-------------|---------|")
    lines.append("| | | | | |")
    lines.append("")

    # 통계 섹션
    lines.append("### 통계")
    lines.append("")
    lines.append(f"- 총 이미지: {total}개")
    lines.append("- 전량 통과: 개")
    lines.append("- 조건부 통과: 개")
    lines.append("- 실패 (재생성 필요): 개")
    lines.append("")

    # 액션 섹션
    lines.append("### 다음 액션")
    lines.append("")
    lines.append("- [ ] 개별 shot image_prompt 수정 → 이미지 재생성")
    lines.append("- [ ] 시스템 레벨 수정 (에이전트/스킬)")
    lines.append("- [ ] 전량 재생성")
    lines.append("- [ ] QA 완료 — 편집 진행")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ QA Sheet 생성: {output_path}")
    print(f"   Shot 수: {total}개 | 항목: {len(QA_ITEMS)}개 | Round: {qa_round}")


def main():
    parser = argparse.ArgumentParser(description="QA 체크시트 자동 생성")
    parser.add_argument("--project", required=True, help="프로젝트 코드 (예: CH02E1)")
    parser.add_argument("--section", default=None, help="특정 Section만 (예: SECTION01)")
    parser.add_argument("--round", type=int, default=1, help="검수 라운드 (기본: 1)")
    args = parser.parse_args()

    project_root = WORKSPACE / "projects" / args.project
    if not project_root.exists():
        print(f"[ERROR] 프로젝트 없음: {project_root}")
        sys.exit(1)

    run_id = resolve_run_id(project_root)
    shots = load_shots(project_root, run_id, args.section)

    if not shots:
        print(f"[ERROR] Shot Record 없음: {project_root / '07_shot_records' / run_id}")
        sys.exit(1)

    # 출력 경로: 이미지 폴더 내 QA_SHEET.md
    if args.round > 1:
        filename = f"QA_SHEET_R{args.round}.md"
    else:
        filename = "QA_SHEET.md"

    output_path = project_root / "09_assets" / "images" / run_id / filename
    generate_sheet(args.project, run_id, shots, args.round, output_path)


if __name__ == "__main__":
    main()
