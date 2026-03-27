"""
generate_images.py
==================
image_prompt에서 레퍼런스 이미지를 파싱하고
NB2 API(gemini-3.1-flash-image-preview)로 이미지를 생성합니다.

ref_images YAML 필드에서 이미지 경로를 직접 읽음 (v3 서수 참조)

실행 방법:
  python scripts/generate_images.py --project CH01 [--section HOOK] [--overwrite] [--shots 7,8,9]
  python scripts/generate_images.py --project CH02 --workers 2       ← 내부 병렬 (C)
  python scripts/generate_images.py --project CH02 --section SECTION01 --workers 2  ← A+C 조합

외부 병렬 (A) 사용 시 — 섹션별 6개 프로세스 동시 실행:
  python scripts/generate_images.py --project CH02 --section TITLECARD      --workers 2
  python scripts/generate_images.py --project CH02 --section SECTION00_HOOK --workers 2
  python scripts/generate_images.py --project CH02 --section SECTION01      --workers 2
  ...

매니페스트 모드 (version_manifest.yaml 존재 시):
  python scripts/generate_images.py --project CH02              ← current_run 자동 해상도
  python scripts/generate_images.py --project CH01 --version v5 ← 레거시 강제 지정
"""

import os
import re
import sys
import time
import yaml
import textwrap
import argparse
import threading
import concurrent.futures
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("[ERROR] google-genai 패키지가 없습니다. 아래 명령을 실행하세요:")
    print("  pip install google-genai pillow")
    sys.exit(1)


# ────────────────────────────────────────────────
# 레퍼런스 이미지 라벨 (API 콘텐츠 배열에 이미지 앞에 삽입)
# 우선순위 숫자가 낮을수록 먼저 배치됨
#
# 아키텍처 원칙:
#   characters/*.jpeg  = 완성 캐릭터 레퍼런스 (몸+의상 통합본) → [CHARACTER SOURCE], priority 1
#   basic_chareter_ref.png = 베이스 체형 (costume ref 없는 캐릭터용) → [BASE BODY REFERENCE], priority 2
#   props/*.jpeg     = 소품 레퍼런스 → [OBJECT SOURCE], priority 3
# ────────────────────────────────────────────────
# ────────────────────────────────────────────────
# v3 레퍼런스 이미지 라벨 (THIS {name} 네이밍 — 실험 확정)
# ref_images YAML 배열 순서대로 API에 전달
# {name}은 파일명 stem으로 자동 치환 (예: artisan.jpeg → THIS artisan)
# ────────────────────────────────────────────────
V3_IMAGE_LABELS = {
    "style_reference": (
        "THIS style — 이 이미지의 드로잉 스타일(선의 질감, 음영, 채색 기법)로 장면 전체를 그려줘:"
    , 0),
    "costume_ref": (
        "THIS {name} — 이 대상의 형태만 따라 그려줘:"
    , 1),
    "character_prop_ref": (
        "THIS {name} — 이 대상의 형태만 따라 그려줘:"
    , 1),
    "main_turnaround": (
        "THIS main — 이 캐릭터의 체형과 비율을 따라 그려줘:"
    , 1),
    "crowd_turnaround": (
        "THIS crowd — 이 익명 캐릭터의 체형을 따라 그려줘:"
    , 2),
    "basic_charater_ref": (
        "THIS {name} — 이 대상의 형태만 따라 그려줘:"
    , 2),
    "character_ref": (
        "THIS {name} — 이 대상의 형태만 따라 그려줘:"
    , 2),
    "character_reference": (
        "THIS {name} — 이 캐릭터의 기본 체형을 따라 그려줘:"
    , 2),
    "prop_ref": (
        "THIS {name} — 이 대상의 형태만 따라 그려줘:"
    , 3),
}

# character_prop으로 취급할 파일명 패턴 (ANCHOR character_prop 타입)
CHARACTER_PROP_STEMS = {"ai_robot", "robot", "ai_assistant"}


def _classify_ref_image(ref_path: Path) -> tuple[str, int]:
    """레퍼런스 이미지 경로에서 라벨과 우선순위를 반환.

    감지 순서:
      1) 폴더 기반: characters/ → costume_ref, props/ → prop_ref
      2) 파일명 접두어 매칭
      3) 폴백: 기본 라벨 + 중간 우선순위
    """
    labels = V3_IMAGE_LABELS
    path_parts = [p.lower() for p in ref_path.parts]
    if "characters" in path_parts:
        return labels["costume_ref"]
    elif "props" in path_parts:
        stem = ref_path.stem.lower()
        if stem in CHARACTER_PROP_STEMS:
            return labels["character_prop_ref"]
        if not any(stem.startswith(k) for k in labels):
            return labels["prop_ref"]
    stem = ref_path.stem.lower()
    if stem in CHARACTER_PROP_STEMS:
        return labels["character_prop_ref"]
    for key, (label, priority) in labels.items():
        if stem.startswith(key):
            return label, priority
    return f"참조 이미지 ({ref_path.name}):", 4


SECTION_ORDER = ["TITLECARD", "SECTION00_HOOK", "SECTION01", "SECTION02", "SECTION03", "SECTION04_OUTRO"]


