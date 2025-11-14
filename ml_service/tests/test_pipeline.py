import pytest
from app.pipeline import RatingPipeline


@pytest.fixture
def pipeline():
    return RatingPipeline()


def test_parse_script_to_scenes(pipeline):
    script = """
    INT. HOUSE - DAY

    John enters the room.

    EXT. STREET - NIGHT

    Mary walks down the street.
    """

    scenes = pipeline.parse_script_to_scenes(script)
    assert len(scenes) >= 2
    assert any('INT' in s['heading'] for s in scenes)


def test_scene_feature_vector(pipeline):
    scene_text = "He pulled out a gun and shot the man. Blood everywhere."

    features = pipeline.scene_feature_vector(scene_text)

    assert 'violence' in features
    assert 'gore' in features
    assert features['violence'] > 0
    assert features['gore'] > 0


def test_normalize_scene_scores(pipeline):
    features = {
        'violence': 5,
        'gore': 3,
        'sex_act': 0,
        'nudity': 0,
        'profanity': 2,
        'drugs': 1,
        'child_mentions': 0,
        'length': 100
    }

    normalized = pipeline.normalize_scene_scores(features)

    for key, value in normalized.items():
        if key != 'child_risk':
            assert 0 <= value <= 1


def test_map_scores_to_rating(pipeline):
    agg_scores = {
        'violence': 0.2,
        'gore': 0.1,
        'sex_act': 0.0,
        'nudity': 0.0,
        'profanity': 0.1,
        'drugs': 0.0,
        'child_risk': 0.0
    }

    result = pipeline.map_scores_to_rating(agg_scores)

    assert 'rating' in result
    assert result['rating'] in ['6+', '12+', '16+', '18+']


def test_analyze_script_mild_content(pipeline):
    script = """
    INT. OFFICE - DAY

    Sarah sits at her desk, typing on her computer.
    Her phone rings.

    SARAH
    Hello? Yes, I'll be there soon.
    """

    result = pipeline.analyze_script(script, script_id="test1")

    assert result['script_id'] == "test1"
    assert result['predicted_rating'] in ['6+', '12+']
    assert result['total_scenes'] > 0


def test_analyze_script_violent_content(pipeline):
    script = """
    INT. WAREHOUSE - NIGHT

    The man pulls out a gun and shoots. Blood splatters on the wall.
    The victim falls dead. Murder scene. Violence everywhere.
    Corpse on the floor. Killer stands over the dead body.
    """

    result = pipeline.analyze_script(script, script_id="test2")

    assert result['predicted_rating'] in ['16+', '18+']
    assert len(result['top_trigger_scenes']) > 0
    assert result['agg_scores']['violence'] > 0.3


def test_analyze_script_explicit_content(pipeline):
    script = """
    INT. BEDROOM - NIGHT

    Sexual content. They have sex. Explicit intercourse scene.
    Nudity everywhere. Very graphic sexual activity.
    """

    result = pipeline.analyze_script(script, script_id="test3")

    assert result['predicted_rating'] == '18+'
    assert result['agg_scores']['sex_act'] > 0.5
