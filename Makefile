.PHONY: help dev-up dev-down dev-logs dev-ml dev-backend dev-frontend prod-up prod-down clean

help:
	@echo "Movie Rating Service - Development Commands"
	@echo ""
	@echo "  make dev-up          - Start all dev services"
	@echo "  make dev-down        - Stop all dev services"
	@echo "  make dev-logs        - Follow logs for all services"
	@echo "  make dev-ml          - Start only ML service (for ML dev)"
	@echo "  make dev-backend     - Start backend + deps (for backend dev)"
	@echo "  make dev-frontend    - Start frontend + deps (for frontend dev)"
	@echo "  make prod-up         - Start production services"
	@echo "  make prod-down       - Stop production services"
	@echo "  make clean           - Remove all containers and volumes"
	@echo "  make test-ml         - Run ML service tests"
	@echo "  make test-backend    - Run backend tests"
	@echo "  make format-ml       - Format ML code"
	@echo "  make format-backend  - Format backend code"

dev-up:
	docker compose -f infra/docker/compose.dev.yml up -d

dev-down:
	docker compose -f infra/docker/compose.dev.yml down

dev-logs:
	docker compose -f infra/docker/compose.dev.yml logs -f

dev-ml:
	docker compose -f infra/docker/compose.dev.yml up -d postgres redis ml-service
	@echo "ML service available at http://localhost:8001/docs"

dev-backend:
	docker compose -f infra/docker/compose.dev.yml up -d postgres redis ml-service backend worker
	@echo "Backend available at http://localhost:8000/docs"

dev-frontend:
	docker compose -f infra/docker/compose.dev.yml up -d postgres redis ml-service backend worker frontend
	@echo "Frontend available at http://localhost:5173"

prod-up:
	docker compose -f infra/docker/compose.prod.yml up -d

prod-down:
	docker compose -f infra/docker/compose.prod.yml down

clean:
	docker compose -f infra/docker/compose.dev.yml down -v
	docker compose -f infra/docker/compose.prod.yml down -v

test-ml:
	cd ml_service && pytest

test-backend:
	cd backend && pytest

format-ml:
	cd ml_service && ruff check . && black .

format-backend:
	cd backend && ruff check . && black .
