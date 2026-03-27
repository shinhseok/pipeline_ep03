#!/usr/bin/env python3
"""version_manager.py — Run-based pipeline versioning (YAML CRUD).

Supports two manifest formats:
  - Dict format (existing): runs as dict keyed by run_id, sections as dict(section→run_id)
  - List format (new init): runs as list of dicts

Usage:
    python version_manager.py --project CH02 init [--description "Full run"]
    python version_manager.py --project CH02 new-run [--sections SECTION01] [--description "SEC01 fix"]
    python version_manager.py --project CH02 bump 07_shot_records
    python version_manager.py --project CH02 status
"""

import argparse
import io
import sys
from datetime import date
from pathlib import Path

# Windows cp949 encoding fix
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    import yaml
except ImportError:
    sys.exit("ERROR: PyYAML not installed. Run: pip install pyyaml")

WORKSPACE = Path(__file__).resolve().parents[4]
VALID_STAGES = [
    "04_shot_composition",
    "05_visual_direction",
    "06_audio_narration",
    "07_shot_records",
    "08_storyboard",
    "09_assets",
]
VALID_SECTIONS = [
    "TITLECARD",
    "SECTION00_HOOK",
    "SECTION01",
    "SECTION02",
    "SECTION03",
    "SECTION04_OUTRO",
]


def manifest_path(project: str) -> Path:
    return WORKSPACE / "projects" / project / "version_manifest.yaml"


def load_manifest(project: str) -> dict:
    p = manifest_path(project)
    if not p.exists():
        sys.exit(f"ERROR: {p} not found. Run 'init' first.")
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_manifest(project: str, data: dict):
    p = manifest_path(project)
    with open(p, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"Saved: {p}")


def is_dict_format(data: dict) -> bool:
    """Check if manifest uses dict format (runs keyed by run_id)."""
    runs = data.get("runs", {})
    return isinstance(runs, dict)


def get_run_ids(data: dict) -> list[str]:
    """Get sorted list of run IDs from either format."""
    runs = data.get("runs", {})
    if isinstance(runs, dict):
        return sorted(runs.keys())
    elif isinstance(runs, list):
        return [r["run_id"] for r in runs]
    return []


def get_max_run_num(data: dict) -> int:
    """Get the highest run number from either format."""
    ids = get_run_ids(data)
    if not ids:
        return 0
    return max(int(rid.replace("run", "")) for rid in ids)


# ── Commands ────────────────────────────────────────────

def cmd_init(args):
    p = manifest_path(args.project)
    if p.exists() and not args.force:
        sys.exit(f"ERROR: {p} already exists. Use --force to overwrite.")
    p.parent.mkdir(parents=True, exist_ok=True)

    all_sections = {s: "run001" for s in VALID_SECTIONS}
    data = {
        "current_run": "run001",
        "runs": {
            "run001": {
                "created": str(date.today()),
                "status": "in_progress",
                "note": args.description or "Full run",
                "sections": all_sections,
            }
        },
    }
    save_manifest(args.project, data)
    print(f"✅ Initialized {args.project} — run001")


def cmd_new_run(args):
    data = load_manifest(args.project)
    new_num = get_max_run_num(data) + 1
    new_id = f"run{new_num:03d}"

    # Determine sections
    partial_sections = None
    if args.sections:
        partial_sections = [s.strip() for s in args.sections.split(",")]
        for s in partial_sections:
            if s not in VALID_SECTIONS:
                sys.exit(f"ERROR: Invalid section '{s}'. Valid: {VALID_SECTIONS}")

    if is_dict_format(data):
        # Dict format: sections map section→run_id
        current = data["current_run"]
        prev_run = data["runs"].get(current, {})
        prev_sections = prev_run.get("sections", {})

        if partial_sections:
            # Partial update: only specified sections get new run_id
            new_sections = dict(prev_sections)
            for s in partial_sections:
                new_sections[s] = new_id
        else:
            new_sections = {s: new_id for s in VALID_SECTIONS}

        data["runs"][new_id] = {
            "created": str(date.today()),
            "status": "in_progress",
            "note": args.description or (f"Partial: {','.join(partial_sections)}" if partial_sections else "Full run"),
            "base_run": current,
            "sections": new_sections,
        }
    else:
        # List format
        new_run = {
            "run_id": new_id,
            "description": args.description or "Full run",
            "created": str(date.today()),
            "sections": partial_sections,
            "stages_done": [],
        }
        data["runs"].append(new_run)

    data["current_run"] = new_id
    save_manifest(args.project, data)
    scope = f"sections={partial_sections}" if partial_sections else "전체"
    print(f"✅ Created {new_id} ({scope})")


