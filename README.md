# Movie Script Rating System

Automated system for analyzing movie scripts and predicting age-appropriate ratings based on content analysis.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│    Nginx     │────▶│   Backend   │
│ React/Vite  │     │   Reverse    │     │   FastAPI   │
└─────────────┘     │    Proxy     │     └──────┬──────┘
                    └──────┬───────┘            │
                           │              ┌─────┴──────┐
                           │              │            │
                    ┌──────▼──────┐  ┌───▼───┐   ┌────▼────┐
                    │ ML Service  │  │ ARQ   │   │ Alembic │
                    │  PyTorch    │  │Worker │   │         │
                    └─────────────┘  └───┬───┘   └────┬────┘
                                         │            │
                                    ┌────▼────┐  ┌────▼────┐
                                    │  Redis  │  │Postgres │
                                    └─────────┘  └─────────┘
```

## Monitoring Stack

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Prometheus  │────▶│   Grafana   │◀────│    Loki     │
│  (Metrics)  │     │(Dashboards) │     │   (Logs)    │
└──────┬──────┘     └─────────────┘     └──────▲──────┘
       │                                        │
       └────────────────┬───────────────────────┘
                        │
                  ┌─────▼──────┐
                  │  Promtail  │
                  │(Log Agent) │
                  └────────────┘
```

## Tech Stack

### Backend
- **FastAPI** - High-performance async REST API framework
- **SQLAlchemy 2.0** - Async ORM for PostgreSQL
- **Alembic** - Database migration tool
- **ARQ** - Async background job processing with Redis
- **Uvicorn/Gunicorn** - Production-ready ASGI server
- **Pydantic v2** - Data validation with type safety
- **Loguru** - Structured logging
- **Prometheus** - Application metrics

### ML Service
- **PyTorch** - Deep learning framework
- **Sentence Transformers** - Text embeddings
- **UMAP + HDBSCAN** - Clustering algorithms
- **FastAPI** - ML inference API

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Fast build tool
- **TailwindCSS** - Utility-first CSS
- **TanStack Query** - Async state management
- **Recharts** - Chart visualization

### Infrastructure
- **Docker + Docker Compose** - Containerization
- **PostgreSQL 16** - Relational database with connection pooling
- **Redis 7** - Cache & job queue
- **Nginx** - Reverse proxy with load balancing
- **Prometheus + Grafana** - Metrics and dashboards
- **Loki + Promtail** - Log aggregation
- **GitHub Actions** - CI/CD pipeline

## Features

### Backend
- ✅ Async/await throughout the stack
- ✅ Connection pooling (20 connections, max overflow 10)
- ✅ Request ID tracing (X-Request-ID header)
- ✅ Comprehensive health checks (DB + Redis)
- ✅ Retry logic with exponential backoff
- ✅ Environment variable validation
- ✅ Type hints with Pydantic v2
- ✅ Graceful shutdown handling

### Infrastructure
- ✅ Nginx reverse proxy with JSON logging
- ✅ Prometheus metrics collection
- ✅ Grafana dashboards
- ✅ Loki log aggregation with 7-day retention
- ✅ Hot reload for development
- ✅ Separate dev/prod configurations

## Quick Start

### Prerequisites
- Docker & Docker Compose
- (Optional) Node.js 20+, Python 3.12+ for local development

### Development Setup

1. Clone the repository

2. Copy and configure environment file:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Start all services:
```bash
make dev-up
```

4. Access the services:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/docs
- **ML Service**: http://localhost:8001/docs
- **Nginx Proxy**: http://localhost:80
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100

### Development Workflows

#### For ML Development
Start only ML service + dependencies:
```bash
make dev-ml
```

Edit code in `ml_service/app/` - hot reload is enabled.

#### For Backend Development
```bash
make dev-backend
```

Edit code in `backend/app/` - hot reload is enabled.

#### For Frontend Development
```bash
make dev-frontend
```

Edit code in `frontend/src/` - hot reload is enabled.

### Stopping Services
```bash
make dev-down
```

### Clean All Data
```bash
make clean  # Removes all containers and volumes
```

## Project Structure

