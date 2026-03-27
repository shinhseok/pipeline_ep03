"""
validate_image_prompt.py
image_prompt 내부 구조 자동 검증 스크립트 (v2/v3 듀얼 모드)

사용법:
  python scripts/validate_image_prompt.py --project CH02              # current_run, 07_shot_records
  python scripts/validate_image_prompt.py --project CH02 --run run003 # 특정 run
  python scripts/validate_image_prompt.py --project CH02 --source 06  # 05_visual_direction (delta)
  python scripts/validate_image_prompt.py --project CH02 --strict      # 경고도 오류로 처리
  python scripts/validate_image_prompt.py --project CH02 --section SECTION01

버전 자동 감지:
  v3: ref_images YAML 필드 존재 → v3 검증 (한국어 서술형)
  v2: [SCENE]/[MUST] 태그 존재 → v2 검증 (구조적 태그)

v3 검증 항목:
  ERROR  STRUCTURAL_TAG_FOUND    구조적 태그 잔존 ([SCENE], [MUST] 등)
  ERROR  REF_IMAGES_MISSING      ref_images 필드 누락 (참조 있어야 할 때)
  ERROR  ORDINAL_MISMATCH        서수 참조와 ref_images 수 불일치
  ERROR  HAS_HUMAN_NO_REF        has_human:main인데 캐릭터 ref 없음
  WARNING ANONYM_NO_CHAR_REF     has_human:anonym인데 character_reference.jpeg 미포함
  ERROR  QUALITY_SUFFIX          품질 접미사 사용
  WARNING STYLE_KW_MISSING       스타일 키워드 누락
  WARNING BACKGROUND_KW_MISSING  배경 키워드 누락
  WARNING KOREAN_MISSING         한국어 서술 없음
  WARNING SIZE_TRIPLE_MISSING    크기 3중 표현 누락
  WARNING COUNT_MISSING          카운트 제약 누락
  WARNING FACE_RULE_MISSING      얼굴 규칙 누락 (has_human:main)
  WARNING SINGLE_SCENE_MISSING   단일 장면 가드 누락

v2 검증 항목 (기존):
  ERROR  TASK_BLOCK_MISSING    TASK block 누락
  ERROR  SCENE_BLOCK_MISSING   [SCENE] block 누락
  ERROR  MUST_BLOCK_MISSING    [MUST] block 누락
  ERROR  MUST_OVER_LIMIT       [MUST] 항목 6개 이상 (최대 5)
  ERROR  REDRAW_MISSING        REDRAW 항목 누락 (SOURCE REF 있을 때)
  ERROR  REF_CONFLICT          [CHARACTER SOURCE] + [BASE BODY REFERENCE] 동시 포함
  ERROR  DEPRECATED_ID         deprecated identifier 형식
  ERROR  HAS_HUMAN_NO_REF      has_human:true인데 SOURCE REF 없음
  WARNING BACKGROUND_MUST      배경 [MUST] 항목 누락
  WARNING STYLE_ANCHOR         스타일 앵커 문구 누락 (SCENE HOW줄)
  WARNING STYLE_ISOLATION      금지 스타일 표현이 [SCENE]에 있음
  WARNING FACE_MUST_MISSING    has_human:true인데 얼굴 [MUST] 없음
  WARNING EMOTION_EXPR_MISSING emotion_tag에 맞는 표정 표현 누락
  WARNING SIZE_PERCENT_MISSING 캐릭터 프레임 점유율(%) 누락

파이프라인 통합:
  merge_records.py 실행 전 의무 실행. 오류 발견 시 exit(1)로 merge 블로킹.
"""

import sys
import io
import re
import yaml
import argparse
from pathlib import Path

# Windows cp949 환경에서 UTF-8 출력 강제
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parents[3]

# ─── 공통 패턴 ───────────────────────────────────────────────────────────────

# 품질 접미사 금지
QUALITY_SUFFIX_PATTERN = re.compile(
    r"\b(4k|masterpiece|HD|high quality|ultra realistic|photorealistic)\b", re.IGNORECASE
)

