from fastapi import APIRouter
from .endpoints import scripts, versions

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(scripts.router)
api_router.include_router(versions.router, prefix="/scripts", tags=["versions"])
