from pathlib import Path
from typing import Dict, Any
from loguru import logger
import tempfile

from .config import settings
from .metrics import MetricsTracker
from .structured_logger import log_feature_scores
from .repair_pipeline import analyze_script_file, parse_script_to_scenes, extract_scene_features, normalize_and_contextualize_scores, map_scores_to_rating


class RatingPipeline:
    def __init__(self):
        logger.info("Rating pipeline initialized")

    def analyze_script(self, text: str, script_id: str | None = None) -> Dict[str, Any]:
        logger.info(f"Analyzing script (id={script_id})")
        tracker = MetricsTracker() if settings.enable_metrics else None

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(text)
            temp_path = f.name

        try:
            if tracker:
                tracker.start_timer("analysis")

            result = analyze_script_file(temp_path)

            if tracker:
                tracker.end_timer("analysis")
                tracker.record_scenes_count(result.get('total_scenes', 0))
                tracker.record_rating(result['predicted_rating'])

            if settings.json_logs:
                agg_scores = result.get('aggregated_scores', {})
                log_feature_scores(
                    script_id=script_id,
                    violence=agg_scores.get('violence', 0.0),
                    sex_act=agg_scores.get('sex_act', 0.0),
                    gore=agg_scores.get('gore', 0.0),
                    profanity=agg_scores.get('profanity', 0.0),
                    drugs=agg_scores.get('drugs', 0.0),
                    nudity=agg_scores.get('nudity', 0.0),
                    predicted_rating=result['predicted_rating'],
                )

            top_scenes = []
            for scene in result.get('top_trigger_scenes', []):
                scores = scene.get('scores', {})
                top_scenes.append({
                    'scene_id': scene['scene_id'],
                    'heading': scene['heading'],
                    'violence': scores.get('violence', 0.0),
                    'gore': scores.get('gore', 0.0),
                    'sex_act': scores.get('sex_act', 0.0),
                    'nudity': scores.get('nudity', 0.0),
                    'profanity': scores.get('profanity', 0.0),
                    'drugs': scores.get('drugs', 0.0),
                    'child_risk': scores.get('child_risk', 0.0),
                    'weight': scene.get('weight', 0.0),
                    'sample_text': scene.get('sample_text'),
                    'recommendations': scene.get('recommendations', []),
                })

            return {
                "script_id": script_id,
                "predicted_rating": result['predicted_rating'],
                "reasons": result['reasons'],
                "agg_scores": result.get('aggregated_scores', {}),
                "top_trigger_scenes": top_scenes,
                "model_version": settings.model_version,
                "total_scenes": result.get('total_scenes', 0),
                "evidence_excerpts": result.get('evidence_excerpts', []),
            }
        finally:
            Path(temp_path).unlink(missing_ok=True)


pipeline: RatingPipeline | None = None


def get_pipeline() -> RatingPipeline:
    global pipeline
    if pipeline is None:
        pipeline = RatingPipeline()
    return pipeline
