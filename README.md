# Movie Script Rating System

Automated system for analyzing movie scripts and predicting age-appropriate ratings based on content analysis.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend    │────▶│ ML Service  │
│ React/Vite  │     │   FastAPI    │     │   PyTorch   │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
               ┌────▼───┐    ┌────▼───┐
               │PostgreSQL│   │  Redis  │
               └────────┘    └─────────┘
```

## Tech Stack

### Backend
- **FastAPI** - REST API framework
- **SQLAlchemy** - ORM for PostgreSQL
- **Redis + RQ** - Background job processing
- **Uvicorn/Gunicorn** - ASGI server

### ML Service
- **PyTorch** - Deep learning framework
- **Sentence Transformers** - Text embeddings
- **UMAP + HDBSCAN** - Clustering algorithms
- **FastAPI** - ML inference API

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **TanStack Query** - Data fetching
- **Recharts** - Visualizations

### Infrastructure
- **Docker + Docker Compose** - Containerization
- **PostgreSQL** - Database
- **Redis** - Cache & job queue
- **GitHub Actions** - CI/CD

## Quick Start

### Prerequisites
- Docker & Docker Compose
- (Optional) Node.js 20+, Python 3.12+ for local development

### Development Setup

1. Clone the repository

2. Copy environment files:
```bash
cp .env.example .env
```

3. Start all services:
```bash
make dev-up
```

4. Access the services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs
- ML Service: http://localhost:8001/docs

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

## Project Structure

```
.
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Configuration
│   │   ├── db/          # Database setup
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── alembic/         # Database migrations
│   └── requirements.txt
│
├── frontend/            # React frontend
│   ├── src/
│   │   ├── api/         # API client
│   │   ├── components/  # React components
│   │   └── App.tsx
│   └── package.json
│
├── ml_service/          # ML inference service
│   ├── app/
│   │   ├── config.py    # ML configuration
│   │   ├── pipeline.py  # Rating pipeline
│   │   ├── schemas.py   # API schemas
│   │   └── main.py      # FastAPI app
│   └── requirements.txt
│
├── infra/
│   └── docker/          # Docker Compose files
│       ├── compose.dev.yml
│       └── compose.prod.yml
│
├── dataset/             # Movie scripts dataset
│   └── BERT_annotations/
│
└── Makefile             # Dev commands
```

## API Endpoints

### Backend (`/api/v1`)
- `POST /scripts/` - Create script
- `POST /scripts/upload` - Upload script file
- `GET /scripts/` - List all scripts
- `GET /scripts/{id}` - Get script details
- `POST /scripts/{id}/rate` - Rate script (async or sync)
- `GET /scripts/jobs/{job_id}/status` - Check rating job status

### ML Service
- `POST /rate_script` - Analyze and rate script
- `GET /health` - Health check

## Database Migrations

Create a new migration:
```bash
docker compose -f infra/docker/compose.dev.yml exec backend alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
docker compose -f infra/docker/compose.dev.yml exec backend alembic upgrade head
```

## Testing

Run tests:
```bash
make test-ml        # ML service tests
make test-backend   # Backend tests
```

## Code Formatting

Format code:
```bash
make format-ml      # Format ML code
make format-backend # Format backend code
```

## CI/CD

GitHub Actions workflows automatically:
- Run tests and linting
- Build Docker images
- Push to GitHub Container Registry

Workflows trigger on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

## Dataset

Movie scripts from [Kaggle Movie Scripts Corpus](https://www.kaggle.com/datasets/gufukuro/movie-scripts-corpus)

## License

See [LICENSE](LICENSE)