def get_latest_files(visual_dir: Path, section_filter: str = None) -> list[Path]:
    """05_visual_direction 폴더에서 Shot별 최신 버전 파일만 반환."""
    file_map = {}

    for f in visual_dir.rglob("*.md"):
        if "ANCHOR" in f.name.upper():
            continue
        # archived/ 폴더는 이전 버전 보관용 — 이미지 생성 대상에서 제외
        if "archived" in [p.lower() for p in f.parts]:
            continue

        version = None
        section_key = None
        shot_base = None

        m_ver = re.search(r"_v(\d+)\.md$", f.name, re.IGNORECASE)
        if m_ver:
            version = int(m_ver.group(1))
            if f.parent != visual_dir and f.parent.name.upper() != visual_dir.name.upper():
                section_key = f.parent.name.upper()
                shot_base = re.sub(r"_v\d+\.md$", "", f.name, flags=re.IGNORECASE)
            else:
                m_sec = re.search(
                    r"_(SECTION\d+(?:_HOOK|_OUTRO)?|HOOK|OUTRO|TITLECARD)_v\d+\.md$",
                    f.name, re.IGNORECASE
                )
                if not m_sec:
                    continue
                section_key = m_sec.group(1).upper()
                shot_base = re.sub(r"_v\d+\.md$", "", f.name, flags=re.IGNORECASE)
        else:
            rel_parts = f.relative_to(visual_dir).parts
            folder_ver = None
            section_from_path = None
            for part in rel_parts[:-1]:
                m_fv = re.match(r"^v(\d+)$", part, re.IGNORECASE)
                if m_fv:
                    folder_ver = int(m_fv.group(1))
                elif part.lower() == "test":
                    folder_ver = 999
                elif part.lower() == "test2":
                    folder_ver = 1000
                elif re.match(r"^(SECTION\d+|TITLECARD)", part, re.IGNORECASE):
                    section_from_path = part.upper()
            if folder_ver is None:
                continue
            version = folder_ver
            section_key = section_from_path if section_from_path else f.parent.name.upper()
            shot_base = re.sub(r"\.md$", "", f.name, flags=re.IGNORECASE)

        if section_key is None:
            continue
        if section_filter and section_filter.upper() not in section_key:
            continue

        map_key = (section_key, shot_base)
        cur_ver, _ = file_map.get(map_key, (0, None))
        if version > cur_ver:
            file_map[map_key] = (version, f)

    def shot_sort_key(entry):
        shot_base = entry[0][1]
        m = re.search(r"(\d+)", shot_base)
        return int(m.group(1)) if m else 0

    sorted_files = []
    for sec in SECTION_ORDER:
        sec_entries = [(k, v) for k, v in file_map.items() if k[0] == sec]
        sec_entries.sort(key=shot_sort_key)
        for (sec_key, shot_base), (ver, path) in sec_entries:
            rel = path.relative_to(visual_dir)
            print(f"   [버전 선택] {rel}  (v{ver} — 최신)")
            sorted_files.append(path)

    remaining = [(k, v) for k, v in file_map.items() if k[0] not in SECTION_ORDER]
    remaining.sort(key=shot_sort_key)
    for (sec_key, shot_base), (ver, path) in remaining:
        rel = path.relative_to(visual_dir)
        print(f"   [버전 선택] {rel}  (v{ver} — 최신)")
        sorted_files.append(path)

    return sorted_files


def extract_ref_from_yaml(content: str) -> list[str]:
    """YAML ref_images 필드에서 경로 목록을 추출 (v3 전용).

    형식:
      ref_images:
        - characters/run001/artisan.jpeg
        - props/run001/spinning_wheel.jpeg
    """
    m = re.search(r"^ref_images:\s*\n((?:\s+-\s+.+\n?)*)", content, re.MULTILINE)
    if not m:
        return []
    paths = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if line.startswith("- "):
            path = line[2:].strip()
            if path and path not in ("~", "null", "[]"):
                paths.append(path)
    return paths


def extract_thinking_level_from_yaml(content: str) -> str:
    """YAML thinking_level 필드 추출 (v3 전용). 기본값: high."""
    m = re.search(r"^thinking_level:\s*(\S+)", content, re.MULTILINE)
    return m.group(1).lower() if m else "high"


def resolve_ref_path(reference_dir: Path, relative_path: str) -> Path:
    """ref_images 경로를 해석.

    1) reference_dir 기준: props/run001/file.jpeg → reference_dir/props/run001/file.jpeg
    2) 워크스페이스 루트 기준: assets/reference/style/... → workspace_root/assets/...
    존재하지 않으면 그대로 반환 (호출측에서 존재 확인).
    """
    # 1) reference_dir 기준 시도
    resolved = reference_dir / relative_path
    if resolved.exists():
        return resolved
    # 2) 워크스페이스 루트 기준 시도 (assets/reference/style/ 등 채널 공통 경로)
    ws_root = reference_dir
    while ws_root.name and ws_root.name != "projects":
        ws_root = ws_root.parent
    if ws_root.name == "projects":
        ws_root = ws_root.parent
        ws_resolved = ws_root / relative_path
        if ws_resolved.exists():
            return ws_resolved
    return resolved


