"""
Basic tests for Advanced What-If Analyzer.
Run with: pytest test_basic.py
"""
import pytest
from .analyzer import AdvancedWhatIfAnalyzer
from .schemas import StructuredWhatIfRequest, ModificationConfig


SAMPLE_SCRIPT = """INT. WAREHOUSE - NIGHT

JOHN pulls out a gun and aims at the VILLAIN.

JOHN
Drop your weapon!

VILLAIN
You'll never take me alive, you bastard!

They fight violently. Blood sprays across the floor.

EXT. PARK - DAY

MARY sits on a bench reading a book.
"""


@pytest.fixture
def analyzer():
    return AdvancedWhatIfAnalyzer(use_llm=False)


def test_entity_extraction(analyzer):
    """Test that entities are extracted correctly."""
    request = StructuredWhatIfRequest(
        script_text=SAMPLE_SCRIPT,
        modifications=[],
    )

    result = analyzer.analyze_structured(request)

    assert len(result.entities_extracted) > 0
    character_names = [e.name for e in result.entities_extracted if e.type == "character"]
    assert any("JOHN" in name or "MARY" in name for name in character_names)


def test_scene_classification(analyzer):
    """Test that scenes are classified."""
    request = StructuredWhatIfRequest(
        script_text=SAMPLE_SCRIPT,
        modifications=[],
    )

    result = analyzer.analyze_structured(request)

    assert len(result.scene_analysis) > 0
    scene_types = [s.scene_type for s in result.scene_analysis]
    assert all(st in ["action", "dialogue", "exposition", "emotional", "suspense", "romantic", "comedic"] for st in scene_types)


def test_violence_reduction(analyzer):
    """Test violence reduction strategy."""
    request = StructuredWhatIfRequest(
        script_text=SAMPLE_SCRIPT,
        modifications=[
            ModificationConfig(
                type="reduce_violence",
                params={"content_types": ["violence", "gore"]},
            )
        ],
    )

    result = analyzer.analyze_structured(request)

    assert len(result.modifications_applied) == 1
    assert result.modifications_applied[0]["type"] == "reduce_violence"
    assert "total_replacements" in result.modifications_applied[0]["metadata"]

    orig_violence = result.original_scores.get("violence", 0)
    mod_violence = result.modified_scores.get("violence", 0)
    assert mod_violence <= orig_violence


def test_profanity_reduction(analyzer):
    """Test profanity reduction strategy."""
    request = StructuredWhatIfRequest(
        script_text=SAMPLE_SCRIPT,
        modifications=[
            ModificationConfig(
                type="reduce_profanity",
                params={"content_types": ["profanity"]},
            )
        ],
    )

    result = analyzer.analyze_structured(request)

    assert "bastard" not in result.modified_script.lower()


def test_scene_removal(analyzer):
    """Test scene removal strategy."""
    request = StructuredWhatIfRequest(
        script_text=SAMPLE_SCRIPT,
        modifications=[
            ModificationConfig(
                type="remove_scenes",
                params={"scene_ids": [0]},
            )
        ],
    )

    result = analyzer.analyze_structured(request)

    assert result.modifications_applied[0]["metadata"]["removed_count"] >= 1


def test_character_rename(analyzer):
    """Test character rename strategy."""
    request = StructuredWhatIfRequest(
        script_text=SAMPLE_SCRIPT,
        modifications=[
            ModificationConfig(
                type="modify_character",
                params={
                    "action": "rename",
                    "character_name": "JOHN",
                    "new_name": "JACK",
                },
            )
        ],
    )

    result = analyzer.analyze_structured(request)

    assert "JACK" in result.modified_script
    assert result.modifications_applied[0]["metadata"]["replacements"] > 0


def test_multiple_modifications(analyzer):
    """Test applying multiple modifications in sequence."""
    request = StructuredWhatIfRequest(
        script_text=SAMPLE_SCRIPT,
        modifications=[
            ModificationConfig(
                type="reduce_violence",
                params={"content_types": ["violence"]},
            ),
            ModificationConfig(
                type="reduce_profanity",
                params={"content_types": ["profanity"]},
            ),
        ],
    )

    result = analyzer.analyze_structured(request)

    assert len(result.modifications_applied) == 2
    assert result.modifications_applied[0]["type"] == "reduce_violence"
    assert result.modifications_applied[1]["type"] == "reduce_profanity"


def test_rating_comparison(analyzer):
    """Test that ratings are compared correctly."""
    request = StructuredWhatIfRequest(
        script_text=SAMPLE_SCRIPT,
        modifications=[
            ModificationConfig(
                type="reduce_violence",
                params={"content_types": ["violence", "gore"]},
            ),
            ModificationConfig(
                type="reduce_profanity",
                params={"content_types": ["profanity"]},
            ),
        ],
    )

    result = analyzer.analyze_structured(request)

    assert result.original_rating in ["0+", "6+", "12+", "16+", "18+"]
    assert result.modified_rating in ["0+", "6+", "12+", "16+", "18+"]
    assert result.explanation is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
