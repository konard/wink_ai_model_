from typing import Any

from loguru import logger

from ..db.base import async_session
from .script_service import script_service


async def process_script_rating(script_id: int) -> dict[str, Any]:
    logger.info(f"Starting rating task for script {script_id}")

    async with async_session() as db:
        try:
            result = await script_service.process_rating(db, script_id)
            logger.info(f"Rating task completed for script {script_id}")
            return result
        except Exception as e:
            logger.error(f"Rating task failed for script {script_id}: {e}")
            raise
