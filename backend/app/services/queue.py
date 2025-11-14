import redis
from rq import Queue
from loguru import logger

from ..core.config import settings

redis_conn = redis.from_url(settings.redis_url)
rating_queue = Queue("rating", connection=redis_conn)


def enqueue_rating_job(script_id: int) -> str:
    from .tasks import process_script_rating

    job = rating_queue.enqueue(process_script_rating, script_id, job_timeout="10m")
    logger.info(f"Enqueued rating job {job.id} for script {script_id}")
    return job.id


def get_job_status(job_id: str) -> dict:
    from rq.job import Job

    try:
        job = Job.fetch(job_id, connection=redis_conn)
        return {
            "job_id": job_id,
            "status": job.get_status(),
            "result": job.result if job.is_finished else None,
            "error": str(job.exc_info) if job.is_failed else None,
        }
    except Exception as e:
        logger.error(f"Error fetching job {job_id}: {e}")
        return {"job_id": job_id, "status": "unknown", "error": str(e)}
