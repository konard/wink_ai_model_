import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Script, Scene


@pytest.mark.asyncio
async def test_create_script(test_session: AsyncSession):
    script = Script(
        title="Test Movie",
        content="INT. HOUSE - DAY\n\nJohn enters."
    )

    test_session.add(script)
    await test_session.commit()
    await test_session.refresh(script)

    assert script.id is not None
    assert script.title == "Test Movie"
    assert script.created_at is not None


@pytest.mark.asyncio
async def test_script_with_scenes(test_session: AsyncSession):
    script = Script(
        title="Test Movie",
        content="INT. HOUSE - DAY\n\nJohn enters.",
        predicted_rating="12+",
        total_scenes=1
    )

    test_session.add(script)
    await test_session.commit()
    await test_session.refresh(script)

    scene = Scene(
        script_id=script.id,
        scene_id=0,
        heading="INT. HOUSE - DAY",
        violence=0.2,
        gore=0.0,
        sex_act=0.0,
        nudity=0.0,
        profanity=0.0,
        drugs=0.0,
        child_risk=0.0,
        weight=0.1
    )

    test_session.add(scene)
    await test_session.commit()
    await test_session.refresh(script)

    assert len(script.scenes) == 1
    assert script.scenes[0].heading == "INT. HOUSE - DAY"
