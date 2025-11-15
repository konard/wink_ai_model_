from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
import difflib

from ..models.script import Script, ScriptVersion, Scene


class VersionService:
    @staticmethod
    async def create_version(
        db: AsyncSession,
        script_id: int,
        change_description: Optional[str] = None,
        make_current: bool = True,
    ) -> ScriptVersion:
        result = await db.execute(select(Script).where(Script.id == script_id))
        script = result.scalar_one_or_none()
        if not script:
            raise ValueError(f"Script {script_id} not found")

        result = await db.execute(
            select(ScriptVersion)
            .where(ScriptVersion.script_id == script_id)
            .order_by(desc(ScriptVersion.version_number))
        )
        latest_version = result.scalar_one_or_none()
        new_version_number = (
            (latest_version.version_number + 1) if latest_version else 1
        )

        scenes_result = await db.execute(
            select(Scene).where(Scene.script_id == script_id)
        )
        scenes = scenes_result.scalars().all()
        scenes_data = [
            {
                "scene_id": scene.scene_id,
                "heading": scene.heading,
                "violence": scene.violence,
                "gore": scene.gore,
                "sex_act": scene.sex_act,
                "nudity": scene.nudity,
                "profanity": scene.profanity,
                "drugs": scene.drugs,
                "child_risk": scene.child_risk,
                "weight": scene.weight,
                "sample_text": scene.sample_text,
            }
            for scene in scenes
        ]

        new_version = ScriptVersion(
            script_id=script_id,
            version_number=new_version_number,
            title=script.title,
            content=script.content,
            predicted_rating=script.predicted_rating,
            agg_scores=script.agg_scores,
            total_scenes=script.total_scenes,
            change_description=change_description,
            is_current=make_current,
            scenes_data=scenes_data,
            metadata={
                "model_version": script.model_version,
                "created_from": "manual_save",
            },
        )

        if make_current:
            await db.execute(
                select(ScriptVersion).where(
                    and_(ScriptVersion.script_id == script_id, ScriptVersion.is_current)
                )
            )
            result = await db.execute(
                select(ScriptVersion).where(
                    and_(ScriptVersion.script_id == script_id, ScriptVersion.is_current)
                )
            )
            for version in result.scalars():
                version.is_current = False

            script.current_version = new_version_number

        db.add(new_version)
        await db.commit()
        await db.refresh(new_version)

        return new_version

    @staticmethod
    async def get_versions(db: AsyncSession, script_id: int) -> List[ScriptVersion]:
        result = await db.execute(
            select(ScriptVersion)
            .where(ScriptVersion.script_id == script_id)
            .order_by(desc(ScriptVersion.version_number))
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_version(
        db: AsyncSession, script_id: int, version_number: int
    ) -> Optional[ScriptVersion]:
        result = await db.execute(
            select(ScriptVersion).where(
                and_(
                    ScriptVersion.script_id == script_id,
                    ScriptVersion.version_number == version_number,
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def restore_version(
        db: AsyncSession, script_id: int, version_number: int
    ) -> Script:
        version = await VersionService.get_version(db, script_id, version_number)
        if not version:
            raise ValueError(f"Version {version_number} not found")

        result = await db.execute(select(Script).where(Script.id == script_id))
        script = result.scalar_one_or_none()
        if not script:
            raise ValueError(f"Script {script_id} not found")

        await VersionService.create_version(
            db,
            script_id,
            change_description=f"Backup before restore to v{version_number}",
            make_current=False,
        )

        script.title = version.title
        script.content = version.content
        script.predicted_rating = version.predicted_rating
        script.agg_scores = version.agg_scores
        script.total_scenes = version.total_scenes
        script.current_version = version.version_number

        await db.execute(
            select(ScriptVersion).where(ScriptVersion.script_id == script_id)
        )
        result = await db.execute(
            select(ScriptVersion).where(ScriptVersion.script_id == script_id)
        )
        for v in result.scalars():
            v.is_current = v.version_number == version_number

        await db.commit()
        await db.refresh(script)

        return script

    @staticmethod
    def compare_versions(
        version1: ScriptVersion, version2: ScriptVersion
    ) -> Dict[str, Any]:
        content_diff = list(
            difflib.unified_diff(
                version1.content.splitlines(keepends=True),
                version2.content.splitlines(keepends=True),
                fromfile=f"v{version1.version_number}",
                tofile=f"v{version2.version_number}",
                lineterm="",
            )
        )

        rating_changed = version1.predicted_rating != version2.predicted_rating

        score_changes = {}
        if version1.agg_scores and version2.agg_scores:
            for key in version1.agg_scores.keys():
                old_val = version1.agg_scores.get(key, 0)
                new_val = version2.agg_scores.get(key, 0)
                if abs(old_val - new_val) > 0.01:
                    score_changes[key] = {
                        "old": old_val,
                        "new": new_val,
                        "change": new_val - old_val,
                    }

        scenes_changed = 0
        if version1.scenes_data and version2.scenes_data:
            scenes_changed = abs(len(version1.scenes_data) - len(version2.scenes_data))

        return {
            "version1": {
                "number": version1.version_number,
                "rating": version1.predicted_rating,
                "scenes": version1.total_scenes,
                "created_at": (
                    version1.created_at.isoformat() if version1.created_at else None
                ),
            },
            "version2": {
                "number": version2.version_number,
                "rating": version2.predicted_rating,
                "scenes": version2.total_scenes,
                "created_at": (
                    version2.created_at.isoformat() if version2.created_at else None
                ),
            },
            "changes": {
                "rating_changed": rating_changed,
                "rating_change": (
                    {"from": version1.predicted_rating, "to": version2.predicted_rating}
                    if rating_changed
                    else None
                ),
                "scenes_changed": scenes_changed,
                "score_changes": score_changes,
                "content_diff": content_diff[:100],
                "total_lines_changed": len(content_diff),
            },
        }

    @staticmethod
    async def delete_version(
        db: AsyncSession, script_id: int, version_number: int
    ) -> bool:
        version = await VersionService.get_version(db, script_id, version_number)
        if not version:
            return False

        if version.is_current:
            raise ValueError("Cannot delete current version")

        await db.delete(version)
        await db.commit()

        return True
