#!/usr/bin/env python3
"""
STEP 06 Audio Director - Audio Delta Generator
Reads STEP 04 shot composition files and generates STEP 06 audio narration deltas
"""

import os
import sys
import yaml
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configuration
PROJECT_CODE = "CH03"
RUN_ID = "run003"
VOICE_ID = "Liam"
ELEVENLABS_MODEL = "Eleven v3"

# Section BGM templates (§5)
SECTION_BGM = {
    "TITLECARD": {
        "bgm": "ambient solo piano | BPM 78 | Low-Mid",
        "el_prompt": 'ambient solo piano, 78 BPM, slow reflective arpeggios, sparse and curious, quiet, lo-fi, loop'
    },
    "SECTION00_HOOK": {
        "bgm": "ambient solo piano | BPM 78 | Low-Mid",
        "el_prompt": 'ambient solo piano, 78 BPM, slow reflective arpeggios, sparse and curious, quiet, lo-fi, loop'
    },
    "SECTION01": {
        "bgm": "ambient strings | BPM 72 | Low",
        "el_prompt": 'ambient strings, 72 BPM, gentle warm cello and violin layers, contemplative, emotional, loop'
    },
    "SECTION02": {
        "bgm": "acoustic folk piano | BPM 82 | Mid",
        "el_prompt": 'acoustic folk piano and light guitar, 82 BPM, warm gentle arpeggios, Yann Tiersen style, loop'
    },
    "SECTION03": {
        "bgm": "post-rock strings | BPM 90 | Mid-High",
        "el_prompt": 'post-rock strings, 90 BPM, hopeful building swell, light brush percussion, inspiring, loop'
    },
    "SECTION04_OUTRO": {
        "bgm": "ambient pad | BPM 65 | Low",
        "el_prompt": 'ambient pad with reverb piano notes, 65 BPM, spacious and atmospheric, Brian Eno style, loop'
    },
}

# Emotion tag to EL narration mapping (§6)
EMOTION_MAPPING = {
    "HUMOR": {
        "el_tone": "[EARNEST]/[PLAYFULLY] (tension-release rule)",
        "volume_mix": "Narration 100% / BGM 20% / SFX 60%"
    },
    "REFLECTIVE": {
        "el_tone": "[REFLECTIVE]",
        "volume_mix": "Narration 100% / BGM 15% / SFX 0%"
    },
    "AWE": {
        "el_tone": "[AWE]/[WISTFUL]",
        "volume_mix": "Narration 100% / BGM 30% / SFX 70%"
    },
    "REVEAL": {
        "el_tone": "[CONTEMPLATIVE]/[EARNEST]",
        "volume_mix": "Narration 100% / BGM 20% / SFX 60%"
    },
    "TENSION": {
        "el_tone": "[SERIOUS TONE]/[DRAMATIC TONE]",
        "volume_mix": "Narration 100% / BGM 30% / SFX 70%"
    }
}

def convert_pause(text):
    """Convert [PAUSE: Xs] tags to EL pause notation"""
    # Pattern: [PAUSE: duration]
    pause_pattern = r'\[PAUSE:\s*([^]]+)\]'

    def replace_pause(match):
        duration_str = match.group(1).strip()
        # Parse duration
        if '~' in duration_str:
            # Range like 1~1.5초
            return "... [PAUSES]"
        elif '2초+' in duration_str or '2초 +' in duration_str:
            # Long pause - separate line
            return "... ... [PAUSES]"
        elif '2' in duration_str:
            return "... ... [PAUSES]"
        else:
            return "... [PAUSES]"

    return re.sub(pause_pattern, replace_pause, text)

def extract_yaml_content(file_text):
    """Extract YAML content from markdown file"""
    # Find content between ```yaml and ```
    yaml_match = re.search(r'```yaml\n(.*?)\n```', file_text, re.DOTALL)
    if yaml_match:
        return yaml_match.group(1)
    return None

