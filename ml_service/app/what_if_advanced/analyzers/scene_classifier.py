from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer, util
from loguru import logger


class SceneClassifier:
    """Classify scenes into types using zero-shot classification."""

    def __init__(self, embedder: SentenceTransformer):
        self.embedder = embedder

        self.scene_type_templates = {
            "action": [
                "intense physical action and fighting",
                "chase sequence and pursuit",
                "combat and battle scenes",
                "explosive action and stunts",
            ],
            "dialogue": [
                "conversation between characters",
                "verbal exchange and discussion",
                "characters talking and interacting",
                "interpersonal communication",
            ],
            "exposition": [
                "introducing setting and context",
                "establishing story background",
                "world-building and explanation",
                "narrative setup and information",
            ],
            "emotional": [
                "character emotional moment",
                "dramatic and intense feelings",
                "personal revelation and vulnerability",
                "emotional climax and catharsis",
            ],
            "suspense": [
                "building tension and mystery",
                "creating anticipation and dread",
                "suspenseful and tense atmosphere",
                "thriller-like uncertainty",
            ],
            "romantic": [
                "romantic interaction between characters",
                "love and intimacy",
                "relationship development",
                "tender and affectionate moments",
            ],
            "comedic": [
                "humorous and funny situations",
                "comedy and lighthearted moments",
                "jokes and comic relief",
                "amusing character interactions",
            ],
        }

        self.type_embeddings = {}
        for scene_type, templates in self.scene_type_templates.items():
            embeddings = self.embedder.encode(templates, convert_to_numpy=True)
            self.type_embeddings[scene_type] = np.mean(embeddings, axis=0)

        logger.info(f"SceneClassifier initialized with {len(self.scene_type_templates)} scene types")

    def classify_scene(self, scene_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Classify a single scene into types."""
        scene_embedding = self.embedder.encode([scene_text], convert_to_numpy=True)[0]

        scores = {}
        for scene_type, type_embedding in self.type_embeddings.items():
            similarity = util.cos_sim(scene_embedding, type_embedding)[0][0].item()
            scores[scene_type] = similarity

        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return [
            {"type": scene_type, "confidence": float(score)}
            for scene_type, score in sorted_types[:top_k]
        ]

    def classify_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify all scenes and add type information."""
        classified_scenes = []

        for scene in scenes:
            scene_types = self.classify_scene(scene["text"], top_k=1)
            primary_type = scene_types[0]["type"] if scene_types else "unknown"

            classified_scene = scene.copy()
            classified_scene["scene_type"] = primary_type
            classified_scene["type_confidence"] = scene_types[0]["confidence"] if scene_types else 0.0
            classified_scene["all_types"] = scene_types

            classified_scenes.append(classified_scene)

        return classified_scenes

    def filter_scenes_by_type(
        self, scenes: List[Dict[str, Any]], scene_types: List[str], min_confidence: float = 0.3
    ) -> List[int]:
        """Return scene IDs that match the given types."""
        matching_scene_ids = []

        for scene in scenes:
            if scene.get("scene_type") in scene_types:
                if scene.get("type_confidence", 0) >= min_confidence:
                    matching_scene_ids.append(scene.get("scene_id", 0))

        return matching_scene_ids
