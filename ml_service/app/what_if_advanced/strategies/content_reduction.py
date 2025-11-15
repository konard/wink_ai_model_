from typing import Dict, Any, List, Tuple
import re
from .base import ModificationStrategy


class ContentReductionStrategy(ModificationStrategy):
    """Reduce intensity of violent, profane, or sexual content using text replacements."""

    def __init__(self):
        super().__init__()

        self.default_replacements = {
            "violence": {
                "kill": "confront",
                "shoot": "point at",
                "stab": "threaten",
                "murder": "argue with",
                "attack": "approach",
                "beating": "pushing",
                "fight": "argue",
                "punch": "push",
                "kick": "shove",
                "убить": "противостоять",
                "убийство": "конфликт",
                "стрелять": "направить на",
                "зарезать": "угрожать",
                "атаковать": "приблизиться",
                "избиение": "толкание",
                "драка": "спор",
            },
            "profanity": {
                r"\bfuck\w*\b": "darn",
                r"\bshit\b": "crap",
                r"\bmotherfucker\b": "jerk",
                r"\bbitch\b": "witch",
                r"\basshole\b": "idiot",
                r"\bблядь\b": "черт",
                r"\bбля\b": "блин",
                r"\bсука\b": "зараза",
                r"\bхуй\w*\b": "черт",
                r"\bпизд\w*\b": "черт",
                r"\bебать\b": "черт",
                r"\bебал\w*\b": "черт",
            },
            "gore": {
                "blood": "mark",
                "bloody": "marked",
                "bleeding": "injured",
                "wound": "injury",
                "guts": "injury",
                "кровь": "след",
                "кровавый": "помеченный",
                "кровоточ": "ранен",
                "рана": "повреждение",
            },
            "sexual": {
                r"\brape\b": "assault",
                r"\bsex scene\b": "romantic scene",
                r"\bnaked\b": "undressed",
                r"\bnude\b": "unclothed",
                r"\bизнасилов\w*\b": "напад",
                r"\bсексуальн\w*\b": "романтическ",
                r"\bголый\b": "раздетый",
                r"\bголая\b": "раздетая",
            },
            "drugs": {
                r"\bheroin\b": "substance",
                r"\bcocaine\b": "substance",
                r"\bmarijuana\b": "substance",
                r"\bгероин\b": "вещество",
                r"\bкокаин\b": "вещество",
                r"\bмарихуан\w*\b": "вещество",
            },
        }

    def can_handle(self, modification_type: str) -> bool:
        return modification_type in [
            "reduce_violence",
            "reduce_profanity",
            "reduce_gore",
            "reduce_sexual",
            "reduce_drugs",
            "reduce_content",
        ]

    def apply(
        self,
        scenes: List[Dict[str, Any]],
        params: Dict[str, Any],
        entities: Dict[str, List[Any]],
        **kwargs
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Reduce content intensity by replacing words/phrases.

        Params:
            content_types: List[str] - types to reduce (violence, profanity, gore, sexual, drugs)
            custom_replacements: Dict[str, str] - custom word replacements
            scope: List[int] - scene IDs to apply to (if None, apply to all)
            target_characters: List[str] - only modify scenes with these characters
        """
        content_types = params.get("content_types", ["violence", "profanity"])
        custom_replacements = params.get("custom_replacements", {})
        scope = params.get("scope")
        target_characters = params.get("target_characters")

        replacements = custom_replacements.copy()
        for content_type in content_types:
            if content_type in self.default_replacements:
                replacements.update(self.default_replacements[content_type])

        modified_scenes = []
        total_replacements = 0

        for scene in scenes:
            scene_id = scene.get("scene_id", 0)

            if scope and scene_id not in scope:
                modified_scenes.append(scene)
                continue

            if target_characters:
                scene_chars = set(scene.get("characters", []))
                if not (scene_chars & set(target_characters)):
                    modified_scenes.append(scene)
                    continue

            modified_text, count = self._apply_replacements(scene["text"], replacements)
            total_replacements += count

            modified_scene = scene.copy()
            modified_scene["text"] = modified_text
            modified_scenes.append(modified_scene)

        metadata = {
            "content_types_reduced": content_types,
            "total_replacements": total_replacements,
            "scenes_modified": sum(1 for s in modified_scenes if s["text"] != scenes[modified_scenes.index(s)]["text"]),
        }

        return modified_scenes, metadata

    def _apply_replacements(self, text: str, replacements: Dict[str, str]) -> Tuple[str, int]:
        """Apply all replacements to text."""
        modified_text = text
        count = 0

        for pattern, replacement in replacements.items():
            if r"\b" in pattern or pattern.startswith(r"\b"):
                matches = re.findall(pattern, modified_text, re.I)
                count += len(matches)
                modified_text = re.sub(pattern, replacement, modified_text, flags=re.I)
            else:
                pattern_regex = r"\b" + re.escape(pattern) + r"\w*"
                matches = re.findall(pattern_regex, modified_text, re.I)
                count += len(matches)
                modified_text = re.sub(pattern_regex, replacement, modified_text, flags=re.I)

        return modified_text, count

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate parameters."""
        if "content_types" in params:
            valid_types = {"violence", "profanity", "gore", "sexual", "drugs"}
            return all(ct in valid_types for ct in params["content_types"])
        return True
