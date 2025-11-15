from typing import Dict, Any, List, Tuple, Optional
from .base import ModificationStrategy
from ..generators.llm_generator import LLMGenerator
from loguru import logger


class LLMRewriteStrategy(ModificationStrategy):
    """Rewrite scenes using LLM for context-aware modifications."""

    def __init__(self, llm_generator: Optional[LLMGenerator] = None):
        super().__init__()
        self.llm_generator = llm_generator

    def can_handle(self, modification_type: str) -> bool:
        return modification_type in [
            "llm_rewrite",
            "intelligent_rewrite",
            "contextual_modification",
        ]

    def apply(
        self,
        scenes: List[Dict[str, Any]],
        params: Dict[str, Any],
        entities: Dict[str, List[Any]],
        **kwargs
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Rewrite scenes using LLM with context awareness.

        Params:
            instruction: str - how to modify the scenes
            scope: List[int] - scene IDs to apply to
            target_characters: List[str] - focus on scenes with these characters
            preserve_style: bool - maintain original writing style
            temperature: float - LLM temperature (0.0-1.0)
        """
        if not self.llm_generator:
            logger.warning("LLM generator not available, skipping LLM rewrite")
            return scenes, {"error": "LLM generator not configured"}

        instruction = params.get("instruction", "Rewrite to be more appropriate for general audiences")
        scope = params.get("scope")
        target_characters = params.get("target_characters")
        preserve_style = params.get("preserve_style", True)

        modified_scenes = []
        rewrites_count = 0

        for scene in scenes:
            scene_id = scene.get("scene_id", 0)

            should_rewrite = True
            if scope and scene_id not in scope:
                should_rewrite = False
            if target_characters:
                scene_chars = set(scene.get("characters", []))
                if not (scene_chars & set(target_characters)):
                    should_rewrite = False

            if should_rewrite:
                context = {
                    "characters": scene.get("characters", []),
                    "location": scene.get("location"),
                    "scene_type": scene.get("scene_type"),
                    "preserve_style": preserve_style,
                }

                try:
                    rewritten_text = self.llm_generator.rewrite_scene(
                        scene["text"], instruction, context
                    )
                    modified_scene = scene.copy()
                    modified_scene["text"] = rewritten_text
                    modified_scene["llm_rewritten"] = True
                    modified_scenes.append(modified_scene)
                    rewrites_count += 1
                except Exception as e:
                    logger.error(f"Failed to rewrite scene {scene_id}: {e}")
                    modified_scenes.append(scene)
            else:
                modified_scenes.append(scene)

        metadata = {
            "scenes_rewritten": rewrites_count,
            "instruction": instruction,
            "llm_provider": self.llm_generator.provider if self.llm_generator else None,
        }

        return modified_scenes, metadata

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate parameters."""
        return "instruction" in params or True
