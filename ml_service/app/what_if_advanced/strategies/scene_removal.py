from typing import Dict, Any, List, Tuple
from .base import ModificationStrategy


class SceneRemovalStrategy(ModificationStrategy):
    """Remove specific scenes from the script."""

    def can_handle(self, modification_type: str) -> bool:
        return modification_type in ["remove_scenes", "delete_scenes"]

    def apply(
        self,
        scenes: List[Dict[str, Any]],
        params: Dict[str, Any],
        entities: Dict[str, List[Any]],
        **kwargs
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Remove scenes by ID or by criteria.

        Params:
            scene_ids: List[int] - specific scene IDs to remove
            scene_types: List[str] - remove scenes of these types
            characters: List[str] - remove scenes with these characters
            locations: List[str] - remove scenes in these locations
        """
        scenes_to_remove = set()

        if "scene_ids" in params:
            scenes_to_remove.update(params["scene_ids"])

        if "scene_types" in params:
            target_types = params["scene_types"]
            for scene in scenes:
                if scene.get("scene_type") in target_types:
                    scenes_to_remove.add(scene.get("scene_id", 0))

        if "characters" in params:
            target_chars = set(params["characters"])
            for scene in scenes:
                scene_chars = set(scene.get("characters", []))
                if scene_chars & target_chars:
                    scenes_to_remove.add(scene.get("scene_id", 0))

        if "locations" in params:
            target_locs = set(params["locations"])
            for scene in scenes:
                if scene.get("location") in target_locs:
                    scenes_to_remove.add(scene.get("scene_id", 0))

        original_count = len(scenes)
        filtered_scenes = [
            s for s in scenes if s.get("scene_id", 0) not in scenes_to_remove
        ]

        for idx, scene in enumerate(filtered_scenes):
            scene["scene_id"] = idx

        metadata = {
            "removed_count": original_count - len(filtered_scenes),
            "removed_scene_ids": sorted(list(scenes_to_remove)),
            "remaining_count": len(filtered_scenes),
        }

        return filtered_scenes, metadata

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate parameters."""
        valid_keys = {"scene_ids", "scene_types", "characters", "locations"}
        return any(key in params for key in valid_keys)
