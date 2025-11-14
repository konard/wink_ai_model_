from pydantic import BaseModel, Field
from datetime import datetime


class ScriptCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=10)


class SceneResponse(BaseModel):
    id: int
    scene_id: int
    heading: str
    violence: float
    gore: float
    sex_act: float
    nudity: float
    profanity: float
    drugs: float
    child_risk: float
    weight: float
    sample_text: str | None

    class Config:
        from_attributes = True


class ScriptResponse(BaseModel):
    id: int
    title: str
    predicted_rating: str | None
    agg_scores: dict | None
    model_version: str | None
    total_scenes: int | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class ScriptDetailResponse(ScriptResponse):
    scenes: list[SceneResponse] = []


class RatingJobResponse(BaseModel):
    job_id: str
    script_id: int
    status: str
    message: str


class RatingResultResponse(BaseModel):
    script_id: int
    predicted_rating: str
    reasons: list[str]
    agg_scores: dict
    top_trigger_scenes: list[SceneResponse]
    model_version: str
    total_scenes: int