def generate_image(client, model_name: str, text_prompt: str, ref_image_paths: list[Path],
                    thinking_level: str = "high", style_ref_path: Path = None,
                    style_ref_label: str = None) -> bytes:
    """레퍼런스 이미지 + 텍스트 프롬프트로 이미지를 생성하여 bytes 반환.

    API 전달 순서: [스타일참조, 라벨1, 이미지1, 라벨2, 이미지2, ..., 텍스트 프롬프트]
    ref_images 순서 유지 (THIS {name} 참조와 일치).
    style_ref_label: 커스텀 스타일 참조 라벨 (None이면 기본값 사용)
    """
    contents = []

    # 스타일 참조 이미지 — content 배열 맨 앞에 삽입
    if style_ref_path and style_ref_path.exists():
        label = style_ref_label or "THIS style — 이 이미지의 드로잉 스타일(선의 질감, 음영, 채색 기법)로 장면 전체를 그려줘:"
        contents.append(label)
        with open(style_ref_path, "rb") as f:
            style_bytes = f.read()
        style_suffix = style_ref_path.suffix.lower().lstrip(".")
        style_mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(style_suffix, "image/png")
        contents.append(types.Part.from_bytes(data=style_bytes, mime_type=style_mime))

    if ref_image_paths:
        labeled = []
        for ref_path in ref_image_paths:
            label, priority = _classify_ref_image(ref_path)
            labeled.append((priority, label, ref_path))

        for priority, label, ref_path in labeled:
            contents.append(label.replace("{name}", ref_path.stem))
            with open(ref_path, "rb") as f:
                image_bytes = f.read()
            suffix = ref_path.suffix.lower().lstrip(".")
            mime = {
                "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "webp": "image/webp"
            }.get(suffix, "image/jpeg")
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime))

    contents.append(text_prompt)

    # NB2 Flash는 thinking_level LOW 미지원 → HIGH로 폴백
    think_enum = types.ThinkingLevel.HIGH
    if thinking_level == "low" and "flash" not in model_name:
        think_enum = types.ThinkingLevel.LOW

    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="16:9"),
            thinking_config=types.ThinkingConfig(
                thinking_level=think_enum
            )
        )
    )
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            return part.inline_data.data

    for part in response.candidates[0].content.parts:
        if part.text:
            print(f"   API Text Response: {part.text}")
    raise RuntimeError("API 응답에 이미지가 포함되지 않았습니다.")


def parse_yaml_shot_records(text: str) -> list[dict]:
    """05_visual_direction 파일에서 YAML Shot Record 블록을 파싱.
    ```yaml ... ``` 코드블록 안에 --- 로 구분된 YAML 레코드를 읽는다.
    """
    yaml_match = re.search(r"```yaml\n(.*?)```", text, re.DOTALL)
    content = yaml_match.group(1) if yaml_match else text

    shots = []
    for block in re.split(r"\n---\n", content):
        block = block.strip()
        if not block:
            continue

        m_id = re.search(r"^shot_id:\s*(\S+)", block, re.MULTILINE)
        if not m_id:
            continue
        m_path = re.search(r"^asset_path:\s*(.+)", block, re.MULTILINE)
        if not m_path:
            continue
        # image_prompt 또는 image_prompt[start] (Video Hook) 매칭
        m_prompt = re.search(
            r"^image_prompt:\s*\|\s*\n(.*?)(?=\n[a-zA-Z_#]|\Z)",
            block, re.MULTILINE | re.DOTALL
        )
        m_prompt_start = re.search(
            r"^image_prompt\[start\]:\s*\|\s*\n(.*?)(?=\n[a-zA-Z_#]|\nimage_prompt\[end\]|\Z)",
            block, re.MULTILINE | re.DOTALL
        )
        m_prompt_end = re.search(
            r"^image_prompt\[end\]:\s*\|\s*\n(.*?)(?=\n[a-zA-Z_#]|\Z)",
            block, re.MULTILINE | re.DOTALL
        )

        if m_prompt:
            prompt_raw = textwrap.dedent(m_prompt.group(1)).strip()
            if not prompt_raw or prompt_raw == "~":
                continue
            entry = {
                "shot_id": m_id.group(1),
                "asset_path": m_path.group(1).strip(),
                "image_prompt": prompt_raw,
            }
            # v3 필드: ref_images, thinking_level, has_human
            ref_imgs = extract_ref_from_yaml(block)
            if ref_imgs:
                entry["ref_images"] = ref_imgs
            m_think = re.search(r"^thinking_level:\s*(\S+)", block, re.MULTILINE)
            if m_think:
                entry["thinking_level"] = m_think.group(1).lower()
            m_human = re.search(r"^has_human:\s*(\S+)", block, re.MULTILINE)
            if m_human:
                entry["has_human"] = m_human.group(1).lower()
            shots.append(entry)
        elif m_prompt_start:
            start_raw = textwrap.dedent(m_prompt_start.group(1)).strip()
            end_raw = textwrap.dedent(m_prompt_end.group(1)).strip() if m_prompt_end else None
            if not start_raw or start_raw == "~":
                continue
            shot_entry = {
                "shot_id": m_id.group(1),
                "asset_path": m_path.group(1).strip(),
                "image_prompt": start_raw,  # start를 기본 image_prompt로
                "image_prompt_start": start_raw,
            }
            if end_raw and end_raw not in ("~", "null"):
                shot_entry["image_prompt_end"] = end_raw
            # v3 필드: ref_images, thinking_level, has_human (Video Hook도 동일하게 추출)
            ref_imgs = extract_ref_from_yaml(block)
            if ref_imgs:
                shot_entry["ref_images"] = ref_imgs
            m_think = re.search(r"^thinking_level:\s*(\S+)", block, re.MULTILINE)
            if m_think:
                shot_entry["thinking_level"] = m_think.group(1).lower()
            m_human = re.search(r"^has_human:\s*(\S+)", block, re.MULTILINE)
            if m_human:
                shot_entry["has_human"] = m_human.group(1).lower()
            shots.append(shot_entry)
        else:
            continue

    return shots


