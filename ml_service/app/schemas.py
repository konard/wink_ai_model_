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


class WhatIfRequest(BaseModel):
    script_text: str = Field(..., min_length=10, description="Original script text")
    modification_request: str = Field(
        ...,
        min_length=3,
        description="What-if modification request (e.g., 'remove scene 12-13', 'replace fight with verbal conflict')",
    )


class WhatIfResponse(BaseModel):
    original_rating: str
    modified_rating: str
    original_scores: dict[str, float]
    modified_scores: dict[str, float]
    changes_applied: list[str]
    explanation: str
    rating_changed: bool


class EntityTargetSchema(BaseModel):
    entity_type: str = "all"
    entity_names: list[str] | None = None


class ModificationConfigSchema(BaseModel):
    type: str = Field(..., description="Type of modification")
    params: dict = Field(default_factory=dict)
    targets: EntityTargetSchema | None = None
    scope: list[int] | None = None


class StructuredWhatIfRequest(BaseModel):
    script_text: str = Field(..., min_length=10)
    modifications: list[ModificationConfigSchema]
    use_llm: bool = False
    llm_provider: str | None = None
    preserve_structure: bool = True


class EntityInfoSchema(BaseModel):
    type: str
    name: str
    mentions: int
    scenes: list[int]


class SceneInfoSchema(BaseModel):
    scene_id: int
    scene_type: str
    characters: list[str]
    location: str | None
    summary: str | None


class AdvancedWhatIfResponse(BaseModel):
    original_rating: str
    modified_rating: str
    original_scores: dict[str, float]
    modified_scores: dict[str, float]
    modifications_applied: list[dict]
    entities_extracted: list[EntityInfoSchema]
    scene_analysis: list[SceneInfoSchema]
    explanation: str
    modified_script: str | None = None
    rating_changed: bool
