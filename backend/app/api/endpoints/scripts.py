from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.base import get_db
from ...schemas.script import (
    ScriptCreate,
    ScriptResponse,
    ScriptDetailResponse,
    RatingJobResponse,
    WhatIfRequest,
    WhatIfResponse,
)
from ...services.script_service import script_service
from ...services.ml_client import ml_client
from ...services.queue import enqueue_rating_job, get_job_status
from ...services.pdf_generator import PDFReportGenerator
from ...services.export_service import ExportService
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
    file: UploadFile = File(...),
    title: str = Form(None),
    db: AsyncSession = Depends(get_db),
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


@router.post("/{script_id}/what-if", response_model=WhatIfResponse)
async def what_if_analysis(
    script_id: int, request: WhatIfRequest, db: AsyncSession = Depends(get_db)
):
    script = await script_service.get_script(db, script_id)
    if not script:
        raise ScriptNotFoundError(script_id)

    result = await ml_client.what_if_analysis(
        script_text=str(script.content),
        modification_request=request.modification_request,
    )

    return WhatIfResponse(**result)


@router.get("/{script_id}/export/pdf")
async def export_pdf(script_id: int, db: AsyncSession = Depends(get_db)):
    script = await script_service.get_script(db, script_id)
    if not script:
        raise ScriptNotFoundError(script_id)

    generator = PDFReportGenerator(language="ru")
    pdf_buffer = generator.generate_report(
        script=script,
        scenes=script.scenes or []
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=rating_report_{script_id}.pdf"
        }
    )


@router.get("/{script_id}/export/excel")
async def export_excel(script_id: int, db: AsyncSession = Depends(get_db)):
    script = await script_service.get_script(db, script_id)
    if not script:
        raise ScriptNotFoundError(script_id)

    excel_buffer = ExportService.export_to_excel(
        script=script,
        scenes=script.scenes or []
    )

    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=rating_report_{script_id}.xlsx"
        }
    )


@router.get("/{script_id}/export/csv")
async def export_csv(script_id: int, db: AsyncSession = Depends(get_db)):
    script = await script_service.get_script(db, script_id)
    if not script:
        raise ScriptNotFoundError(script_id)

    csv_output = ExportService.export_to_csv(
        script=script,
        scenes=script.scenes or []
    )

    return StreamingResponse(
        csv_output,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=rating_report_{script_id}.csv"
        }
    )