# Style Isolation 금지어
STYLE_ISOLATION_KEYWORDS = [
    "charcoal fill", "solid fill", "dark fill", "dense shadow",
    "ink silhouette", "flat ink", "watercolor wash pooling",
    "dense cross-hatch", "heavy pencil",
]


# ─── 유틸리티 ─────────────────────────────────────────────────────────────────

def parse_yaml_field(content: str, field: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(field)}:\s*(.+)$", re.MULTILINE)
    match = pattern.search(content)
    return match.group(1).strip() if match else None


def parse_multiline_field(content: str, field: str) -> str | None:
    pattern = re.compile(
        rf"^{re.escape(field)}:\s*\|\n((?:(?:  .*|)\n)*)", re.MULTILINE
    )
    match = pattern.search(content)
    if not match:
        return None
    raw = match.group(1)
    lines = raw.split("\n")
    stripped = "\n".join(line[2:] if line.startswith("  ") else line for line in lines)
    return stripped


def detect_prompt_version(content: str) -> str:
    """v3 vs v2 자동 감지."""
    # v3 감지: ref_images 리스트 존재 OR thinking_level 필드 존재 OR ref_images: [] 빈 배열
    if re.search(r"^ref_images:\s*\n\s+-", content, re.MULTILINE):
        return "v3"
    if re.search(r"^thinking_level:\s*(high|low)", content, re.MULTILINE):
        return "v3"
    if re.search(r"^ref_images:\s*\[\s*\]", content, re.MULTILINE):
        return "v3"
    return "v2"


def extract_ref_images_list(content: str) -> list[str]:
    """ref_images YAML 필드에서 경로 목록 추출."""
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


# ─── v2 검증 패턴 ────────────────────────────────────────────────────────────

TASK_PATTERN = re.compile(r"TASK:\s*Draw a single narrative scene", re.IGNORECASE)
THINKING_LOW_PATTERN = re.compile(r"\[thinking:\s*(low|medium)\]", re.IGNORECASE)
SCENE_BLOCK_PATTERN = re.compile(r"^\[SCENE\]", re.MULTILINE)
MUST_BLOCK_PATTERN = re.compile(r"^\[MUST\]", re.MULTILINE)
MUST_ITEM_PATTERN = re.compile(r"^- ", re.MULTILINE)
REDRAW_PATTERN = re.compile(
    r"REDRAW \[(CHARACTER SOURCE|OBJECT SOURCE|BASE BODY REFERENCE)\]", re.IGNORECASE
)
SOURCE_REF_BLOCK_PATTERN = re.compile(
    r"\[SOURCE REFERENCES\](.*?)(?=\n\[SCENE\]|\n\{|\Z)", re.DOTALL
)
DEPRECATED_ID_PATTERN = re.compile(r"THIS WISEMAN in \w+", re.IGNORECASE)
STYLE_ANCHOR_PATTERN = re.compile(r"Fine trembling ink lines", re.IGNORECASE)
BACKGROUND_MUST_PATTERN = re.compile(r"Bare white canvas background", re.IGNORECASE)
FACE_MUST_PATTERN = re.compile(r"(small round dot eyes|NO nose)", re.IGNORECASE)
SIZE_PERCENT_PATTERN = re.compile(r"\d+%\s*(?:of\s*frame|of\s*the\s*frame)", re.IGNORECASE)

EMOTION_EXPRESSION_PATTERNS = {
    "REVEAL":     re.compile(r"eyes\s+wide|mouth\s+drop|surprise|jaw\s+drop|leaning\s+back", re.IGNORECASE),
    "REFLECTIVE": re.compile(r"eyes\s+(?:cast\s+)?downward|quiet\s+stillness|downcast|gaze\s+down|mouth\s+closed", re.IGNORECASE),
    "HUMOR":      re.compile(r"eyebrow\s+cocked|lopsided\s+grin|grin|smirk|wry|one\s+eyebrow", re.IGNORECASE),
    "AWE":        re.compile(r"eyes\s+wide\s+open|mouth\s+slightly\s+parted|wonder|agape|mouth.*open", re.IGNORECASE),
    "TENSION":    re.compile(r"eyes\s+narrowed|brow\s+(creased|furrowed)|hunched|shoulders\s+tight", re.IGNORECASE),
}