```
.
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   │   └── endpoints/
│   │   ├── core/        # Configuration & exceptions
│   │   ├── db/          # Database setup & connection pooling
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic & ML client
│   ├── alembic/         # Database migrations
│   ├── tests/           # Backend tests
│   ├── worker.py        # ARQ background worker
│   └── requirements.txt
│
├── frontend/            # React frontend
│   ├── src/
│   │   ├── api/         # API client
│   │   ├── components/  # React components
│   │   └── App.tsx
│   ├── Dockerfile       # Production build
│   ├── Dockerfile.dev   # Development build
│   └── package.json
│
├── ml_service/          # ML inference service
│   ├── app/
│   │   ├── config.py    # ML configuration
│   │   ├── pipeline.py  # Rating pipeline
│   │   ├── schemas.py   # API schemas
│   │   ├── metrics.py   # Prometheus metrics
│   │   └── main.py      # FastAPI app
│   ├── tests/           # ML tests
│   └── requirements.txt
│
├── infra/
│   └── docker/          # Docker Compose & configs
│       ├── compose.dev.yml   # Development stack
│       ├── compose.prod.yml  # Production stack
│       ├── nginx/           # Nginx configuration
│       ├── prometheus.yml   # Prometheus scrape config
│       ├── loki/           # Loki configuration
│       ├── promtail/       # Promtail configuration
│       └── grafana/        # Grafana provisioning
│
├── dataset/             # Movie scripts dataset
│   └── BERT_annotations/
│
├── .env.example         # Environment variables template
├── .gitignore
├── Makefile             # Dev commands
└── README.md
```

## API Endpoints

### Backend (`/api/v1`)
- `POST /scripts/` - Create script
- `POST /scripts/upload` - Upload script file (max 10MB)
- `GET /scripts/` - List all scripts (paginated)
- `GET /scripts/{id}` - Get script details with scenes
- `POST /scripts/{id}/rate` - Rate script (background=true for async)
- `GET /scripts/jobs/{job_id}/status` - Check rating job status

### Health & Metrics
- `GET /health` - Health check (DB + Redis connectivity)
- `GET /metrics` - Prometheus metrics
- `GET /` - API info

### ML Service
- `POST /rate_script` - Analyze and rate script
- `GET /health` - Health check
- `GET /metrics` - ML metrics

## Database Migrations

Create a new migration:
```bash
docker compose -f infra/docker/compose.dev.yml exec backend alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
docker compose -f infra/docker/compose.dev.yml exec backend alembic upgrade head
```

Rollback one migration:
```bash
docker compose -f infra/docker/compose.dev.yml exec backend alembic downgrade -1
```

## Testing

Run tests:
```bash
make test-ml        # ML service tests
make test-backend   # Backend tests
```

Run tests with coverage:
```bash
cd backend && pytest --cov=app tests/
cd ml_service && pytest --cov=app tests/
```

## Code Quality

Format code:
```bash
make format-ml      # Black + Ruff for ML code
make format-backend # Black + Ruff for backend code
```

Lint code:
```bash
cd backend && ruff check app/
cd ml_service && ruff check app/
cd frontend && npm run lint
```

## CI/CD

GitHub Actions workflows automatically:
- **Lint & Format Check** - Ruff, Black, ESLint
- **Run Tests** - pytest with coverage
- **Build Docker Images** - Multi-stage optimized builds
- **Push to GHCR** - GitHub Container Registry

Workflows trigger on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Path-specific triggers (backend/, frontend/, ml_service/)

## Monitoring

### Prometheus Metrics
- HTTP request duration and count
- Database connection pool stats
- ARQ job queue metrics
- ML inference latency

### Grafana Dashboards
- Backend API performance
- ML service metrics
- Database health
- Redis queue status

Access Grafana at http://localhost:3000 (admin/admin)

### Loki Logs
- Structured JSON logs from all services
- 7-day retention period
- Queryable via Grafana LogQL

## Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Database
POSTGRES_USER=rating_user
POSTGRES_PASSWORD=rating_pass
POSTGRES_DB=rating_db

# Backend
DATABASE_URL=postgresql+asyncpg://rating_user:rating_pass@postgres:5432/rating_db
REDIS_URL=redis://redis:6379/0
ML_SERVICE_URL=http://ml-service:8001
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
LOG_LEVEL=INFO

# ML Service
ML_LOG_LEVEL=INFO
ML_DEVICE=cpu
ML_ENABLE_METRICS=true

# Grafana
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=admin
```

## Production Deployment

1. Update `.env` with production values
2. Configure secrets management
3. Enable HTTPS in nginx
4. Use production compose file:

```bash
docker compose -f infra/docker/compose.prod.yml up -d
```

Production optimizations:
- Gunicorn with 4 workers
- Connection pooling (20+10)
- Nginx caching and gzip
- Health check monitoring
- Log aggregation with Loki

## Troubleshooting

### Backend not connecting to database
```bash
# Check database logs
docker compose -f infra/docker/compose.dev.yml logs postgres

# Verify database connection
docker compose -f infra/docker/compose.dev.yml exec backend python -c "from app.core.config import settings; print(settings.database_url)"
```

### Worker not processing jobs
```bash
# Check worker logs
docker compose -f infra/docker/compose.dev.yml logs worker

# Check Redis connection
docker compose -f infra/docker/compose.dev.yml exec redis redis-cli ping
```

### Check service health
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

## Dataset

Movie scripts from [Kaggle Movie Scripts Corpus](https://www.kaggle.com/datasets/gufukuro/movie-scripts-corpus)

## License

See [LICENSE](LICENSE)
