from typing import Any

from arq import create_pool
from arq.connections import ArqRedis
from arq.jobs import JobStatus
from loguru import logger

from ..core.config import settings


async def get_arq_pool() -> ArqRedis:
    redis_settings = settings.get_arq_settings()
    return await create_pool(redis_settings)


async def enqueue_rating_job(script_id: int) -> str:
    pool = await get_arq_pool()
    try:
        job = await pool.enqueue_job("process_script_rating", script_id)
        logger.info(f"Enqueued rating job {job.job_id} for script {script_id}")
        return job.job_id  # type: ignore[no-any-return]
    finally:
        await pool.close()


async def get_job_status(job_id: str) -> dict[str, Any]:
    pool = await get_arq_pool()
    try:
        job_info = await pool.job_info(job_id)  # type: ignore[attr-defined]

        if job_info is None:
            return {
                "job_id": job_id,
                "status": "not_found",
                "result": None,
                "error": None,
            }

        status_mapping = {
            JobStatus.deferred: "deferred",
            JobStatus.queued: "queued",
            JobStatus.in_progress: "in_progress",
            JobStatus.complete: "completed",
            JobStatus.not_found: "not_found",
        }

        status = status_mapping.get(job_info.status, "unknown")

        return {
            "job_id": job_id,
            "status": status,
            "result": (
                job_info.result if job_info.status == JobStatus.complete else None
            ),
            "error": (
                str(job_info.result)
                if job_info.status
                not in [
                    JobStatus.complete,
                    JobStatus.queued,
                    JobStatus.in_progress,
                    JobStatus.deferred,
                ]
                else None
            ),
        }
    except Exception as e:
        logger.error(f"Error fetching job {job_id}: {e}")
        return {"job_id": job_id, "status": "error", "error": str(e), "result": None}
    finally:
        await pool.close()
