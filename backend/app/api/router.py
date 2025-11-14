from fastapi import APIRouter
from .endpoints import scripts

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(scripts.router)