def parse_anchor_phase1(anchor_text: str) -> list[dict]:
    """ANCHOR.md Layer 3 섹션에서 Phase 1 렌더링 항목을 파싱.

    형식:
      Type: costume | prop
      Filename: main.jpeg
      ref_label: "THIS main — ..."  (선택)
      ref_file: assets/reference/anchor/main.jpeg  (선택)
      Flow 프롬프트:
      [prompt text ...]

    Layer 3 헤더 ~ Layer 4 헤더 사이 구간을 추출한다.
    """
    # Layer 2 (Phase 1 프롬프트) 또는 레거시 Layer 3 구간 추출
    layer_match = re.search(
        r"##\s*\[Global Visual Anchor.*?Layer [23].*?\](.*?)(?=##\s*\[Global Visual Anchor.*?Layer [34]|\Z)",
        anchor_text, re.DOTALL | re.IGNORECASE
    )
    if not layer_match:
        return []
    layer3_text = layer_match.group(1)

    items = []
    # "Type:" 기준으로 블록 분리 (markdown 헤더 `### Type:` 도 허용)
    blocks = re.split(r"(?=^#{0,6}\s*Type:\s)", layer3_text, flags=re.MULTILINE)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        m_type = re.search(r"^#{0,6}\s*Type:\s*(\S+)", block, re.MULTILINE)
        m_file = re.search(r"^#{0,6}\s*Filename:\s*(\S+)", block, re.MULTILINE)
        m_prompt = re.search(r"^Flow\s*프롬프트:\s*\n(.*)", block, re.DOTALL | re.MULTILINE)
        if not (m_type and m_file and m_prompt):
            continue
        item = {
            "type": m_type.group(1).lower(),       # "costume" | "prop" | "character_prop"
            "filename": m_file.group(1).strip(),    # e.g. "main.jpeg"
            "prompt": m_prompt.group(1).strip(),    # 프롬프트 전문
        }
        # 선택 필드: ref_label, ref_file (턴어라운드 시트 생성용)
        m_label = re.search(r'^ref_label:\s*"(.+)"', block, re.MULTILINE)
        m_ref = re.search(r'^ref_file:\s*(\S+)', block, re.MULTILINE)
        if m_label:
            item["ref_label"] = m_label.group(1)
        if m_ref:
            item["ref_file"] = m_ref.group(1).strip()
        items.append(item)
    return items


def parse_hook_image_prompts(image_prompt_raw: str) -> tuple[str | None, str | None]:
    """Video Hook image_prompt에서 [start]와 [end] 섹션을 분리 추출.

    형식:
      [thinking: high]
      [SOURCE REFERENCES]
      ...

      [start]
      {JSON}

      [end]
      {JSON or null}

    반환: (start_prompt, end_prompt_or_none)
    """
    m_start = re.search(r"\[start\]\s*\n(.*?)(?=\n\s*\[end\]|\Z)", image_prompt_raw, re.DOTALL)
    m_end = re.search(r"\[end\]\s*\n(.*?)$", image_prompt_raw, re.DOTALL)

    start = m_start.group(1).strip() if m_start else None
    end_raw = m_end.group(1).strip() if m_end else None

    # null, ~, 빈 값 처리
    if end_raw and end_raw.lower() in ("null", "~", ""):
        end_raw = None

    # [SOURCE REFERENCES] 블록을 start/end 양쪽에 공유
    src_match = re.search(r"(\[thinking:.*?\]\s*\n)?\s*(\[SOURCE REFERENCES\].*?)(?=\n\s*\[start\])", image_prompt_raw, re.DOTALL)
    shared_header = src_match.group(0).strip() if src_match else ""

    if start and shared_header:
        start = f"{shared_header}\n\n{start}"
    if end_raw and shared_header:
        end_raw = f"{shared_header}\n\n{end_raw}"

    return start, end_raw


