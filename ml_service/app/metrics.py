from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
    generate_latest,
)
import time
from functools import wraps
from typing import Callable, Dict

registry = CollectorRegistry()

ml_inference_latency_seconds = Histogram(
    "ml_inference_latency_seconds",
    "Time spent on ML inference",
    ["endpoint"],
    registry=registry,
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

ml_inference_errors_total = Counter(
    "ml_inference_errors_total",
    "Total number of ML inference errors",
    ["error_type"],
    registry=registry,
)

ml_requests_total = Counter(
    "ml_requests_total",
    "Total number of ML requests",
    ["endpoint", "status"],
    registry=registry,
)

ml_active_requests = Gauge(
    "ml_active_requests",
    "Number of active ML requests",
    registry=registry,
)

ml_feature_extraction_time = Histogram(
    "ml_feature_extraction_time",
    "Time spent extracting features per scene",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
    registry=registry,
)

ml_scene_parsing_time = Histogram(
    "ml_scene_parsing_time",
    "Time spent parsing script into scenes",
    buckets=(0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=registry,
)

ml_avg_violence_score = Gauge(
    "ml_avg_violence_score",
    "Average violence score from recent inferences",
    registry=registry,
)

ml_avg_sex_score = Gauge(
    "ml_avg_sex_score",
    "Average sex act score from recent inferences",
    registry=registry,
)

ml_avg_gore_score = Gauge(
    "ml_avg_gore_score",
    "Average gore score from recent inferences",
    registry=registry,
)

ml_avg_profanity_score = Gauge(
    "ml_avg_profanity_score",
    "Average profanity score from recent inferences",
    registry=registry,
)

ml_avg_drugs_score = Gauge(
    "ml_avg_drugs_score",
    "Average drugs score from recent inferences",
    registry=registry,
)

ml_avg_nudity_score = Gauge(
    "ml_avg_nudity_score",
    "Average nudity score from recent inferences",
    registry=registry,
)

ml_scenes_per_script = Histogram(
    "ml_scenes_per_script",
    "Number of scenes parsed per script",
    buckets=(1, 5, 10, 20, 50, 100, 200, 500, 1000),
    registry=registry,
)

ml_rating_distribution = Counter(
    "ml_rating_distribution",
    "Distribution of predicted ratings",
    ["rating"],
    registry=registry,
)

rating_inference_duration_seconds = Histogram(
    "rating_inference_duration_seconds",
    "Time spent on rating inference",
    ["endpoint"],
    registry=registry,
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

rating_errors_total = Counter(
    "rating_errors_total",
    "Total number of rating errors",
    ["error_type"],
    registry=registry,
)


class MetricsTracker:
    """Helper for tracking metrics during inference"""

    def __init__(self):
        self.timers = {}

    def start_timer(self, name: str):
        self.timers[name] = time.time()

    def end_timer(self, name: str) -> float:
        if name in self.timers:
            elapsed: float = time.time() - self.timers[name]
            del self.timers[name]
            return elapsed
        return 0.0

    def record_scene_parsing(self, duration: float):
        ml_scene_parsing_time.observe(duration)

    def record_feature_extraction(self, duration: float):
        ml_feature_extraction_time.observe(duration)

    def record_scores(self, agg_scores: Dict[str, float]):
        ml_avg_violence_score.set(agg_scores.get("violence", 0.0))
        ml_avg_sex_score.set(agg_scores.get("sex_act", 0.0))
        ml_avg_gore_score.set(agg_scores.get("gore", 0.0))
        ml_avg_profanity_score.set(agg_scores.get("profanity", 0.0))
        ml_avg_drugs_score.set(agg_scores.get("drugs", 0.0))
        ml_avg_nudity_score.set(agg_scores.get("nudity", 0.0))

    def record_scenes_count(self, count: int):
        ml_scenes_per_script.observe(count)

    def record_rating(self, rating: str):
        ml_rating_distribution.labels(rating=rating).inc()


def track_inference_time(endpoint: str):
    """Decorator to track inference time and errors"""

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            ml_active_requests.inc()
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                ml_inference_latency_seconds.labels(endpoint=endpoint).observe(duration)
                rating_inference_duration_seconds.labels(endpoint=endpoint).observe(
                    duration
                )
                ml_requests_total.labels(endpoint=endpoint, status="success").inc()
                return result
            except Exception as e:
                duration = time.time() - start_time
                ml_inference_latency_seconds.labels(endpoint=endpoint).observe(duration)
                rating_inference_duration_seconds.labels(endpoint=endpoint).observe(
                    duration
                )
                ml_inference_errors_total.labels(error_type=type(e).__name__).inc()
                rating_errors_total.labels(error_type=type(e).__name__).inc()
                ml_requests_total.labels(endpoint=endpoint, status="error").inc()
                raise
            finally:
                ml_active_requests.dec()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            ml_active_requests.inc()
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                ml_inference_latency_seconds.labels(endpoint=endpoint).observe(duration)
                rating_inference_duration_seconds.labels(endpoint=endpoint).observe(
                    duration
                )
                ml_requests_total.labels(endpoint=endpoint, status="success").inc()
                return result
            except Exception as e:
                duration = time.time() - start_time
                ml_inference_latency_seconds.labels(endpoint=endpoint).observe(duration)
                rating_inference_duration_seconds.labels(endpoint=endpoint).observe(
                    duration
                )
                ml_inference_errors_total.labels(error_type=type(e).__name__).inc()
                rating_errors_total.labels(error_type=type(e).__name__).inc()
                ml_requests_total.labels(endpoint=endpoint, status="error").inc()
                raise
            finally:
                ml_active_requests.dec()

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def get_metrics() -> bytes:
    """Export metrics in Prometheus format"""
    result: bytes = generate_latest(registry)  # type: ignore[assignment]
    return result