def read_shot_file(file_path):
    """Read and parse a shot file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        yaml_content = extract_yaml_content(content)
        if not yaml_content:
            return None

        # Remove leading --- and parse
        yaml_content = yaml_content.lstrip('---').strip()
        shot_data = yaml.safe_load(yaml_content)
        return shot_data
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def get_scene_id(shot_id, emotion_tag, narration_span, section):
    """Assign scene_id based on narration paragraph boundaries"""
    # For no-narration shots, scene_id = 0
    if "(없음)" in str(narration_span) or "(PAUSE)" in str(narration_span) or narration_span.strip() == "" or narration_span is None:
        return 0
    # For secondary narrator shots, assign unique scene_id
    if "[보조]" in str(narration_span):
        return shot_id  # Each gets unique id
    # Otherwise, scene_id groups multiple shots by narration paragraph
    # Simplification: use shot_id as base scene grouping
    return (shot_id // 3) * 3 if shot_id > 0 else 1

def generate_el_narration(shot_data, section):
    """Generate EL narration based on emotion_tag and narration_span"""
    narration_span = shot_data.get('narration_span', '').strip()
    emotion_tag = shot_data.get('emotion_tag', 'REFLECTIVE')
    has_human = shot_data.get('has_human', 'none')

    # Handle no-narration shots
    if not narration_span or "(없음)" in narration_span or "(PAUSE)" in narration_span:
        return "(없음)"

    # Handle song hook shots
    if section == "SECTION00_HOOK" and shot_data.get('hook_type') == 'song':
        return "(Song Hook — Suno 음원으로 대체)"

    # Handle secondary narrator
    if "[보조]" in narration_span:
        # Extract secondary narrator text and add voice tag
        text = narration_span.replace("[보조]", "").strip()
        return f"[보조 음성] {text}"

    # Apply EL tone tags based on emotion
    if emotion_tag == "TENSION":
        el_tone = "[SERIOUS TONE]"
    elif emotion_tag == "REVEAL":
        el_tone = "[EARNEST]"
    elif emotion_tag == "AWE":
        el_tone = "[AWE]"
    elif emotion_tag == "REFLECTIVE":
        el_tone = "[REFLECTIVE]"
    elif emotion_tag == "HUMOR":
        # HUMOR rule: setup with [EARNEST], punch with [PLAYFULLY] only on last sentence
        sentences = narration_span.split('.')
        if len(sentences) > 1:
            # Multi-sentence: first = EARNEST, last = PLAYFULLY
            el_tone = "[EARNEST]"  # Setup
            # We'll need to add [PLAYFULLY] to last sentence
            text = ". ".join([s.strip() for s in sentences[:-1] if s.strip()])
            last = sentences[-1].strip()
            if last:
                text += ". [PLAYFULLY] " + last
            return f"{el_tone} {text.lstrip()}"
        else:
            # Single sentence: use SERIOUS TONE
            el_tone = "[SERIOUS TONE]"
    else:
        el_tone = "[CONVERSATIONAL TONE]"

    # Convert PAUSE tags
    narration = convert_pause(narration_span)

    # Apply tone tag at sentence start
    if not narration.startswith('['):
        narration = f"{el_tone} {narration}"

    return narration

def generate_bgm(section, emotion_tag):
    """Generate BGM specification"""
    section_bgm = SECTION_BGM.get(section, SECTION_BGM["SECTION01"])
    bgm_base = section_bgm["bgm"]
    el_prompt = section_bgm["el_prompt"]

    # Emotion modulation (§6)
    if emotion_tag == "HUMOR":
        # Energy +10~15%, bright chord shift
        energy_note = " + energy +10%, bright chord shift"
    elif emotion_tag == "REFLECTIVE":
        # Reduce energy 20~30%, solo instrument
        energy_note = " - energy 20%, reduce to solo instrument"
    elif emotion_tag == "AWE":
        # Energy +20~30% swell, add sustained pad
        energy_note = " + energy +25%, add sustained pad"
    elif emotion_tag == "REVEAL":
        # 0.5s micro-dip then resume
        energy_note = " (0.5s micro-dip then resume)"
    elif emotion_tag == "TENSION":
        # Energy +10%, emphasize low bass
        energy_note = " + energy +10%, emphasize low bass"
    else:
        energy_note = ""

    return f"{bgm_base}{energy_note} | EL: \"{el_prompt}\""

def generate_volume_mix(emotion_tag, narration_is_present):
    """Generate volume_mix specification"""
    if not narration_is_present:
        # No narration - transition/breath
        return "Narration 0% / BGM 50% / SFX 90%"

    # Emotion-based defaults from §6
    if emotion_tag == "HUMOR":
        return "Narration 100% / BGM 20% / SFX 60%"
    elif emotion_tag == "REFLECTIVE":
        return "Narration 100% / BGM 15% / SFX 0%"
    elif emotion_tag == "AWE":
        return "Narration 100% / BGM 30% / SFX 70%"
    elif emotion_tag == "REVEAL":
        return "Narration 100% / BGM 20% / SFX 60%"
    elif emotion_tag == "TENSION":
        return "Narration 100% / BGM 30% / SFX 70%"
    else:
        return "Narration 100% / BGM 20% / SFX 60%"

def create_audio_delta(shot_data, section, voice_id):
    """Create audio delta YAML"""
    shot_id = shot_data.get('shot_id')
    emotion_tag = shot_data.get('emotion_tag', 'REFLECTIVE')
    narration_span = shot_data.get('narration_span', '').strip()
    hook_type = shot_data.get('hook_type', 'standard')

    # Handle Song Hook shots specially
    if section == "SECTION00_HOOK" and hook_type == 'song':
        return generate_song_hook_delta(shot_data, section, voice_id)

    scene_id = get_scene_id(shot_id, emotion_tag, narration_span, section)
    el_narration = generate_el_narration(shot_data, section)
    narration_present = el_narration != "(없음)"
    bgm = generate_bgm(section, emotion_tag)
    volume_mix = generate_volume_mix(emotion_tag, narration_present)

    delta = {
        'shot_id': shot_id,
        'scene_id': scene_id,
        'el_narration': el_narration,
        'bgm': bgm,
        'volume_mix': volume_mix
    }

    return delta

def generate_song_hook_delta(shot_data, section, voice_id):
    """Generate delta for Song Hook shots"""
    shot_id = shot_data.get('shot_id')

    suno_lyrics = """[verse]
