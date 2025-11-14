from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ...db.base import get_db
from ...schemas.script import (
    ScriptCreate,
    ScriptResponse,
    ScriptDetailResponse,
    RatingJobResponse,
)
from ...services.script_service import script_service
from ...services.queue import enqueue_rating_job, get_job_status

router = APIRouter(prefix="/scripts", tags=["scripts"])


@router.post("/", response_model=ScriptResponse, status_code=201)
async def create_script(script: ScriptCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_script = await script_service.create_script(db, script)
        return new_script
    except Exception as e:
        logger.error(f"Error creating script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=ScriptResponse, status_code=201)
async def upload_script(
    file: UploadFile = File(...), title: str = None, db: AsyncSession = Depends(get_db)
):
    try:
        content = await file.read()
        text = content.decode("utf-8")

        script_title = title or file.filename or "Untitled Script"
        script_data = ScriptCreate(title=script_title, content=text)

        new_script = await script_service.create_script(db, script_data)
        return new_script
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text")
    except Exception as e:
        logger.error(f"Error uploading script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[ScriptResponse])
async def list_scripts(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    scripts = await script_service.list_scripts(db, skip, limit)
    return scripts


@router.get("/{script_id}", response_model=ScriptDetailResponse)
async def get_script(script_id: int, db: AsyncSession = Depends(get_db)):
    script = await script_service.get_script(db, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@router.post("/{script_id}/rate", response_model=RatingJobResponse)
async def rate_script(
    script_id: int, background: bool = True, db: AsyncSession = Depends(get_db)
):
    script = await script_service.get_script(db, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    if background:
        job_id = enqueue_rating_job(script_id)
        return RatingJobResponse(
            job_id=job_id,
            script_id=script_id,
            status="queued",
            message="Rating job has been queued",
        )
    else:
        try:
            await script_service.process_rating(db, script_id)
            return RatingJobResponse(
                job_id="sync",
                script_id=script_id,
                status="completed",
                message="Rating completed synchronously",
            )
        except Exception as e:
            logger.error(f"Sync rating failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/status")
async def get_rating_job_status(job_id: str):
    status = get_job_status(job_id)
    return status
