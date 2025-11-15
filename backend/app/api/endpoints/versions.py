from typing import List, cast
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...services.version_service import VersionService
from ...schemas.version import (
    VersionCreate,
    VersionResponse,
    VersionCompareResponse,
    VersionListResponse,
)

router = APIRouter()


@router.post("/{script_id}/versions", response_model=VersionResponse)
async def create_version(
    script_id: int, version_data: VersionCreate, db: AsyncSession = Depends(get_db)
):
    try:
        version = await VersionService.create_version(
            db,
            script_id,
            change_description=version_data.change_description,
            make_current=version_data.make_current,
        )

        return VersionResponse(
            id=int(version.id),
            script_id=int(version.script_id),
            version_number=int(version.version_number),
            title=str(version.title),
            predicted_rating=str(version.predicted_rating),
            agg_scores=dict(version.agg_scores or {}),
            total_scenes=int(version.total_scenes or 0),
            change_description=str(version.change_description),
            is_current=bool(version.is_current or False),
            created_at=cast(datetime, version.created_at),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create version: {str(e)}"
        )


@router.get("/{script_id}/versions", response_model=List[VersionListResponse])
async def get_versions(script_id: int, db: AsyncSession = Depends(get_db)):
    try:
        versions = await VersionService.get_versions(db, script_id)
        return [
            VersionListResponse(
                id=int(v.id),
                version_number=int(v.version_number),
                title=str(v.title),
                predicted_rating=str(v.predicted_rating),
                total_scenes=int(v.total_scenes or 0),
                change_description=str(v.change_description),
                is_current=bool(v.is_current or False),
                created_at=cast(datetime, v.created_at),
            )
            for v in versions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get versions: {str(e)}")


@router.get("/{script_id}/versions/{version_number}", response_model=VersionResponse)
async def get_version(
    script_id: int, version_number: int, db: AsyncSession = Depends(get_db)
):
    try:
        version = await VersionService.get_version(db, script_id, version_number)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

        return VersionResponse(
            id=int(version.id),
            script_id=int(version.script_id),
            version_number=int(version.version_number),
            title=str(version.title),
            predicted_rating=str(version.predicted_rating),
            agg_scores=dict(version.agg_scores or {}),
            total_scenes=int(version.total_scenes or 0),
            change_description=str(version.change_description),
            is_current=bool(version.is_current or False),
            created_at=cast(datetime, version.created_at),
            content=str(version.content),
            scenes_data=list(version.scenes_data) if version.scenes_data else [],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get version: {str(e)}")


@router.post("/{script_id}/versions/{version_number}/restore")
async def restore_version(
    script_id: int, version_number: int, db: AsyncSession = Depends(get_db)
):
    try:
        script = await VersionService.restore_version(db, script_id, version_number)
        return {
            "message": f"Successfully restored to version {version_number}",
            "script_id": script.id,
            "current_version": script.current_version,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to restore version: {str(e)}"
        )


@router.get(
    "/{script_id}/versions/compare/{version1}/{version2}",
    response_model=VersionCompareResponse,
)
async def compare_versions(
    script_id: int, version1: int, version2: int, db: AsyncSession = Depends(get_db)
):
    try:
        v1 = await VersionService.get_version(db, script_id, version1)
        v2 = await VersionService.get_version(db, script_id, version2)

        if not v1 or not v2:
            raise HTTPException(
                status_code=404, detail="One or both versions not found"
            )

        comparison = VersionService.compare_versions(v1, v2)
        return VersionCompareResponse(**comparison)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to compare versions: {str(e)}"
        )


@router.delete("/{script_id}/versions/{version_number}")
async def delete_version(
    script_id: int, version_number: int, db: AsyncSession = Depends(get_db)
):
    try:
        success = await VersionService.delete_version(db, script_id, version_number)
        if not success:
            raise HTTPException(status_code=404, detail="Version not found")

        return {"message": f"Version {version_number} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete version: {str(e)}"
        )