# ─── v3 검증 패턴 ────────────────────────────────────────────────────────────

# 구조적 태그 잔존 감지 (v3에서는 없어야 함)
V3_STRUCTURAL_TAG_PATTERN = re.compile(
    r"\[(?:SCENE|MUST|SOURCE REFERENCES|thinking:\s*(?:high|low|medium))\]|^TASK:\s*Draw",
    re.MULTILINE | re.IGNORECASE
)

# v3 스타일 키워드 (한국어)
V3_STYLE_KEYWORDS = re.compile(r"(떨림|잉크\s*선|교차\s*해칭|cross-hatching|펜\s*드로잉)", re.IGNORECASE)

# v3 배경 키워드 (한국어)
V3_BACKGROUND_KEYWORDS = re.compile(
    r"(순백|빈\s*공간|색이나\s*질감이\s*없는|배경.*연하고\s*가늘게|배경.*윤곽|배경.*암시|배경에는)", re.IGNORECASE
)

# v3 한국어 존재 확인
V3_KOREAN_PATTERN = re.compile(r"[\uac00-\ud7af]")

# v3 크기 표현: 수치(N%), 상대비교, 은유 — 최소한 수치 확인
V3_SIZE_PERCENT_PATTERN = re.compile(r"\d+%")

# v3 카운트 제약
V3_COUNT_PATTERN = re.compile(r"정확히\s*[\s\S]+?만\s*그려", re.IGNORECASE)

# v3 얼굴 규칙
V3_FACE_RULE_PATTERN = re.compile(r"(코\s*없이|점\s*형태의\s*눈)", re.IGNORECASE)

# v3 단일 장면 가드
V3_SINGLE_SCENE_PATTERN = re.compile(r"(하나의\s*장면만|한\s*장을)", re.IGNORECASE)

# v3 서수 참조 패턴
V3_ORDINAL_PATTERN = re.compile(r"(첫\s*번째|두\s*번째|세\s*번째|네\s*번째)\s*이미지")


# ─── v3 검증 로직 ────────────────────────────────────────────────────────────

