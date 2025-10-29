from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ========== INPUT SCHEMAS ==========

class GenerateWarningsRequest(BaseModel):
    """Request to generate warnings for a persona structure"""
    persona_data: dict = Field(..., description="Full PersonaCreate structure (not saved yet)")
    
    model_config = ConfigDict(from_attributes=True)


class GetWarningRequest(BaseModel):
    """Query parameters to fetch specific warning"""
    persona_id: str = Field(..., description="Persona ID or 'preview' for unsaved personas")
    entity_type: str = Field(..., description="'category' or 'subcategory'")
    entity_name: str = Field(..., description="Name of the entity")
    violation_type: str = Field(..., description="'below_min' or 'above_max'")
    
    model_config = ConfigDict(from_attributes=True)

class GetOrGenerateWarningRequest(BaseModel):
    """Request to get warning (generates if missing) - single entity on-demand"""
    persona_id: Optional[str] = Field(None, description="Persona ID. If null, backend generates new preview ID")
    entity_type: str = Field(..., description="'category' or 'subcategory'")
    entity_name: str = Field(..., description="Name of the violated entity")
    violation_type: str = Field(..., description="'below_min' or 'above_max'")
    entity_data: Optional[dict] = Field(
        None,  # ✅ NOW OPTIONAL
        description=(
            "Entity info (REQUIRED if generating for first time, OPTIONAL if cached). "
            "Must include: {name, weight, range_min, range_max, technologies, level_id (for subcategories)}"
        )
    )
    
    model_config = ConfigDict(from_attributes=True)
class LinkWarningsRequest(BaseModel):
    """Request to link preview warnings to saved persona"""
    temp_persona_id: str = Field(..., description="Temporary preview persona ID", examples=["preview-a1b2c3d4"])
    saved_persona_id: str = Field(..., description="Actual saved persona ID", examples=["persona-uuid-123"])
    
    model_config = ConfigDict(from_attributes=True)


# ========== OUTPUT SCHEMAS ==========

class WarningMessage(BaseModel):
    """Single warning for an entity"""
    entity_type: str
    entity_name: str
    below_min_message: str
    above_max_message: str
    
    model_config = ConfigDict(from_attributes=True)


class GenerateWarningsResponse(BaseModel):
    """Response after generating all warnings"""
    persona_id: str  # Temporary ID for preview
    total_warnings: int
    warnings: List[WarningMessage]
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class GetWarningResponse(BaseModel):
    """Response with warning message (single entity)"""
    persona_id: str  # Always return the persona_id (generated or existing)
    entity_type: str
    entity_name: str
    violation_type: str
    message: str
    generated_now: bool = False  # True if just generated
    
    model_config = ConfigDict(from_attributes=True)


class PersonaWarningRead(BaseModel):
    """Read single warning from DB"""
    id: str
    persona_id: Optional[str] = None
    entity_type: str
    entity_name: str
    below_min_message: str
    above_max_message: str
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class LinkWarningsResponse(BaseModel):
    """Response after linking warnings"""
    temp_persona_id: str
    saved_persona_id: str
    warnings_linked: int
    
    model_config = ConfigDict(from_attributes=True)