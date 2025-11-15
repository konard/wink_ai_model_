from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class EntityTarget(BaseModel):
    entity_type: Literal["character", "location", "object", "all"] = "all"
    entity_names: Optional[List[str]] = None


class ModificationConfig(BaseModel):
    type: str = Field(..., description="Type of modification to apply")
    params: Dict[str, Any] = Field(default_factory=dict)
    targets: Optional[EntityTarget] = None
    scope: Optional[List[int]] = Field(None, description="Scene IDs to apply modification to")


class StructuredWhatIfRequest(BaseModel):
    script_text: str
    modifications: List[ModificationConfig]
    use_llm: bool = Field(default=False, description="Use LLM for intelligent rewrites")
    llm_provider: Optional[str] = Field(default=None, description="LLM provider (openai, anthropic, local)")
    preserve_structure: bool = Field(default=True, description="Preserve script formatting")


class EntityInfo(BaseModel):
    type: str
    name: str
    mentions: int
    scenes: List[int]


class SceneInfo(BaseModel):
    scene_id: int
    scene_type: str
    characters: List[str]
    location: Optional[str]
    summary: Optional[str]


class AdvancedWhatIfResponse(BaseModel):
    original_rating: str
    modified_rating: str
    original_scores: Dict[str, float]
    modified_scores: Dict[str, float]
    modifications_applied: List[Dict[str, Any]]
    entities_extracted: List[EntityInfo]
    scene_analysis: List[SceneInfo]
    explanation: str
    modified_script: Optional[str] = None
    rating_changed: bool