def validate_v3_image_prompt(path: Path, check_emotion: bool = False, strict: bool = False) -> list[dict]:
    """v3 Shot 파일의 image_prompt 검증."""
    issues = []
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return [{"level": "ERROR", "check": "READ_ERROR", "message": str(e), "file": str(path)}]

    def add(level: str, check: str, msg: str):
        issues.append({"level": level, "check": check, "message": msg, "file": str(path)})

    # image_prompt 추출
    image_prompt = parse_multiline_field(content, "image_prompt")
    if image_prompt is None:
        image_prompt = parse_yaml_field(content, "image_prompt") or ""

    if not image_prompt.strip():
        add("WARNING", "FLOW_PROMPT_EMPTY", "image_prompt 필드 없음 — 검증 건너뜀")
        return issues

    has_human_str = (parse_yaml_field(content, "has_human") or "none").lower()
    # 레거시 호환
    if has_human_str == "true":
        has_human_str = "main"
    elif has_human_str == "false":
        has_human_str = "none"
    is_main = has_human_str == "main"
    is_anonym = has_human_str == "anonym"
    has_human = is_main or is_anonym  # 사람 형태 존재 여부 (크기 표현 등에 사용)

    # ── Check 1: 구조적 태그 잔존 ──
    m = V3_STRUCTURAL_TAG_PATTERN.search(image_prompt)
    if m:
        add("ERROR", "STRUCTURAL_TAG_FOUND",
            f"v3 image_prompt에 구조적 태그 잔존: '{m.group()}' — 순수 한국어 서술만 허용")

    # ── Check 2: ref_images 필드 ──
    ref_images = extract_ref_images_list(content)
    if is_main and not ref_images:
        add("ERROR", "HAS_HUMAN_NO_REF",
            "has_human:main이지만 ref_images 없음 → 리얼 사람 생성 위험")
    if is_anonym:
        has_char_ref = any("character_reference" in r for r in ref_images)
        if not has_char_ref:
            add("WARNING", "ANONYM_NO_CHAR_REF",
                "has_human:anonym이지만 character_reference.jpeg 미포함")

    # ── Check 3: 서수 참조 일치 ──
    ordinals_in_prompt = V3_ORDINAL_PATTERN.findall(image_prompt)
    ordinal_count = len(set(ordinals_in_prompt))
    if ref_images and ordinal_count > len(ref_images):
        add("ERROR", "ORDINAL_MISMATCH",
            f"서수 참조 {ordinal_count}개 > ref_images {len(ref_images)}개 — 순서 불일치")

    # ── Check 4: 스타일 키워드 ──
    if not V3_STYLE_KEYWORDS.search(image_prompt):
        add("WARNING", "STYLE_KW_MISSING",
            "스타일 키워드 누락 ('떨림', '잉크 선', '교차 해칭' 등)")

    # ── Check 5: 배경 키워드 ──
    if not V3_BACKGROUND_KEYWORDS.search(image_prompt):
        add("WARNING", "BACKGROUND_KW_MISSING",
            "배경 키워드 누락 ('순백', '빈 공간' 등)")

    # ── Check 6: 한국어 존재 ──
    if not V3_KOREAN_PATTERN.search(image_prompt):
        add("WARNING", "KOREAN_MISSING",
            "image_prompt에 한국어 서술 없음 — v3는 순수 한국어 필수")

    # ── Check 7: 크기 표현 (has_human) ──
    if has_human and not V3_SIZE_PERCENT_PATTERN.search(image_prompt):
        add("WARNING", "SIZE_TRIPLE_MISSING",
            "크기 수치(N%) 누락 — 크기 3중 표현 필수")

    # ── Check 8: 카운트 제약 ──
    if not V3_COUNT_PATTERN.search(image_prompt):
        add("WARNING", "COUNT_MISSING",
            "카운트 제약 누락 ('정확히 ~만 그려줘')")

    # ── Check 9: 얼굴 규칙 (has_human:main, 실루엣/손만 등장 예외) ──
    is_silhouette = bool(re.search(r"실루엣", image_prompt))
    is_hand_only = bool(re.search(r"손바닥|손\s*스케치", image_prompt)) and not re.search(r"캐릭터가|캐릭터는", image_prompt)
    if is_main and not is_silhouette and not is_hand_only and not V3_FACE_RULE_PATTERN.search(image_prompt):
        add("WARNING", "FACE_RULE_MISSING",
            "has_human:main인데 얼굴 규칙 누락 ('코 없이', '점 형태의 눈')")

    # ── Check 10: 단일 장면 가드 ──
    if not V3_SINGLE_SCENE_PATTERN.search(image_prompt):
        add("WARNING", "SINGLE_SCENE_MISSING",
            "단일 장면 가드 누락 ('하나의 장면만' 또는 '한 장을')")

    # ── Check 11: 품질 접미사 ──
    quality_match = QUALITY_SUFFIX_PATTERN.search(image_prompt)
    if quality_match:
        add("ERROR", "QUALITY_SUFFIX",
            f"품질 접미사 사용 금지: '{quality_match.group()}'")

    # ── Check 12: Style Isolation 금지어 ──
    for kw in STYLE_ISOLATION_KEYWORDS:
        if kw.lower() in image_prompt.lower():
            add("WARNING", "STYLE_ISOLATION",
                f"금지 스타일 표현: '{kw}'")
            break

    # ── Check 13: thinking_level 필드 ──
    thinking = parse_yaml_field(content, "thinking_level")
    if not thinking:
        add("WARNING", "THINKING_LEVEL_MISSING",
            "thinking_level YAML 필드 누락 (기본값 high 사용)")

    return issues


# ─── v2 검증 로직 (기존) ──────────────────────────────────────────────────────

