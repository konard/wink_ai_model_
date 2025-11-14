import sys
import signal
from loguru import logger

from app.core.config import settings
from app.services.tasks import process_script_rating

logger.remove()
logger.add(sys.stderr, level=settings.log_level)


class WorkerSettings:
    functions = [process_script_rating]
    redis_settings = settings.get_arq_settings()
    job_timeout = 600


def handle_sigterm(signum, frame):
    logger.info("Received SIGTERM, shutting down gracefully...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    logger.info("Starting ARQ worker...")

    from arq import run_worker

    run_worker(WorkerSettings)
