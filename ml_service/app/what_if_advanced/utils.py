"""Utility functions for advanced what-if analyzer."""
from typing import List, Dict, Any
import re


def extract_scene_heading(scene_text: str) -> str:
    """Extract scene heading (INT/EXT location)."""
    lines = scene_text.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith(("INT.", "EXT.", "INT/EXT")):
            return line
    return "UNKNOWN"


def extract_location_from_heading(heading: str) -> str:
    """Extract location from scene heading."""
    match = re.match(r"(?:INT\.|EXT\.|INT/EXT)\s+([A-Z\s]+?)(?:\s*-\s*|\n|$)", heading)
    if match:
        return match.group(1).strip()
    return "UNKNOWN"


def extract_character_names(scene_text: str) -> List[str]:
    """Extract character names from scene (simple regex approach)."""
    pattern = r'^([A-Z][A-Z\s]+?)(?:\s*\(|:)'
    characters = set()

    for line in scene_text.split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            char_name = match.group(1).strip()
            if len(char_name) > 1 and not char_name.startswith(("INT", "EXT")):
                characters.add(char_name)

    return list(characters)


def count_words(text: str) -> int:
    """Count words in text."""
    return len(re.findall(r'\b\w+\b', text))


def merge_scenes(scenes: List[Dict[str, Any]], scene_ids: List[int]) -> Dict[str, Any]:
    """Merge multiple scenes into one."""
    scenes_to_merge = [s for s in scenes if s.get("scene_id") in scene_ids]

    if not scenes_to_merge:
        raise ValueError("No scenes found with given IDs")

    merged_text = "\n\n".join([s["text"] for s in scenes_to_merge])

    all_characters = set()
    for s in scenes_to_merge:
        all_characters.update(s.get("characters", []))

    return {
        "scene_id": min(scene_ids),
        "text": merged_text,
        "characters": list(all_characters),
        "merged_from": scene_ids,
    }


def split_scene(scene: Dict[str, Any], split_at_line: int) -> List[Dict[str, Any]]:
    """Split a scene into two at specified line number."""
    lines = scene["text"].split("\n")

    if split_at_line <= 0 or split_at_line >= len(lines):
        raise ValueError("Invalid split line number")

    first_part = "\n".join(lines[:split_at_line])
    second_part = "\n".join(lines[split_at_line:])

    return [
        {
            **scene,
            "scene_id": scene["scene_id"],
            "text": first_part,
        },
        {
            **scene,
            "scene_id": scene["scene_id"] + 1,
            "text": second_part,
        },
    ]


def estimate_screen_time(scene_text: str, words_per_minute: int = 150) -> float:
    """Estimate scene screen time in minutes based on word count."""
    word_count = count_words(scene_text)
    return word_count / words_per_minute


def get_modification_summary(modifications_applied: List[Dict[str, Any]]) -> str:
    """Generate human-readable summary of applied modifications."""
    if not modifications_applied:
        return "No modifications applied"

    summary_parts = []
    for mod in modifications_applied:
        mod_type = mod.get("type", "unknown")
        metadata = mod.get("metadata", {})

        if "error" in mod:
            summary_parts.append(f"❌ {mod_type}: {mod['error']}")
        else:
            key_info = []
            for key in ["removed_count", "total_replacements", "scenes_modified", "replacements"]:
                if key in metadata:
                    key_info.append(f"{key}={metadata[key]}")

            if key_info:
                summary_parts.append(f"✓ {mod_type}: {', '.join(key_info)}")
            else:
                summary_parts.append(f"✓ {mod_type}")

    return "\n".join(summary_parts)


def validate_modification_config(config: Dict[str, Any]) -> bool:
    """Validate modification configuration."""
    required_fields = ["type"]
    return all(field in config for field in required_fields)
