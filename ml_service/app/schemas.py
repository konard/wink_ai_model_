from pydantic import BaseModel, Field


class ScriptRequest(BaseModel):
    script_id: str | None = None
    text: str = Field(..., min_length=10, description="Full movie script text")


class SceneRecommendation(BaseModel):
    scene_id: int
    heading: str
    recommendations: list[str]


class SceneFeatures(BaseModel):
    scene_id: int
    heading: str
    violence: float = Field(ge=0, le=1)
    gore: float = Field(ge=0, le=1)
    sex_act: float = Field(ge=0, le=1)
    nudity: float = Field(ge=0, le=1)
    profanity: float = Field(ge=0, le=1)
    drugs: float = Field(ge=0, le=1)
    child_risk: float = Field(ge=0, le=1)
    weight: float
    sample_text: str | None = None
    recommendations: list[str] = Field(default_factory=list)


class ScriptRatingResponse(BaseModel):
    script_id: str | None
    predicted_rating: str = Field(..., pattern="^(0\\+|6\\+|12\\+|16\\+|18\\+)$")
    reasons: list[str]
    agg_scores: dict[str, float]
    top_trigger_scenes: list[SceneFeatures]
    model_version: str
    total_scenes: int
    evidence_excerpts: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    model_version: str
    model_loaded: bool
