from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from .schemas import ScriptRequest, ScriptRatingResponse, HealthResponse
from .pipeline import get_pipeline
from .config import settings

logger.remove()
logger.add(sys.stderr, level=settings.log_level)

app = FastAPI(
    title="Movie Script Rating Service",
    description="ML service for analyzing movie scripts and predicting age ratings",
    version=settings.model_version
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health():
    try:
        pipeline = get_pipeline()
        return HealthResponse(
            status="healthy",
            model_version=settings.model_version,
            model_loaded=pipeline is not None
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.post("/rate_script", response_model=ScriptRatingResponse)
async def rate_script(request: ScriptRequest):
    try:
        pipeline = get_pipeline()
        result = pipeline.analyze_script(request.text, request.script_id)
        return ScriptRatingResponse(**result)
    except Exception as e:
        logger.error(f"Error processing script: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/")
async def root():
    return {
        "service": settings.service_name,
        "version": settings.model_version,
        "endpoints": {
            "health": "/health",
            "rate_script": "/rate_script",
            "docs": "/docs"
        }
    }
