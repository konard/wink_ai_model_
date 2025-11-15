from typing import Dict, Any, List, Optional
import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

from ..repair_pipeline import (
    parse_script_to_scenes,
    extract_scene_features,
    normalize_and_contextualize_scores,
    map_scores_to_rating,
)
from .analyzers import EntityExtractor, SceneClassifier
from .generators import LLMGenerator
from .strategies import (
    get_strategy_registry,
    SceneRemovalStrategy,
    ContentReductionStrategy,
    CharacterFocusedStrategy,
    LLMRewriteStrategy,
)
from .schemas import (
    StructuredWhatIfRequest,
    AdvancedWhatIfResponse,
    EntityInfo,
    SceneInfo,
)


class AdvancedWhatIfAnalyzer:
    """
    Advanced What-If analyzer with ML-based entity extraction,
    scene classification, and intelligent content modification.
    """

    def __init__(
        self,
        use_llm: bool = False,
        llm_provider: Optional[str] = None,
        llm_api_key: Optional[str] = None,
    ):
        logger.info("Initializing Advanced What-If Analyzer")

        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        self.entity_extractor = EntityExtractor()
        self.scene_classifier = SceneClassifier(self.embedder)

        self.llm_generator = None
        if use_llm and llm_provider:
            try:
                self.llm_generator = LLMGenerator(
                    provider=llm_provider,
                    api_key=llm_api_key,
                )
                logger.info(f"LLM generator initialized with provider: {llm_provider}")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM generator: {e}")

        self._init_strategies()

        logger.info("Advanced What-If Analyzer initialized successfully")

    def _init_strategies(self):
        """Initialize and register all modification strategies."""
        registry = get_strategy_registry()

        registry.register(SceneRemovalStrategy())
        registry.register(ContentReductionStrategy())
        registry.register(CharacterFocusedStrategy())

        if self.llm_generator:
            registry.register(LLMRewriteStrategy(self.llm_generator))

        logger.info(f"Registered {len(registry.list_strategies())} modification strategies")

    def analyze_structured(self, request: StructuredWhatIfRequest) -> AdvancedWhatIfResponse:
        """Process structured what-if request with multiple modifications."""
        logger.info(f"Processing structured what-if with {len(request.modifications)} modifications")

        original_result = self._analyze_script(request.script_text)

        scenes = parse_script_to_scenes(request.script_text)

        entities = self.entity_extractor.extract_entities(scenes)

        classified_scenes = self.scene_classifier.classify_scenes(scenes)

        modified_scenes = classified_scenes.copy()
        modifications_applied = []

        registry = get_strategy_registry()

        for mod_config in request.modifications:
            try:
                strategy = registry.get_strategy(mod_config.type)

                if not strategy.validate_params(mod_config.params):
                    logger.warning(f"Invalid params for {mod_config.type}, skipping")
                    continue

                modified_scenes, metadata = strategy.apply(
                    modified_scenes,
                    mod_config.params,
                    entities,
                )

                modifications_applied.append({
                    "type": mod_config.type,
                    "metadata": metadata,
                })

                logger.info(f"Applied {mod_config.type}: {metadata}")

            except Exception as e:
                logger.error(f"Failed to apply {mod_config.type}: {e}")
                modifications_applied.append({
                    "type": mod_config.type,
                    "error": str(e),
                })

        if request.preserve_structure:
            modified_text = self._reconstruct_script(modified_scenes)
        else:
            modified_text = "\n\n".join([s["text"] for s in modified_scenes])

        modified_result = self._analyze_script(modified_text)

        explanation = self._generate_explanation(
            original_result, modified_result, modifications_applied
        )

        entity_infos = self._format_entities(entities)
        scene_infos = self._format_scene_info(classified_scenes)

        return AdvancedWhatIfResponse(
            original_rating=original_result["rating"],
            modified_rating=modified_result["rating"],
            original_scores=original_result["scores"],
            modified_scores=modified_result["scores"],
            modifications_applied=modifications_applied,
            entities_extracted=entity_infos,
            scene_analysis=scene_infos,
            explanation=explanation,
            modified_script=modified_text,
            rating_changed=original_result["rating"] != modified_result["rating"],
        )

    def _analyze_script(self, text: str) -> Dict[str, Any]:
        """Analyze script and return rating with scores."""
        scenes = parse_script_to_scenes(text)

        features = []
        for scene in scenes:
            feat = extract_scene_features(scene["text"])
            features.append(feat)

        scores = [normalize_and_contextualize_scores(f) for f in features]

        score_keys = [
            "violence",
            "gore",
            "sex_act",
            "nudity",
            "profanity",
            "drugs",
            "child_risk",
        ]
        agg = {}

        for k in score_keys:
            values = [s[k] for s in scores]
            max_val = float(np.max(values))
            p95_val = float(np.percentile(values, 95))
            p90_val = float(np.percentile(values, 90))

            if k in ["violence", "gore"]:
                agg[k] = max_val * 0.7 + p95_val * 0.3
            elif k in ["sex_act", "nudity", "child_risk"]:
                agg[k] = max_val * 0.85 + p90_val * 0.15
            else:
                agg[k] = float(np.percentile(values, 90))

        rating_info = map_scores_to_rating(agg)

        return {
            "rating": rating_info["rating"],
            "reasons": rating_info["reasons"],
            "scores": {k: round(agg[k], 3) for k in score_keys},
            "total_scenes": len(scenes),
        }

    def _reconstruct_script(self, scenes: List[Dict[str, Any]]) -> str:
        """Reconstruct script maintaining structure."""
        return "\n\n".join([s["text"] for s in scenes])

    def _format_entities(self, entities: Dict[str, List[Any]]) -> List[EntityInfo]:
        """Format entities for response."""
        result = []
        for entity_type, entity_list in entities.items():
            for entity in entity_list[:10]:
                result.append(EntityInfo(
                    type=entity["type"],
                    name=entity["name"],
                    mentions=entity["mentions"],
                    scenes=entity["scenes"],
                ))
        return result

    def _format_scene_info(self, scenes: List[Dict[str, Any]]) -> List[SceneInfo]:
        """Format scene information for response."""
        result = []
        for scene in scenes[:20]:
            result.append(SceneInfo(
                scene_id=scene.get("scene_id", 0),
                scene_type=scene.get("scene_type", "unknown"),
                characters=scene.get("characters", []),
                location=scene.get("location"),
                summary=scene["text"][:100] + "..." if len(scene["text"]) > 100 else scene["text"],
            ))
        return result

    def _generate_explanation(
        self,
        original: Dict[str, Any],
        modified: Dict[str, Any],
        modifications: List[Dict[str, Any]],
    ) -> str:
        """Generate explanation of changes."""
        explanation_parts = []

        explanation_parts.append(
            f"Applied {len(modifications)} modification(s) to the script."
        )

        for mod in modifications:
            if "error" in mod:
                explanation_parts.append(f"- {mod['type']}: Failed ({mod['error']})")
            else:
                metadata = mod.get("metadata", {})
                explanation_parts.append(f"- {mod['type']}: {self._format_metadata(metadata)}")

        if original["rating"] == modified["rating"]:
            explanation_parts.append(
                f"\nRating remained: {original['rating']}. "
                "Modifications were not significant enough to change the age rating."
            )
        else:
            direction = "increased" if modified["rating"] > original["rating"] else "decreased"
            explanation_parts.append(
                f"\nRating {direction}: {original['rating']} → {modified['rating']}"
            )

        score_changes = []
        for key in ["violence", "gore", "sex_act", "nudity", "profanity", "drugs"]:
            orig_score = original["scores"].get(key, 0)
            mod_score = modified["scores"].get(key, 0)
            diff = mod_score - orig_score

            if abs(diff) > 0.1:
                direction = "increased" if diff > 0 else "decreased"
                score_changes.append(f"{key} {direction} by {abs(diff):.2f}")

        if score_changes:
            explanation_parts.append(f"\nScore changes: {', '.join(score_changes)}")

        return "\n".join(explanation_parts)

    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format modification metadata for explanation."""
        parts = []
        for key, value in metadata.items():
            if isinstance(value, (int, float)):
                parts.append(f"{key}={value}")
            elif isinstance(value, list) and len(value) <= 5:
                parts.append(f"{key}={value}")
            elif isinstance(value, str):
                parts.append(f"{key}={value}")
        return ", ".join(parts) if parts else "applied"


_advanced_analyzer: Optional[AdvancedWhatIfAnalyzer] = None


def get_advanced_analyzer(
    use_llm: bool = False,
    llm_provider: Optional[str] = None,
    llm_api_key: Optional[str] = None,
) -> AdvancedWhatIfAnalyzer:
    """Get or create advanced analyzer instance."""
    global _advanced_analyzer
    if _advanced_analyzer is None:
        _advanced_analyzer = AdvancedWhatIfAnalyzer(
            use_llm=use_llm,
            llm_provider=llm_provider,
            llm_api_key=llm_api_key,
        )
    return _advanced_analyzer
