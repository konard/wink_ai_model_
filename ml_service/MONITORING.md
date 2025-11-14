# ML Service Monitoring

## Overview

The ML service includes comprehensive monitoring with Prometheus metrics and structured logging.

## Quick Start

### Enable Metrics

Set environment variables:
```bash
ML_ENABLE_METRICS=true
ML_JSON_LOGS=true  # Optional: for JSON-formatted logs
```

### Access Metrics

Prometheus metrics endpoint:
```
GET http://localhost:8001/metrics
```

## Available Metrics

### Inference Metrics

- **ml_inference_latency_seconds** (histogram)
  - Latency for ML inference requests
  - Labels: `endpoint`

- **ml_requests_total** (counter)
  - Total number of ML requests
  - Labels: `endpoint`, `status` (success/error)

- **ml_inference_errors_total** (counter)
  - Total errors during inference
  - Labels: `error_type`

- **ml_active_requests** (gauge)
  - Current number of active requests

### Performance Metrics

- **ml_scene_parsing_time** (histogram)
  - Time to parse script into scenes

- **ml_feature_extraction_time** (histogram)
  - Average time to extract features per scene

- **ml_scenes_per_script** (histogram)
  - Distribution of scene counts per script

### Content Feature Metrics

Track average scores from recent inferences:

- **ml_avg_violence_score** (gauge)
- **ml_avg_sex_score** (gauge)
- **ml_avg_gore_score** (gauge)
- **ml_avg_profanity_score** (gauge)
- **ml_avg_drugs_score** (gauge)
- **ml_avg_nudity_score** (gauge)

### Rating Distribution

- **ml_rating_distribution** (counter)
  - Count of each predicted rating (6+, 12+, 16+, 18+)
  - Labels: `rating`

## Structured Logging

### JSON Logs

When `ML_JSON_LOGS=true`, logs are in JSON format:

```json
{
  "timestamp": "2025-11-14T12:00:00Z",
  "level": "INFO",
  "message": "feature_scores",
  "event": "feature_scores",
  "script_id": "123",
  "violence": 0.342,
  "sex_act": 0.120,
  "gore": 0.089,
  "profanity": 0.234,
  "drugs": 0.045,
  "nudity": 0.012,
  "predicted_rating": "12+",
  "model_version": "v1.0"
}
```

### Log Events

- **feature_scores**: Aggregated feature scores per script

## Grafana Dashboard

### Key Panels

1. **Latency** (p50/p90/p95/p99)
2. **Error Rate** (%)
3. **Request Rate** (req/s)
4. **Active Requests**
5. **Feature Score Trends** (violence, sex, gore, etc.)
6. **Rating Distribution** (pie chart)
7. **Scene Count Distribution**

### Example Queries

**P95 Latency:**
```promql
histogram_quantile(0.95, rate(ml_inference_latency_seconds_bucket[5m]))
```

**Error Rate:**
```promql
rate(ml_inference_errors_total[5m]) / rate(ml_requests_total[5m])
```

**Average Violence Score:**
```promql
ml_avg_violence_score
```

## Alerts

### Recommended Alerts

**High Error Rate:**
```yaml
alert: MLHighErrorRate
expr: rate(ml_inference_errors_total[5m]) / rate(ml_requests_total[5m]) > 0.01
for: 5m
labels:
  severity: warning
annotations:
  summary: ML inference error rate > 1%
```

**High Latency:**
```yaml
alert: MLHighLatency
expr: histogram_quantile(0.99, rate(ml_inference_latency_seconds_bucket[5m])) > 1.0
for: 5m
labels:
  severity: warning
annotations:
  summary: ML p99 latency > 1s
```

**Model Anomaly (all violence scores near max):**
```yaml
alert: MLModelAnomaly
expr: ml_avg_violence_score > 0.95
for: 10m
labels:
  severity: critical
annotations:
  summary: ML model may be broken - all violence scores high
```

## Integration

### Prometheus Config

Add to `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'ml-service'
    static_configs:
      - targets: ['ml-service:8001']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Loki (for logs)

If using JSON logs, configure Loki to scrape container logs.

### Sentry (optional)

For error tracking, add Sentry SDK and set `SENTRY_DSN` env var.

## Development

### Disable Metrics

For local development without monitoring:
```bash
ML_ENABLE_METRICS=false
```

### Testing Metrics

```bash
# Start service
uvicorn app.main:app --reload

# Send test request
curl -X POST http://localhost:8000/rate_script \
  -H "Content-Type: application/json" \
  -d '{"text": "INT. SCENE - test violence kill", "script_id": "test"}'

# Check metrics
curl http://localhost:8000/metrics
```

## Architecture

The monitoring system is designed to be **minimally invasive** to the ML pipeline:

1. **metrics.py** - Standalone Prometheus metrics module
2. **structured_logger.py** - Optional structured logging
3. **pipeline.py** - Only tracks timing with `if tracker:` checks
4. **main.py** - Adds `/metrics` endpoint and decorator

The ML engineer can continue working on the pipeline with minimal awareness of monitoring code.
