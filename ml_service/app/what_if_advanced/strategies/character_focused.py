from typing import Dict, Any, List, Tuple
import re
from .base import ModificationStrategy


class CharacterFocusedStrategy(ModificationStrategy):
    """Modify content related to specific characters."""

    def can_handle(self, modification_type: str) -> bool:
        return modification_type in [
            "modify_character",
            "remove_character",
            "rename_character",
            "change_character_actions",
        ]

    def apply(
        self,
        scenes: List[Dict[str, Any]],
        params: Dict[str, Any],
        entities: Dict[str, List[Any]],
        **kwargs,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Apply character-focused modifications.

        Params:
            action: str - "remove", "rename", "modify_actions"
            character_name: str - target character
            new_name: str - new name (for rename action)
            remove_scenes: bool - remove scenes with this character
            action_replacements: Dict[str, str] - replace specific actions
        """
        action = params.get("action")
        character_name = params.get("character_name")

        if not character_name:
            return scenes, {"error": "character_name required"}

        if action == "remove":
            return self._remove_character(scenes, character_name, params)
        elif action == "rename":
            return self._rename_character(scenes, character_name, params)
        elif action == "modify_actions":
            return self._modify_character_actions(scenes, character_name, params)
        else:
            return scenes, {"error": f"Unknown action: {action}"}

    def _remove_character(
        self, scenes: List[Dict[str, Any]], character_name: str, params: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Remove character from script."""
        remove_scenes = params.get("remove_scenes", False)

        if remove_scenes:
            filtered_scenes = []
            removed_count = 0

            for scene in scenes:
                scene_chars = scene.get("characters", [])
                if character_name not in scene_chars:
                    filtered_scenes.append(scene)
                else:
                    removed_count += 1

            for idx, scene in enumerate(filtered_scenes):
                scene["scene_id"] = idx

            return filtered_scenes, {
                "action": "remove_character",
                "character": character_name,
                "scenes_removed": removed_count,
            }
        else:
            modified_scenes = []
            lines_removed = 0

            for scene in scenes:
                modified_text = self._remove_character_lines(
                    scene["text"], character_name
                )
                if modified_text != scene["text"]:
                    lines_removed += 1

                modified_scene = scene.copy()
                modified_scene["text"] = modified_text
                modified_scenes.append(modified_scene)

            return modified_scenes, {
                "action": "remove_character_lines",
                "character": character_name,
                "scenes_modified": lines_removed,
            }

    def _remove_character_lines(self, text: str, character_name: str) -> str:
        """Remove dialogue and action lines for a character."""
        lines = text.split("\n")
        filtered_lines: list[str] = []
        skip_next = False

        for i, line in enumerate(lines):
            if re.match(rf"^\s*{re.escape(character_name)}\s*[:.]", line, re.I):
                skip_next = True
                continue

            if (
                skip_next
                and line.strip()
                and not re.match(r"^\s*[A-Z][A-Z\s]+[:.]", line)
            ):
                skip_next = False
                continue

            skip_next = False
            filtered_lines.append(line)

        return "\n".join(filtered_lines)

    def _rename_character(
        self, scenes: List[Dict[str, Any]], character_name: str, params: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Rename character throughout script."""
        new_name = params.get("new_name")
        if not new_name:
            return scenes, {"error": "new_name required for rename action"}

        modified_scenes = []
        replacements_count = 0

        for scene in scenes:
            modified_text = scene["text"]

            pattern = r"\b" + re.escape(character_name) + r"\b"
            matches = len(re.findall(pattern, modified_text, re.I))
            replacements_count += matches

            modified_text = re.sub(pattern, new_name, modified_text, flags=re.I)

            modified_scene = scene.copy()
            modified_scene["text"] = modified_text

            if (
                "characters" in modified_scene
                and character_name in modified_scene["characters"]
            ):
                modified_scene["characters"] = [
                    new_name if c == character_name else c
                    for c in modified_scene["characters"]
                ]

            modified_scenes.append(modified_scene)

        return modified_scenes, {
            "action": "rename_character",
            "old_name": character_name,
            "new_name": new_name,
            "replacements": replacements_count,
        }

    def _modify_character_actions(
        self, scenes: List[Dict[str, Any]], character_name: str, params: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Modify specific actions performed by a character."""
        action_replacements = params.get("action_replacements", {})

        modified_scenes = []
        replacements_count = 0

        for scene in scenes:
            scene_chars = scene.get("characters", [])
            if character_name not in scene_chars:
                modified_scenes.append(scene)
                continue

            modified_text = scene["text"]

            for old_action, new_action in action_replacements.items():
                pattern = rf"({re.escape(character_name)}[^.]*?{re.escape(old_action)})"
                matches = len(re.findall(pattern, modified_text, re.I))
                replacements_count += matches

                modified_text = re.sub(
                    rf"\b{re.escape(old_action)}\b",
                    new_action,
                    modified_text,
                    flags=re.I,
                )

            modified_scene = scene.copy()
            modified_scene["text"] = modified_text
            modified_scenes.append(modified_scene)

        return modified_scenes, {
            "action": "modify_character_actions",
            "character": character_name,
            "actions_replaced": replacements_count,
        }

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate parameters."""
        required = {"action", "character_name"}
        return all(key in params for key in required)
