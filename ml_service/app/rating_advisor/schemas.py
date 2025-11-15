from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal


class RecommendationAction(BaseModel):
    action_type: Literal[
        "remove_scene", "reduce_content", "modify_dialogue", "rewrite_scene"
    ]
    scene_id: int
    description: str
    impact_score: float = Field(..., ge=0, le=1)
    category: str
    specific_changes: List[str]
    difficulty: Literal["easy", "medium", "hard"]


class SceneIssue(BaseModel):
    scene_id: int
    scene_number: int
    content_preview: str
    issues: Dict[str, float]
    severity: Literal["critical", "high", "medium", "low"]
    recommendations: List[str]


class RatingGap(BaseModel):
    dimension: str
    current_score: float
    target_score: float
    gap: float
    priority: Literal["critical", "high", "medium", "low"]


class RatingAdvisorRequest(BaseModel):
    script_text: str
    current_rating: Optional[str] = None
    target_rating: str = Field(..., pattern="^(0\\+|6\\+|12\\+|16\\+|18\\+)$")
    language: Literal["en", "ru"] = "en"
    include_rewrites: bool = False


class RatingAdvisorResponse(BaseModel):
    current_rating: str
    target_rating: str
    is_achievable: bool
    confidence: float = Field(..., ge=0, le=1)

    current_scores: Dict[str, float]
    target_scores: Dict[str, float]
    rating_gaps: List[RatingGap]

    problematic_scenes: List[SceneIssue]
    recommended_actions: List[RecommendationAction]

    summary: str
    estimated_effort: Literal["minimal", "moderate", "significant", "extensive"]

    alternative_targets: Optional[List[str]] = None
