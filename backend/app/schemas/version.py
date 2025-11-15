from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class VersionCreate(BaseModel):
    change_description: Optional[str] = None
    make_current: bool = True


class VersionListResponse(BaseModel):
    id: int
    version_number: int
    title: str
    predicted_rating: Optional[str]
    total_scenes: int
    change_description: Optional[str]
    is_current: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class VersionResponse(VersionListResponse):
    script_id: int
    agg_scores: Dict[str, float]
    content: Optional[str] = None
    scenes_data: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True


class VersionCompareResponse(BaseModel):
    version1: Dict[str, Any]
    version2: Dict[str, Any]
    changes: Dict[str, Any]
