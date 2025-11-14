import json
import sys
from typing import Dict, Any, Optional
from loguru import logger
from .config import settings


def json_formatter(record: Dict[str, Any]) -> str:
    """Format log record as JSON"""
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }

    if record.get("extra"):
        log_entry.update(record["extra"])

    if record.get("exception"):
        log_entry["exception"] = str(record["exception"])

    return json.dumps(log_entry)


def setup_structured_logging(json_logs: bool = False):
    """Configure structured logging for ML service"""
    logger.remove()

    if json_logs:
        logger.add(
            sys.stderr,
            format=json_formatter,
            level=settings.log_level,
            serialize=False,
        )
    else:
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.log_level,
        )


def log_inference_event(
    event: str,
    script_id: Optional[str] = None,
    latency_ms: Optional[float] = None,
    model_version: Optional[str] = None,
    **kwargs,
):
    """Log structured inference event"""
    log_data = {
        "event": event,
        "script_id": script_id,
        "model_version": model_version or settings.model_version,
    }

    if latency_ms is not None:
        log_data["latency_ms"] = round(latency_ms, 2)

    log_data.update(kwargs)

    logger.bind(**log_data).info(f"{event}")


def log_feature_scores(
    script_id: Optional[str],
    violence: float,
    sex_act: float,
    gore: float,
    profanity: float,
    drugs: float,
    nudity: float,
    predicted_rating: str,
):
    """Log feature scores for monitoring"""
    log_inference_event(
        "feature_scores",
        script_id=script_id,
        violence=round(violence, 3),
        sex_act=round(sex_act, 3),
        gore=round(gore, 3),
        profanity=round(profanity, 3),
        drugs=round(drugs, 3),
        nudity=round(nudity, 3),
        predicted_rating=predicted_rating,
    )
