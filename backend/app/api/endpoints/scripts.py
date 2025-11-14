from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.base import get_db
from ...schemas.script import (
    ScriptCreate,
    ScriptResponse,
    ScriptDetailResponse,
    RatingJobResponse,
)
from ...services.script_service import script_service
from ...services.queue import enqueue_rating_job, get_job_status
from ...core.exceptions import (
    ScriptNotFoundError,
    InvalidFileError,
    FileTooLargeError,
)
from ...core.config import settings

router = APIRouter(prefix="/scripts", tags=["scripts"])


@router.post("/", response_model=ScriptResponse, status_code=201)
async def create_script(script: ScriptCreate, db: AsyncSession = Depends(get_db)):
    new_script = await script_service.create_script(db, script)
    return new_script


@router.post("/upload", response_model=ScriptResponse, status_code=201)
async def upload_script(
    file: UploadFile = File(...), title: str = None, db: AsyncSession = Depends(get_db)
):
    if not file.filename:
        raise InvalidFileError("Filename is required")

    file_extension = "." + file.filename.split(".")[-1].lower()
    if file_extension not in settings.allowed_file_extensions:
        raise InvalidFileError(
            f"File type {file_extension} not allowed. Allowed types: {', '.join(settings.allowed_file_extensions)}"
        )

    content = await file.read()

    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise FileTooLargeError(settings.max_upload_size_mb)

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise InvalidFileError("File must be UTF-8 encoded text")

    script_title = title or file.filename or "Untitled Script"
    script_data = ScriptCreate(title=script_title, content=text)

    new_script = await script_service.create_script(db, script_data)
    return new_script


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
        raise ScriptNotFoundError(script_id)
    return script


@router.post("/{script_id}/rate", response_model=RatingJobResponse)
async def rate_script(
    script_id: int, background: bool = True, db: AsyncSession = Depends(get_db)
):
    script = await script_service.get_script(db, script_id)
    if not script:
        raise ScriptNotFoundError(script_id)

    if background:
        job_id = await enqueue_rating_job(script_id)
        return RatingJobResponse(
            job_id=job_id,
            script_id=script_id,
            status="queued",
            message="Rating job has been queued",
        )
    else:
        await script_service.process_rating(db, script_id)
        return RatingJobResponse(
            job_id="sync",
            script_id=script_id,
            status="completed",
            message="Rating completed synchronously",
        )


@router.get("/jobs/{job_id}/status")
async def get_rating_job_status(job_id: str):
    status = await get_job_status(job_id)
    return status
