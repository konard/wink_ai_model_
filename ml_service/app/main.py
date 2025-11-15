from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .schemas import (
    ScriptRequest,
    ScriptRatingResponse,
    HealthResponse,
    WhatIfRequest,
    WhatIfResponse,
    StructuredWhatIfRequest,
    AdvancedWhatIfResponse,
)
from .pipeline import get_pipeline
from .what_if import get_what_if_analyzer
from .what_if_advanced import get_advanced_analyzer
from .what_if_advanced.schemas import StructuredWhatIfRequest as InternalStructuredRequest
from .config import settings
from .metrics import get_metrics, track_inference_time
from .structured_logger import setup_structured_logging

setup_structured_logging(json_logs=settings.json_logs)

app = FastAPI(
    title="Movie Script Rating Service",
    description="ML service for analyzing movie scripts and predicting age ratings",
    version=settings.model_version,
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
            model_loaded=pipeline is not None,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.post("/rate_script", response_model=ScriptRatingResponse)
@track_inference_time("rate_script")
async def rate_script(request: ScriptRequest):
    try:
        pipeline = get_pipeline()
        result = pipeline.analyze_script(request.text, request.script_id)
        return ScriptRatingResponse(**result)
    except Exception as e:
        logger.error(f"Error processing script: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if not settings.enable_metrics:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    return Response(content=get_metrics(), media_type="text/plain")


@app.post("/what_if", response_model=WhatIfResponse)
@track_inference_time("what_if")
async def what_if_simulation(request: WhatIfRequest):
    try:
        analyzer = get_what_if_analyzer()
        result = analyzer.simulate_what_if(
            request.script_text, request.modification_request
        )
        return WhatIfResponse(**result)
    except Exception as e:
        logger.error(f"Error processing what-if request: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.post("/what_if_advanced", response_model=AdvancedWhatIfResponse)
@track_inference_time("what_if_advanced")
async def what_if_advanced_simulation(request: StructuredWhatIfRequest):
    try:
        use_llm = request.use_llm
        llm_provider = request.llm_provider

        analyzer = get_advanced_analyzer(
            use_llm=use_llm,
            llm_provider=llm_provider,
        )

        internal_request = InternalStructuredRequest(**request.model_dump())

        result = analyzer.analyze_structured(internal_request)

        return AdvancedWhatIfResponse(**result.model_dump())
    except Exception as e:
        logger.error(f"Error processing advanced what-if request: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/")
async def root():
    return {
        "service": settings.service_name,
        "version": settings.model_version,
        "endpoints": {
            "health": "/health",
            "rate_script": "/rate_script",
            "what_if": "/what_if",
            "what_if_advanced": "/what_if_advanced",
            "metrics": "/metrics",
            "docs": "/docs",
        },
    }