def validate_v2_image_prompt(path: Path, check_emotion: bool = False, strict: bool = False) -> list[dict]:
    """v2 Shot 파일의 image_prompt 검증 (기존 로직)."""
    issues = []
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return [{"level": "ERROR", "check": "READ_ERROR", "message": str(e), "file": str(path)}]

    def add(level: str, check: str, msg: str):
        issues.append({"level": level, "check": check, "message": msg, "file": str(path)})

    image_prompt = parse_multiline_field(content, "image_prompt")
    if image_prompt is None:
        image_prompt = parse_yaml_field(content, "image_prompt") or ""

    if not image_prompt.strip():
        add("WARNING", "FLOW_PROMPT_EMPTY", "image_prompt 필드 없음 — 검증 건너뜀")
        return issues

    has_human_str = (parse_yaml_field(content, "has_human") or "none").lower()
    # 레거시 호환
    if has_human_str == "true":
        has_human_str = "main"
    elif has_human_str == "false":
        has_human_str = "none"
    has_human = has_human_str in ("main", "anonym")
    emotion_tag = (parse_yaml_field(content, "emotion_tag") or "").upper()

    # Check 1: TASK block
    if not TASK_PATTERN.search(image_prompt):
        add("ERROR", "TASK_BLOCK_MISSING",
            "TASK block 없음 — 'TASK: Draw a single narrative scene...' 필수")

    # Check 1b: [thinking: low/medium] 금지
    m = THINKING_LOW_PATTERN.search(image_prompt)
    if m:
        add("ERROR", "THINKING_LEVEL_INVALID",
            f"'{m.group()}' 사용 불가 — NB2 API는 [thinking: high]만 지원")

    # Check 2: [SCENE] block
    if not SCENE_BLOCK_PATTERN.search(image_prompt):
        add("ERROR", "SCENE_BLOCK_MISSING",
            "[SCENE] block 없음 — 서술형 포맷 필수")

    # Check 3: [MUST] block
    if not MUST_BLOCK_PATTERN.search(image_prompt):
        add("ERROR", "MUST_BLOCK_MISSING",
            "[MUST] block 없음 — 정밀 제어 항목 필수")
    else:
        must_match = MUST_BLOCK_PATTERN.search(image_prompt)
        must_text = image_prompt[must_match.end():]
        must_items = MUST_ITEM_PATTERN.findall(must_text)
        if len(must_items) > 5:
            add("ERROR", "MUST_OVER_LIMIT",
                f"[MUST] 항목 {len(must_items)}개 — 최대 5개 초과")

    # Check 4: SOURCE REFERENCES + REDRAW
    src_ref_match = SOURCE_REF_BLOCK_PATTERN.search(image_prompt)
    src_ref_section = src_ref_match.group(1) if src_ref_match else ""
    has_char_source = "[CHARACTER SOURCE]" in src_ref_section or "[CHARACTER SOURCE:" in src_ref_section
    has_base_body = "[BASE BODY REFERENCE]" in src_ref_section
    has_obj_source = "[OBJECT SOURCE]" in src_ref_section
    has_any_source = has_char_source or has_base_body or has_obj_source

    if has_any_source and not REDRAW_PATTERN.search(image_prompt):
        add("ERROR", "REDRAW_MISSING",
            "REDRAW 항목 없음 — SOURCE REFERENCE 있을 때 [MUST]에 REDRAW 필수")

    # Check 5: 상호 배타
    if has_char_source and has_base_body:
        if "[CHARACTER SOURCE:" not in src_ref_section:
            add("ERROR", "REF_CONFLICT",
                "[CHARACTER SOURCE] + [BASE BODY REFERENCE] 동시 포함 — 상호 배타 위반")

    # Check 6: deprecated identifier
    match = DEPRECATED_ID_PATTERN.search(image_prompt)
    if match:
        add("ERROR", "DEPRECATED_IDENTIFIER",
            f"deprecated identifier: '{match.group()}' → 'THIS CAPPED' 등 간결 고유명사로 수정")

    # Check 7: has_human ↔ SOURCE REFERENCES
    if has_human and not has_char_source and not has_base_body:
        add("ERROR", "HAS_HUMAN_NO_REF",
            "has_human:main/anonym이지만 SOURCE REFERENCES에 CHARACTER/BASE BODY 없음 → 리얼 사람 생성 위험")

    # Check 8: 배경 [MUST]
    if not BACKGROUND_MUST_PATTERN.search(image_prompt):
        add("WARNING", "BACKGROUND_MUST",
            "[MUST]에 배경 bare white canvas 항목 누락")

    # Check 9: 스타일 앵커
    scene_match = SCENE_BLOCK_PATTERN.search(image_prompt)
    must_match2 = MUST_BLOCK_PATTERN.search(image_prompt)
    scene_text = ""
    if scene_match:
        start = scene_match.end()
        end = must_match2.start() if must_match2 else len(image_prompt)
        scene_text = image_prompt[start:end]

    if scene_text and not STYLE_ANCHOR_PATTERN.search(scene_text):
        add("WARNING", "STYLE_ANCHOR",
            "[SCENE] HOW줄에 스타일 앵커 문구 누락 ('Fine trembling ink lines...')")

    # Check 10: 얼굴 [MUST]
    if has_human and not FACE_MUST_PATTERN.search(image_prompt):
        add("WARNING", "FACE_MUST_MISSING",
            "has_human:main인데 [MUST]에 얼굴 규칙 누락 (dot eyes + NO nose)")

    # Check 11: 캐릭터 점유율 %
    if has_human and scene_text and not SIZE_PERCENT_PATTERN.search(scene_text):
        add("WARNING", "SIZE_PERCENT_MISSING",
            "[SCENE]에 캐릭터 프레임 점유율(%) 미명시")

    # Check 12: Style Isolation
    if scene_text:
        for kw in STYLE_ISOLATION_KEYWORDS:
            if kw.lower() in scene_text.lower():
                add("WARNING", "STYLE_ISOLATION",
                    f"[SCENE]에 금지 스타일 표현: '{kw}'")
                break

    # Check 13: 품질 접미사
    quality_match = QUALITY_SUFFIX_PATTERN.search(image_prompt)
    if quality_match:
        add("ERROR", "QUALITY_SUFFIX",
            f"품질 접미사 사용 금지: '{quality_match.group()}'")

    # Check 14: emotion_tag → 표정 표현
    if check_emotion and has_human and emotion_tag in EMOTION_EXPRESSION_PATTERNS:
        pattern = EMOTION_EXPRESSION_PATTERNS[emotion_tag]
        if scene_text and not pattern.search(scene_text):
            if not pattern.search(image_prompt):
                add("WARNING", "EMOTION_EXPR_MISSING",
                    f"emotion_tag '{emotion_tag}'에 대한 표정 표현이 [SCENE]에 없음")

    # Check 15: has_human:none인데 사람 형태
    human_body_keywords = ["hand", "palm", "fist", "arm", "finger", "scholar", "person", "figure standing"]
    if not has_human and scene_text:
        for kw in human_body_keywords:
            if kw in scene_text.lower():
                add("WARNING", "HUMAN_BODY_IN_NONE",
                    f"has_human:none이지만 [SCENE]에 '{kw}' 키워드 → has_human:main/anonym 필요 가능성")
                break

    return issues


