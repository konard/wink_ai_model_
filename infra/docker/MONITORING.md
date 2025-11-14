# Monitoring Setup

## Overview

The development environment includes Prometheus and Grafana for monitoring ML service metrics.

## Quick Start

```bash
cd infra/docker
docker-compose -f compose.dev.yml up -d
```

## Access

- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: `admin`
- **Prometheus**: http://localhost:9090
- **ML Service Metrics**: http://localhost:8001/metrics

## Grafana Dashboard

The "ML Service Metrics" dashboard is automatically provisioned and includes:

### Performance Metrics
- **Inference Latency**: p50, p90, p95, p99 percentiles
- **Request Rate**: Success vs error requests per second
- **Error Rate**: Percentage of failed requests
- **Active Requests**: Current number of concurrent requests

### ML Metrics
- **Content Feature Scores**: Violence, sex, gore, profanity, drugs, nudity
- **Rating Distribution**: Pie chart of predicted ratings (6+, 12+, 16+, 18+)
- **Scenes per Script**: Average number of scenes parsed

## Custom Queries

### PromQL Examples

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

## Alerts (Optional)

To set up alerts, add these rules to Prometheus:

**High Error Rate:**
```yaml
alert: MLHighErrorRate
expr: rate(ml_inference_errors_total[5m]) / rate(ml_requests_total[5m]) > 0.01
for: 5m
```

**High Latency:**
```yaml
alert: MLHighLatency
expr: histogram_quantile(0.99, rate(ml_inference_latency_seconds_bucket[5m])) > 1.0
for: 5m
```

## Data Retention

- Prometheus: 15 days (default)
- Grafana: Indefinite (dashboard configs)

To change Prometheus retention:
```yaml
command:
  - '--storage.tsdb.retention.time=30d'
```

## Troubleshooting

### Metrics not appearing

1. Check ML service is running:
   ```bash
   curl http://localhost:8001/metrics
   ```

2. Check Prometheus targets:
   - Go to http://localhost:9090/targets
   - Ensure `ml-service` target is "UP"

3. Check Grafana datasource:
   - Go to Configuration → Data Sources
   - Test the Prometheus connection

### Dashboard not loading

- Restart Grafana:
  ```bash
  docker-compose -f compose.dev.yml restart grafana
  ```

## Production Setup

For production, see `compose.prod.yml` and configure:
- Persistent volumes for metrics data
- Authentication for Grafana
- TLS/SSL for endpoints
- Alert manager integration
