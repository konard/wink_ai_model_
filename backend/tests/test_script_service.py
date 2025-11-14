import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.services.script_service import ScriptService
from app.schemas.script import ScriptCreate
from app.models.script import Script


@pytest.mark.asyncio
async def test_create_script(test_session: AsyncSession):
    script_data = ScriptCreate(
        title="Test Script", content="INT. ROOM - DAY\n\nJohn enters."
    )

    script = await ScriptService.create_script(test_session, script_data)

    assert script.id is not None
    assert script.title == "Test Script"
    assert "John enters" in script.content


@pytest.mark.asyncio
async def test_get_script_existing(test_session: AsyncSession, sample_script):
    retrieved = await ScriptService.get_script(test_session, sample_script.id)

    assert retrieved is not None
    assert retrieved.id == sample_script.id
    assert retrieved.title == sample_script.title


@pytest.mark.asyncio
async def test_get_script_nonexistent(test_session: AsyncSession):
    result = await ScriptService.get_script(test_session, 99999)
    assert result is None


@pytest.mark.asyncio
async def test_list_scripts(test_session: AsyncSession, sample_script):
    scripts = await ScriptService.list_scripts(test_session)

    assert len(scripts) >= 1
    assert any(s.id == sample_script.id for s in scripts)


@pytest.mark.asyncio
async def test_list_scripts_with_pagination(test_session: AsyncSession):
    for i in range(5):
        script_data = ScriptCreate(title=f"Script {i}", content="Content " * 10)
        await ScriptService.create_script(test_session, script_data)

    scripts = await ScriptService.list_scripts(test_session, skip=2, limit=2)

    assert len(scripts) <= 2


@pytest.mark.asyncio
async def test_process_rating_success(test_session: AsyncSession, sample_script):
    mock_result = {
        "predicted_rating": "16+",
        "agg_scores": {"violence": 0.7, "gore": 0.3},
        "model_version": "v1.0",
        "total_scenes": 2,
        "top_trigger_scenes": [
            {
                "scene_id": 0,
                "heading": "INT. WAREHOUSE - NIGHT",
                "violence": 0.8,
                "gore": 0.5,
                "sex_act": 0.0,
                "nudity": 0.0,
                "profanity": 0.2,
                "drugs": 0.0,
                "child_risk": 0.0,
                "weight": 0.5,
            }
        ],
        "reasons": ["High violence content"],
    }

    with patch("app.services.script_service.ml_client") as mock_client:
        mock_client.rate_script = AsyncMock(return_value=mock_result)

        result = await ScriptService.process_rating(test_session, sample_script.id)

        refreshed_result = await test_session.execute(
            select(Script)
            .options(selectinload(Script.scenes), selectinload(Script.ratings))
            .where(Script.id == sample_script.id)
        )
        refreshed_script = refreshed_result.scalar_one()

        assert result["predicted_rating"] == "16+"
        assert refreshed_script.predicted_rating == "16+"
        assert len(refreshed_script.scenes) >= 1
        assert len(refreshed_script.ratings) >= 1


@pytest.mark.asyncio
async def test_process_rating_script_not_found(test_session: AsyncSession):
    with pytest.raises(ValueError) as exc_info:
        await ScriptService.process_rating(test_session, 99999)
    assert "not found" in str(exc_info.value)
