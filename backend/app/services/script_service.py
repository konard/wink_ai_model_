from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.script import Script, Scene, RatingLog
from ..schemas.script import ScriptCreate
from .ml_client import ml_client


class ScriptService:
    @staticmethod
    async def create_script(db: AsyncSession, script_data: ScriptCreate) -> Script:
        script = Script(title=script_data.title, content=script_data.content)
        db.add(script)
        await db.commit()
        await db.refresh(script)
        logger.info(f"Created script: {script.id}")
        return script

    @staticmethod
    async def get_script(db: AsyncSession, script_id: int) -> Script | None:
        result = await db.execute(
            select(Script)
            .options(selectinload(Script.scenes))
            .where(Script.id == script_id)
        )
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    @staticmethod
    async def list_scripts(
        db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[Script]:
        result = await db.execute(
            select(Script).offset(skip).limit(limit).order_by(Script.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def process_rating(db: AsyncSession, script_id: int) -> dict[str, Any]:
        script = await ScriptService.get_script(db, script_id)
        if not script:
            raise ValueError(f"Script {script_id} not found")

        logger.info(f"Processing rating for script {script_id}")

        result = await ml_client.rate_script(
            text=str(script.content), script_id=str(script.id)
        )

        script.predicted_rating = result["predicted_rating"]
        script.agg_scores = result["agg_scores"]
        script.model_version = result["model_version"]
        script.total_scenes = result["total_scenes"]

        for scene_data in result["top_trigger_scenes"]:
            scene = Scene(
                script_id=script.id,
                scene_id=scene_data["scene_id"],
                heading=scene_data["heading"],
                sample_text=scene_data.get("sample_text"),
                violence=scene_data["violence"],
                gore=scene_data["gore"],
                sex_act=scene_data["sex_act"],
                nudity=scene_data["nudity"],
                profanity=scene_data["profanity"],
                drugs=scene_data["drugs"],
                child_risk=scene_data["child_risk"],
                weight=scene_data["weight"],
            )
            db.add(scene)

        rating_log = RatingLog(
            script_id=script.id,
            predicted_rating=result["predicted_rating"],
            reasons=result["reasons"],
            model_version=result["model_version"],
        )
        db.add(rating_log)

        await db.commit()
        await db.refresh(script)

        logger.info(
            f"Rating completed for script {script_id}: {result['predicted_rating']}"
        )
        return result


script_service = ScriptService()
