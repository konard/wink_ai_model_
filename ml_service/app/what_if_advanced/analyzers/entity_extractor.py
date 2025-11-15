import re
from typing import Dict, List, Any
from collections import defaultdict
from loguru import logger

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available, using fallback entity extraction")


class EntityExtractor:
    """Extract entities (characters, locations, objects) from script scenes."""

    def __init__(self):
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found, using fallback")

    def extract_entities(self, scenes: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
        """Extract entities from all scenes."""
        if self.nlp:
            return self._extract_with_spacy(scenes)
        else:
            return self._extract_fallback(scenes)

    def _extract_with_spacy(self, scenes: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
        """Use spaCy NER for entity extraction."""
        entities = {
            "characters": defaultdict(lambda: {"mentions": 0, "scenes": set()}),
            "locations": defaultdict(lambda: {"mentions": 0, "scenes": set()}),
            "objects": defaultdict(lambda: {"mentions": 0, "scenes": set()}),
        }

        for scene in scenes:
            doc = self.nlp(scene["text"])
            scene_id = scene.get("scene_id", 0)

            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    entities["characters"][ent.text]["mentions"] += 1
                    entities["characters"][ent.text]["scenes"].add(scene_id)
                elif ent.label_ in ["GPE", "LOC", "FAC"]:
                    entities["locations"][ent.text]["mentions"] += 1
                    entities["locations"][ent.text]["scenes"].add(scene_id)
                elif ent.label_ in ["PRODUCT", "ORG"]:
                    entities["objects"][ent.text]["mentions"] += 1
                    entities["objects"][ent.text]["scenes"].add(scene_id)

        result = {}
        for entity_type, entity_dict in entities.items():
            result[entity_type] = [
                {
                    "type": entity_type[:-1],
                    "name": name,
                    "mentions": data["mentions"],
                    "scenes": sorted(list(data["scenes"])),
                }
                for name, data in entity_dict.items()
            ]
            result[entity_type].sort(key=lambda x: x["mentions"], reverse=True)

        return result

    def _extract_fallback(self, scenes: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
        """Fallback entity extraction using regex patterns."""
        entities = {
            "characters": defaultdict(lambda: {"mentions": 0, "scenes": set()}),
            "locations": defaultdict(lambda: {"mentions": 0, "scenes": set()}),
            "objects": defaultdict(lambda: {"mentions": 0, "scenes": set()}),
        }

        character_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b(?=\s*:|\s+says|\s+yells|\s+whispers)'
        location_pattern = r'(?:INT\.|EXT\.)\s+([A-Z\s]+?)(?:\s*-\s*|\n)'

        for scene in scenes:
            text = scene["text"]
            scene_id = scene.get("scene_id", 0)

            for match in re.finditer(character_pattern, text):
                char_name = match.group(1)
                entities["characters"][char_name]["mentions"] += 1
                entities["characters"][char_name]["scenes"].add(scene_id)

            for match in re.finditer(location_pattern, text):
                location = match.group(1).strip()
                entities["locations"][location]["mentions"] += 1
                entities["locations"][location]["scenes"].add(scene_id)

        result = {}
        for entity_type, entity_dict in entities.items():
            result[entity_type] = [
                {
                    "type": entity_type[:-1],
                    "name": name,
                    "mentions": data["mentions"],
                    "scenes": sorted(list(data["scenes"])),
                }
                for name, data in entity_dict.items()
                if data["mentions"] >= 2
            ]
            result[entity_type].sort(key=lambda x: x["mentions"], reverse=True)

        return result

    def filter_entities_by_target(
        self, entities: Dict[str, List[Any]], target_type: str, target_names: List[str]
    ) -> List[Any]:
        """Filter entities by type and names."""
        if target_type == "all":
            all_entities = []
            for entity_list in entities.values():
                all_entities.extend(entity_list)
            return all_entities

        entity_list = entities.get(f"{target_type}s", [])

        if target_names:
            return [e for e in entity_list if e["name"] in target_names]

        return entity_list