달리자, 달려, 더 빨리
레일을 따라 온 힘을 다해
연기 속에 사라지기 전에
더 빨리, 더 빨리

[chorus]
모두가 환호한다
세상이 좁아진다
기차가 지나간 자리
무언가 남는다

[bridge]
근데, 그게 뭔지 알고 있어?

[End]"""

    delta = {
        'shot_id': shot_id,
        'scene_id': 1 if shot_id < 6 else 0,  # Group all song shots together
        'el_narration': '(Song Hook — Suno 음원으로 대체)',
        'bgm': '(Song Hook — Suno 음원에 포함)',
        'volume_mix': 'Song 100% / BGM 0% / SFX 60%',
        'suno_style': 'Acoustic singer-songwriter; comedic folk; mid-tempo 130 BPM; playful; warm guitar; lo-fi intimate; harp-like piano; pencil sketch texture',
        'suno_lyrics': suno_lyrics,
        'suno_params': {
            'instrumental': False,
            'negative_tags': 'heavy metal, electronic auto-tune, screaming, aggressive distortion, modern pop, EDM, classical orchestral, dubstep'
        }
    }

    return delta

def format_audio_delta_file(shot_data, delta, section, voice_id):
    """Format audio delta as markdown file"""
    shot_id = shot_data.get('shot_id')
    section_bgm = SECTION_BGM.get(section, SECTION_BGM["SECTION01"])

    header = f"""# shot{shot_id:02d}.md
SECTION: {section}
SHOT_ID: {shot_id}
INPUT_REF: 04_shot_composition/{RUN_ID}/{section}/shot{shot_id:02d}.md
MODEL: claude-haiku
ELEVENLABS_MODEL: {ELEVENLABS_MODEL}
VOICE_ID: {voice_id}
SECTION_BGM: {section_bgm["bgm"]}
CREATED: {datetime.now().strftime('%Y-%m-%d')}

---

```yaml
---
"""

    # Format YAML delta
    yaml_lines = []
    for key in ['shot_id', 'scene_id', 'el_narration', 'bgm', 'volume_mix', 'suno_style', 'suno_lyrics', 'suno_params']:
        if key in delta:
            value = delta[key]
            if key == 'el_narration' and '\n' not in str(value):
                yaml_lines.append(f"{key}: {value}")
            elif key == 'suno_lyrics':
                yaml_lines.append(f"{key}: |")
                for line in value.split('\n'):
                    yaml_lines.append(f"  {line}")
            elif key == 'suno_params':
                yaml_lines.append(f"{key}:")
                yaml_lines.append(f"  instrumental: {str(value['instrumental']).lower()}")
                yaml_lines.append(f"  negative_tags: \"{value['negative_tags']}\"")
            elif key == 'suno_style':
                yaml_lines.append(f"{key}: \"{value}\"")
            else:
                yaml_lines.append(f"{key}: {value}")

    yaml_lines.append("---")

    footer = "```"

    return header + "\n".join(yaml_lines) + "\n" + footer

def main():
    """Main processing function"""
    base_path = Path(f"projects/{PROJECT_CODE}/04_shot_composition/{RUN_ID}")
    output_base = Path(f"projects/{PROJECT_CODE}/06_audio_narration/{RUN_ID}")

    sections = [
        "TITLECARD",
        "SECTION00_HOOK",
        "SECTION01",
        "SECTION02",
        "SECTION03",
        "SECTION04_OUTRO"
    ]

    total_shots = 0
    total_errors = 0

    for section in sections:
        section_path = base_path / section
        output_section = output_base / section

        # Create output directory
        output_section.mkdir(parents=True, exist_ok=True)

        # Find all shot files
        if section_path.exists():
            shot_files = sorted(section_path.glob("shot*.md"), key=lambda x: int(x.stem[4:]))

            print(f"\n[{section}] Processing {len(shot_files)} shots...")

            for shot_file in shot_files:
                shot_data = read_shot_file(shot_file)
                if shot_data is None:
                    print(f"  ✗ {shot_file.name} - Failed to read")
                    total_errors += 1
                    continue

                try:
                    # Generate audio delta
                    delta = create_audio_delta(shot_data, section, VOICE_ID)

                    # Format and write file
                    formatted = format_audio_delta_file(shot_data, delta, section, VOICE_ID)
                    shot_id = shot_data.get('shot_id')
                    output_file = output_section / f"shot{shot_id:02d}.md"

                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(formatted)

                    print(f"  ✓ shot{shot_id:02d}.md")
                    total_shots += 1

                except Exception as e:
                    print(f"  ✗ {shot_file.name} - {e}")
                    total_errors += 1
        else:
            print(f"[{section}] Not found: {section_path}")

    print(f"\n✅ Complete: {total_shots} audio delta files created")
    if total_errors:
        print(f"⚠️  {total_errors} errors")

if __name__ == "__main__":
    main()