# ─── 통합 검증 (버전 자동 감지) ──────────────────────────────────────────────

def validate_image_prompt_file(
    path: Path, check_emotion: bool = False, strict: bool = False
) -> list[dict]:
    """단일 Shot 파일의 image_prompt 검증. 버전 자동 감지."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return [{"level": "ERROR", "check": "READ_ERROR", "message": str(e), "file": str(path)}]

    version = detect_prompt_version(content)
    if version == "v3":
        return validate_v3_image_prompt(path, check_emotion, strict)
    else:
        return validate_v2_image_prompt(path, check_emotion, strict)


# ─── 디렉토리 검증 ────────────────────────────────────────────────────────────

def validate_directory(
    source_dir: Path,
    check_emotion: bool,
    section_filter: str | None,
    strict: bool,
) -> None:
    if not source_dir.exists():
        print(f"[오류] 경로가 존재하지 않습니다: {source_dir}")
        sys.exit(1)

    pattern = "**/*.md" if not section_filter else f"{section_filter}/*.md"
    shot_files = sorted(source_dir.glob(pattern))

    if not shot_files:
        print(f"[경고] Shot 파일을 찾지 못했습니다: {source_dir}/{pattern}")
        return

    all_issues = []
    v3_count = 0
    v2_count = 0

    for shot_path in shot_files:
        if shot_path.name in ("ANCHOR.md", "index.md"):
            continue
        try:
            content = shot_path.read_text(encoding="utf-8")
            ver = detect_prompt_version(content)
            if ver == "v3":
                v3_count += 1
            else:
                v2_count += 1
        except Exception:
            pass
        issues = validate_image_prompt_file(shot_path, check_emotion, strict)
        all_issues.extend(issues)

    errors = [i for i in all_issues if i["level"] == "ERROR"]
    warnings = [i for i in all_issues if i["level"] == "WARNING"]

    print(f"\n=== image_prompt 구조 검증 결과 (듀얼 모드: v3={v3_count}, v2={v2_count}) ===")
    print(f"대상 경로: {source_dir}")
    print(f"감정 표정 체크: {'ON (07 모드)' if check_emotion else 'OFF (06 모드)'}")
    print(f"총 파일 수: {len(shot_files)}개")
    print(f"오류: {len(errors)}건 | 경고: {len(warnings)}건\n")

    if errors:
        print("--- 오류 (ERROR) ---")
        for issue in errors:
            try:
                rel = Path(issue["file"]).relative_to(PROJECT_ROOT)
            except ValueError:
                rel = issue["file"]
            print(f"  [{rel}] [{issue['check']}] {issue['message']}")

    if warnings:
        print("\n--- 경고 (WARNING) ---")
        for issue in warnings:
            try:
                rel = Path(issue["file"]).relative_to(PROJECT_ROOT)
            except ValueError:
                rel = issue["file"]
            print(f"  [{rel}] [{issue['check']}] {issue['message']}")

    if not all_issues:
        print("모든 image_prompt 구조 정상 [OK]")

    if errors or (strict and warnings):
        sys.exit(1)


# ─── 매니페스트 읽기 ──────────────────────────────────────────────────────────

def _read_manifest(project_root: Path):
    manifest_path = project_root / "version_manifest.yaml"
    if not manifest_path.exists():
        return None, None
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    current_run = manifest.get("current_run")
    runs = manifest.get("runs", {})
    if isinstance(runs, dict):
        run_data = runs.get(current_run, {})
        sections = run_data.get("sections", None)
    elif isinstance(runs, list) and runs:
        sections = runs[-1].get("sections", None)
    else:
        sections = None
    return current_run, sections


# ─── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="image_prompt 내부 구조 자동 검증 (v2/v3 듀얼 모드) — merge_records.py 실행 전 의무 실행"
    )
    parser.add_argument(
        "--source",
        choices=["05", "06"],
        default="06",
        help="검증 대상 단계: 06=visual_direction(delta), 07=shot_records(merged, 기본)",
    )
    parser.add_argument("--section", default=None, help="특정 Section만 검증")
    parser.add_argument("--strict", action="store_true", help="경고도 오류로 처리 (exit 1)")
    parser.add_argument("--project", default=None, help="프로젝트 코드 (매니페스트 모드)")
    parser.add_argument("--run", default=None, help="특정 run ID")
    args = parser.parse_args()

    stage_map = {
        "05": "05_visual_direction",
        "06": "07_shot_records",
    }

    check_emotion = args.source == "06"

    if args.project:
        workspace_root = SCRIPT_DIR.parents[3]
        project_root = workspace_root / "projects" / args.project
        current_run, _ = _read_manifest(project_root)

        if current_run:
            run_id = args.run or current_run
            source_dir = project_root / stage_map[args.source] / run_id
        else:
            source_dir = project_root / stage_map[args.source] / "v1"
    else:
        source_map = {
            "05": PROJECT_ROOT / "05_visual_direction" / "v1",
            "06": PROJECT_ROOT / "07_shot_records" / "v1",
        }
        source_dir = source_map[args.source]

    validate_directory(source_dir, check_emotion, args.section, args.strict)


if __name__ == "__main__":
    main()