def run_phase0(client, project_root: Path, run_id: str, reference_dir: Path, overwrite: bool, workers: int = 1):
    """Video Hook Shot의 start/end 이미지를 생성한다 (Phase 0).

    대상: SECTION00_HOOK 폴더의 hook_media_type: video Shot만.
    입력: image_prompt [start] / [end] 태그 분리.
    출력: 09_assets/images/{run_id}/shot{N}_start.png, shot{N}_end.png
    """
    hook_dir = project_root / "05_visual_direction" / run_id / "SECTION00_HOOK"
    if not hook_dir.exists():
        print(f"[INFO] SECTION00_HOOK 폴더 없음 — Phase 0 스킵: {hook_dir}")
        return

    hook_files = sorted(hook_dir.glob("shot*.md"))
    if not hook_files:
        print("[INFO] SECTION00_HOOK에 Shot 파일 없음 — Phase 0 스킵")
        return

    print(f"\n🎨 Phase 0 — Video Hook 이미지 생성")

    generated = 0
    skipped = 0

    for filepath in hook_files:
        text = filepath.read_text(encoding="utf-8")

        # hook_media_type: video 확인
        m_media = re.search(r"^hook_media_type:\s*(\S+)", text, re.MULTILINE)
        if not m_media or m_media.group(1) != "video":
            continue

        m_id = re.search(r"^shot_id:\s*(\S+)", text, re.MULTILINE)
        if not m_id:
            continue
        shot_id = m_id.group(1)

        # image_prompt 추출
        m_prompt = re.search(
            r"^image_prompt:\s*\|\s*\n(.*?)(?=\n[a-zA-Z_#]|\Z)",
            text, re.MULTILINE | re.DOTALL
        )
        if not m_prompt:
            print(f"   [Shot {shot_id}] ❌ image_prompt를 찾을 수 없습니다")
            continue

        prompt_raw = textwrap.dedent(m_prompt.group(1)).strip()
        start_prompt, end_prompt = parse_hook_image_prompts(prompt_raw)

        if not start_prompt:
            print(f"   [Shot {shot_id}] ❌ image_prompt [start] 태그를 찾을 수 없습니다")
            continue

        # 모델: NB2 고정
        model_str = "gemini-3.1-flash-image-preview"

        # ref_images YAML 필드에서 공통 레퍼런스 추출 (start/end 공유)
        ref_paths_shared = []
        for ref_rel in extract_ref_from_yaml(text):
            ref_p = resolve_ref_path(reference_dir, ref_rel)
            if ref_p.exists():
                if ref_p not in ref_paths_shared:
                    ref_paths_shared.append(ref_p)
            else:
                print(f"   [Shot {shot_id}] ⚠️ ref 파일 미존재 → 스킵: {ref_rel}")

        # thinking_level
        thinking_level_shared = extract_thinking_level_from_yaml(text)

        # 출력 경로
        out_dir = project_root / "09_assets" / "images" / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        start_path = out_dir / f"shot{int(shot_id):02d}_start.png"
        end_path = out_dir / f"shot{int(shot_id):02d}_end.png"

        # Start 이미지 생성
        if start_path.exists() and not overwrite:
            print(f"   [Shot {shot_id} start] 이미 존재 → 스킵")
            skipped += 1
        else:
            print(f"   [Shot {shot_id} start] 🖼️  생성 중...")
            ref_paths = list(ref_paths_shared)

            # 후행 --- 제거
            lines = start_prompt.splitlines()
            while lines and lines[-1].strip() in ("---", ""):
                lines.pop()
            clean_prompt = "\n".join(lines).strip()

            thinking_level = thinking_level_shared

            if ref_paths:
                print(f"   > 레퍼런스 첨부: {', '.join(r.name for r in ref_paths)}")

            try:
                img_bytes = generate_image(client, model_str, clean_prompt, ref_paths, thinking_level)
                start_path.write_bytes(img_bytes)
                print(f"   ✅ 저장: 09_assets/images/{run_id}/shot{int(shot_id):02d}_start.png")
                generated += 1
                time.sleep(1.5)
            except Exception as e:
                print(f"   ❌ 오류 [Shot {shot_id} start]: {e}")

        # End 이미지 생성 (있을 때만)
        if end_prompt:
            if end_path.exists() and not overwrite:
                print(f"   [Shot {shot_id} end] 이미 존재 → 스킵")
                skipped += 1
            else:
                print(f"   [Shot {shot_id} end] 🖼️  생성 중...")
                ref_paths = list(ref_paths_shared)

                lines = end_prompt.splitlines()
                while lines and lines[-1].strip() in ("---", ""):
                    lines.pop()
                clean_prompt = "\n".join(lines).strip()

                thinking_level = thinking_level_shared

                if ref_paths:
                    print(f"   > 레퍼런스 첨부: {', '.join(r.name for r in ref_paths)}")

                try:
                    img_bytes = generate_image(client, model_str, clean_prompt, ref_paths, thinking_level)
                    end_path.write_bytes(img_bytes)
                    print(f"   ✅ 저장: 09_assets/images/{run_id}/shot{int(shot_id):02d}_end.png")
                    generated += 1
                    time.sleep(1.5)
                except Exception as e:
                    print(f"   ❌ 오류 [Shot {shot_id} end]: {e}")

    print(f"\n✅ Phase 0 완료 — 생성: {generated}개 / 스킵: {skipped}개")


