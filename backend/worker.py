import sys
from loguru import logger
from rq import Worker

from app.core.config import settings
from app.services.queue import redis_conn

logger.remove()
logger.add(sys.stderr, level=settings.log_level)

if __name__ == "__main__":
    logger.info("Starting RQ worker...")
    worker = Worker(["rating"], connection=redis_conn)
    worker.work()