def cmd_bump(args):
    stage = args.stage
    if stage not in VALID_STAGES:
        sys.exit(f"ERROR: Invalid stage '{stage}'. Valid: {VALID_STAGES}")

    data = load_manifest(args.project)
    current = data["current_run"]

    if is_dict_format(data):
        run = data["runs"].get(current)
        if not run:
            sys.exit(f"ERROR: current_run '{current}' not found.")
        done = run.get("stages_done", [])
        if stage not in done:
            done.append(stage)
            run["stages_done"] = done
        save_manifest(args.project, data)
    else:
        for run in data["runs"]:
            if run["run_id"] == current:
                done = run.get("stages_done", [])
                if stage not in done:
                    done.append(stage)
                    run["stages_done"] = done
                save_manifest(args.project, data)
                break
        else:
            sys.exit(f"ERROR: current_run '{current}' not found.")

    print(f"✅ {current}: {stage} marked done")


def cmd_status(args):
    data = load_manifest(args.project)
    current = data.get("current_run", "?")
    project = data.get("project", args.project)
    print(f"\n📦 {project} 버전 현황")
    print(f"current_run: {current}\n")

    if is_dict_format(data):
        for rid in get_run_ids(data):
            run = data["runs"][rid]
            created = run.get("created", "?")
            status = run.get("status", "?")
            note = run.get("note", "")
            marker = " ← current" if rid == current else ""
            sections = run.get("sections", {})

            # Count unique sections pointing to this run
            own_sections = [s for s, r in sections.items() if r == rid]
            if len(own_sections) == len(VALID_SECTIONS):
                scope = "전체"
            else:
                scope = ",".join(own_sections) if own_sections else "전체"

            print(f"{rid} ({created}) — {scope} [{status}]{marker}")
            if note:
                print(f"  📝 {note}")

            # Show stages_done if present
            done = set(run.get("stages_done", []))
            if done:
                for stage in VALID_STAGES:
                    icon = "✅" if stage in done else "⏳"
                    print(f"  {icon} {stage}")
            print()
    else:
        for run in data.get("runs", []):
            rid = run["run_id"]
            created = run.get("created", "?")
            sections = run.get("sections")
            scope = "전체" if sections is None else ",".join(sections)
            marker = " ← current" if rid == current else ""
            desc = run.get("description", "")

            print(f"{rid} ({created}) — {scope}{marker}")
            if desc:
                print(f"  📝 {desc}")
            done = set(run.get("stages_done", []))
            for stage in VALID_STAGES:
                icon = "✅" if stage in done else "⏳"
                print(f"  {icon} {stage}")
            print()


def main():
    parser = argparse.ArgumentParser(description="Pipeline version manager")
    parser.add_argument("--project", required=True, help="PROJECT_CODE (e.g. CH02)")
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Initialize manifest")
    p_init.add_argument("--description", default=None)
    p_init.add_argument("--force", action="store_true")

    p_new = sub.add_parser("new-run", help="Create new run")
    p_new.add_argument("--sections", default=None, help="Comma-separated sections")
    p_new.add_argument("--description", default=None)

    p_bump = sub.add_parser("bump", help="Mark stage complete")
    p_bump.add_argument("stage", help="Stage name (e.g. 07_shot_records)")

    sub.add_parser("status", help="Show version status")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"init": cmd_init, "new-run": cmd_new_run, "bump": cmd_bump, "status": cmd_status}[
        args.command
    ](args)


if __name__ == "__main__":
    main()