def run_phase1(client, project_root: Path, run_id: str, reference_dir: Path, overwrite: bool, workers: int = 1):
    """ANCHOR.md Layer 3 프롬프트로 Phase 1 레퍼런스 이미지를 생성한다.

    출력 경로:
      09_assets/reference/characters/{run_id}/{filename}  (Type: costume)
      09_assets/reference/props/{run_id}/{filename}     (Type: prop)
    """
    anchor_path = project_root / "04_shot_composition" / run_id / "ANCHOR.md"
    if not anchor_path.exists():
        print(f"[ERROR] ANCHOR.md 없음: {anchor_path}")
        return

    anchor_text = anchor_path.read_text(encoding="utf-8")
    items = parse_anchor_phase1(anchor_text)
    if not items:
        print("[ERROR] ANCHOR.md Layer 3 항목을 파싱할 수 없습니다.")
        return

    print(f"\n🎨 Phase 1 — 레퍼런스 이미지 생성 ({len(items)}개)")

    # Phase 1 참조 이미지 탐색: ref_label/ref_file 필드 우선, 없으면 레거시 폴백
    # reference_dir = projects/{PROJECT}/09_assets/reference/ 이므로 workspace root 역산
    _ws_root = reference_dir.parent.parent.parent.parent  # reference/ → 09_assets/ → {PROJECT}/ → projects/ → workspace
    style_ref_dir = _ws_root / "assets" / "reference" / "style"

    # 레거시 폴백용 (ref_label/ref_file 없는 경우)
    base_ref = style_ref_dir / "character_reference.jpeg"
    if not base_ref.exists():
        # 최종 폴백: 프로젝트 내 기존 basic_charector_ref.png
        base_ref = reference_dir / "basic_charector_ref.png"
        if not base_ref.exists():
            candidates = list(reference_dir.glob("basic_char*ref*.png"))
            base_ref = candidates[0] if candidates else base_ref

    generated = 0
    _lock = threading.Lock()

    def _generate_one(item):
        asset_type = item["type"]
        filename   = item["filename"]
        prompt     = item["prompt"]

        type_folder = "characters" if asset_type == "costume" else "props"
        out_path = reference_dir / type_folder / run_id / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if out_path.exists() and not overwrite:
            with _lock:
                print(f"   [Phase1 {filename}] 이미 존재 → 스킵")
            return 0

        with _lock:
            print(f"   [Phase1 {filename}] 🖼️  생성 중... ({type_folder}/{run_id}/)")

        # ref_label + ref_file이 있으면 THIS {name} 방식 사용
        ref_label = item.get("ref_label")
        ref_file_rel = item.get("ref_file")
        style_ref_for_phase1 = None

        if ref_label and ref_file_rel:
            # ref_file 경로 해석: workspace root 기준
            ref_file_path = _ws_root / ref_file_rel
            if not ref_file_path.exists():
                # style 폴더 내 탐색
                ref_file_path = style_ref_dir / Path(ref_file_rel).name
            if ref_file_path.exists():
                # style_ref로 전달 (content 배열 맨 앞에 라벨+이미지 삽입)
                style_ref_for_phase1 = ref_file_path
                with _lock:
                    print(f"   > Phase1 참조: {ref_label} → {ref_file_path.name}")
                ref_paths = []  # ref_label이 있으면 기존 basic_ref 불필요
            else:
                with _lock:
                    print(f"   > Phase1 ref_file 미발견: {ref_file_rel} → 레거시 폴백")
                ref_paths = [base_ref] if base_ref.exists() else []
        else:
            ref_paths = [base_ref] if base_ref.exists() else []

        try:
            image_bytes = generate_image(
                client, "gemini-3.1-flash-image-preview", prompt, ref_paths,
                style_ref_path=style_ref_for_phase1,
                style_ref_label=ref_label,
            )
            out_path.write_bytes(image_bytes)
            with _lock:
                print(f"   ✅ 저장: reference/{type_folder}/{run_id}/{filename}")
            time.sleep(2.0)
            return 1
        except Exception as e:
            with _lock:
                print(f"   ❌ 오류 [{filename}]: {e}")
            return 0

    if workers <= 1:
        for item in items:
            generated += _generate_one(item)
    else:
        print(f"   > 병렬 처리: --workers {workers}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(_generate_one, items))
        generated = sum(results)

    print(f"\n✅ Phase 1 완료 — 생성: {generated}개 / 전체: {len(items)}개")


def process_file(client, filepath: Path, project_root: Path, reference_dir: Path,
                 overwrite: bool, target_shot_ids: set = None, current_run: str = None,
                 style_ref_path: Path = None, chain_mode: bool = False, chain_prev_image: Path = None):
    text = filepath.read_text(encoding="utf-8")

    # 모델: NB2 고정
    model_str = "gemini-3.1-flash-image-preview"

    print(f"   > 사용 모델: {model_str}")

    shots = parse_yaml_shot_records(text)
    if not shots:
        print(f"   [WARN] Shot Record를 찾을 수 없습니다: {filepath.name}")
        return 0, 0

    generated = 0
    skipped = 0
    _prev_chain_image = chain_prev_image  # 체이닝 모드: 이전 파일에서 전달받은 마지막 이미지

    for shot in shots:
        if current_run:
            _remap_asset_path(shot, current_run)
        shot_id = shot["shot_id"]
        asset_rel_path = shot["asset_path"]
        prompt_raw = shot["image_prompt"]

        if target_shot_ids is not None:
            try:
                if int(shot_id) not in target_shot_ids:
                    continue
            except ValueError:
                continue

        out_path = project_root / asset_rel_path
        if out_path.exists() and not overwrite:
            print(f"   [Shot {shot_id}] 이미 존재 → 스킵 ({asset_rel_path})")
            skipped += 1
            continue

        print(f"   [Shot {shot_id}] 🖼️  생성 중... ({asset_rel_path})")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # ref_images YAML 필드에서 직접 읽음 (순서 유지)
        # 주의: ref_images가 빈 배열 []일 때도 분기 유지 (falsy 방지 — is not None 체크)
        ref_image_paths = []
        if shot.get("ref_images") is not None:
            for f in shot["ref_images"]:
                ref_p = resolve_ref_path(reference_dir, f)
                if ref_p.exists():
                    if ref_p not in ref_image_paths:
                        ref_image_paths.append(ref_p)
                else:
                    print(f"   [Shot {shot_id}] ⚠️ ref 파일 미존재 → 스킵: {f}")

        # 체이닝 모드: 이전 Shot 생성 이미지를 ref에 추가
        if chain_mode and _prev_chain_image and _prev_chain_image.exists():
            if _prev_chain_image not in ref_image_paths:
                ref_image_paths.append(_prev_chain_image)
                print(f"   > 체이닝 참조 자동 첨부: {_prev_chain_image.name}")

        if ref_image_paths:
            print(f"   > 레퍼런스 첨부: {', '.join(r.name for r in ref_image_paths)}")
        else:
            print(f"   > 레퍼런스: 없음")

        # 후행 --- 제거 외 추가 처리 없음 — 프롬프트를 그대로 전달
        lines = prompt_raw.splitlines()
        while lines and lines[-1].strip() in ("---", ""):
            lines.pop()
        prompt_clean = "\n".join(lines).strip()

        # thinking_level: YAML 필드에서 읽기
        thinking_level = shot.get("thinking_level", "high")

        # ref_images에 style_reference가 포함되어 있으면 style_ref_path 중복 방지
        _effective_style_ref = style_ref_path
        if any("style_reference" in str(p) for p in ref_image_paths):
            _effective_style_ref = None

        try:
            image_bytes = generate_image(
                client, model_str, prompt_clean, ref_image_paths, thinking_level,
                style_ref_path=_effective_style_ref,
            )
            out_path.write_bytes(image_bytes)
            print(f"   ✅ 저장: {asset_rel_path}")
            generated += 1
            if chain_mode:
                _prev_chain_image = out_path
            time.sleep(1.5)
        except Exception as e:
            print(f"   ❌ 오류: {e}")

    return generated, skipped, _prev_chain_image


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


def _resolve_path(project_root, stage, run_id, section):
    """stage/run_id/section 경로를 반환한다."""
    return project_root / stage / run_id / section


def _collect_manifest_files(project_root, current_run: str, source_folder: str, section_filter: str = None) -> list[Path]:
    """매니페스트 기반 파일 수집. Section별 경로로 Shot 파일 목록 반환."""
    target_sections = [section_filter] if section_filter else SECTION_ORDER
    files = []

    for section in target_sections:
        section_dir = _resolve_path(project_root, source_folder, current_run, section)
        if section_dir and section_dir.exists():
            shot_files = sorted(section_dir.glob("shot*.md"))
            files.extend(shot_files)

    return files


def _remap_asset_path(shot: dict, current_run: str):
    """asset_path를 현재 run으로 리매핑.

    09_assets/images/v1/shotNN.png → 09_assets/images/{current_run}/shotNN.png
    """
    asset_path = shot.get("asset_path", "")
    if asset_path:
        # v숫자/ 또는 run숫자/ 패턴을 현재 run으로 교체
        remapped = re.sub(
            r"09_assets/images/[^/]+/",
            f"09_assets/images/{current_run}/",
            asset_path,
        )
        shot["asset_path"] = remapped


def main():
    parser = argparse.ArgumentParser(description="05_visual_direction Shot Record 이미지 생성기")
    parser.add_argument("--project", required=True, help="프로젝트 코드 (예: CH01)")
    parser.add_argument("--section", help="처리할 섹션 (예: HOOK). 생략 시 전체")
    parser.add_argument("--overwrite", action="store_true", help="기존 파일 덮어쓰기")
    parser.add_argument("--shots", help="처리할 Shot ID 목록 (쉼표 구분, 예: 7,8,9)")
    parser.add_argument("--source", help="Shot Record 소스 폴더 (기본: 05_visual_direction)")
    parser.add_argument("--version", default=None, help="버전 (레거시: v1 등. 생략 시 매니페스트 자동)")
    parser.add_argument("--workers", type=int, default=3,
                        help="동시 처리 Shot 수 (기본: 3=병렬). 순차 처리 시 1 지정")
    parser.add_argument("--phase", type=int, choices=[0, 1, 2], default=2,
                        help="실행 Phase: 0=Video Hook 이미지 생성, 1=ANCHOR 레퍼런스 이미지 생성, 2=씬 이미지 생성 (기본: 2)")
    parser.add_argument("--style-ref", default=None,
                        help="스타일 참조 이미지 경로. 지정 시 모든 Shot의 content 배열 맨 앞에 삽입")
    parser.add_argument("--chain", action="store_true",
                        help="체이닝 모드: Shot을 순차 생성하며, 이전 Shot 생성 이미지를 다음 Shot의 ref에 자동 추가. Kinetic Transition Hook의 시각 일관성 보장.")
    args = parser.parse_args()

    target_shot_ids = None
    if args.shots:
        target_shot_ids = set(int(s.strip()) for s in args.shots.split(",") if s.strip().isdigit())

    workspace_root = Path(__file__).parents[4].absolute()  # scripts/ → generate-images/ → skills/ → .claude/ → workspace root
    project_root   = workspace_root / "projects" / args.project
    source_folder  = args.source if args.source else "05_visual_direction"
    reference_dir  = project_root / "09_assets" / "reference"

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

    current_run = version if use_manifest else None
    visual_dir = project_root / source_folder

    if not use_manifest and not visual_dir.exists():
        print(f"[ERROR] {source_folder} 폴더가 없습니다: {visual_dir}")
        sys.exit(1)

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
    print(f"\n🚀 generate_images.py 시작 (Project: {args.project}, Phase: {args.phase})")
    if args.overwrite:
        print("   > 덮어쓰기 모드 활성화")

    # Phase 0: Video Hook 이미지 생성
    if args.phase == 0:
        run_phase0(client, project_root, version if use_manifest else "v1", reference_dir, args.overwrite, args.workers)
        return

    # Phase 1: ANCHOR 레퍼런스 이미지 생성
    if args.phase == 1:
        run_phase1(client, project_root, version if use_manifest else "v1", reference_dir, args.overwrite, args.workers)
        return

    if use_manifest:
        print(f"   > 매니페스트 모드 (Run: {current_run})")
        target_files = _collect_manifest_files(project_root, current_run, source_folder, args.section)
    else:
        print(f"\n📁 {source_folder} 파일 선택 (Section별 최신 버전):")
        target_files = get_latest_files(visual_dir, args.section)

    if not target_files:
        section_msg = f"섹션 '{args.section}'" if args.section else "전체"
        print(f"[ERROR] 처리할 파일이 없습니다 ({section_msg})")
        sys.exit(1)

    # 스타일 참조 이미지 경로 — CLI 지정 > 자동 탐색 (assets/reference/anchor/style_ref.png)
    _style_ref_path = Path(args.style_ref).resolve() if args.style_ref else None
    if not _style_ref_path:
        _auto_style = workspace_root / "assets" / "reference" / "style" / "style_reference.png"
        if _auto_style.exists():
            _style_ref_path = _auto_style
            print(f"   > 스타일 참조 자동 감지: {_auto_style.relative_to(workspace_root)}")
    if _style_ref_path and _style_ref_path.exists():
        print(f"   > 스타일 참조 이미지: {_style_ref_path.name}")

    total_generated = 0
    total_skipped   = 0
    _lock = threading.Lock()

    _chain_prev = None  # 체이닝 모드: 파일 간 마지막 이미지 전달

    def _process_one(f):
        nonlocal _chain_prev
        with _lock:
            print(f"\n📄 {f.name}")
        gen, skip, last_img = process_file(client, f, project_root, reference_dir, args.overwrite, target_shot_ids, current_run=current_run, style_ref_path=_style_ref_path, chain_mode=args.chain, chain_prev_image=_chain_prev)
        with _lock:
            nonlocal total_generated, total_skipped
            total_generated += gen
            total_skipped   += skip
        if args.chain and last_img:
            _chain_prev = last_img

    # 체이닝 모드: 순차 실행 강제 (이전 Shot 이미지를 다음 Shot ref에 추가하므로)
    effective_workers = 1 if args.chain else args.workers
    if args.chain:
        print(f"   > 체이닝 모드: 순차 실행 (이전 Shot → 다음 Shot ref 자동 추가)")

    if effective_workers <= 1:
        for f in target_files:
            _process_one(f)
    else:
        print(f"   > 병렬 처리: --workers {args.workers}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(_process_one, f): f for f in target_files}
            for future in concurrent.futures.as_completed(futures):
                if future.exception():
                    with _lock:
                        print(f"   ❌ 오류: {futures[future].name} — {future.exception()}")

    print(f"\n✅ 완료 — 생성: {total_generated}개 / 스킵: {total_skipped}개")



if __name__ == "__main__":
    main()
