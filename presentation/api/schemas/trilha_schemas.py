"""
Pydantic schemas for trilha-related API endpoints.
Presentation Layer - API Package
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ConteudoBase(BaseModel):
    """Base schema for content."""
    titulo: str = Field(..., min_length=1, max_length=200, description="Content title")
    tipo: str = Field(..., description="Content type: video, text, quiz, exercise")
    material: Optional[str] = Field(None, description="Content material or path")

class ConteudoCreate(ConteudoBase):
    """Schema for content creation."""
    pass

class ConteudoResponse(ConteudoBase):
    """Schema for content response."""
    id: int
    trilha_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    progress: Optional[Dict[str, Any]] = None  # User progress if available

    class Config:
        from_attributes = True

class TrilhaBase(BaseModel):
    """Base schema for trilha."""
    titulo: str = Field(..., min_length=1, max_length=200, description="Trilha title")
    dificuldade: str = Field(..., description="Difficulty level: beginner, intermediate, advanced")

class TrilhaCreate(TrilhaBase):
    """Schema for trilha creation."""
    pass

class TrilhaUpdate(BaseModel):
    """Schema for trilha updates."""
    titulo: Optional[str] = Field(None, min_length=1, max_length=200, description="Trilha title")
    dificuldade: Optional[str] = Field(None, description="Difficulty level: beginner, intermediate, advanced")

class TrilhaResponse(TrilhaBase):
    """Schema for trilha response."""
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class TrilhaDetailResponse(TrilhaResponse):
    """Schema for detailed trilha response with content."""
    content_count: int
    conteudos: List[ConteudoResponse]

class TrilhaEnrollmentRequest(BaseModel):
    """Schema for trilha enrollment."""
    user_id: int = Field(..., description="User ID to enroll")

class TrilhaEnrollmentResponse(BaseModel):
    """Schema for enrollment response."""
    user_id: int
    trilha_id: int
    enrolled_at: str
    message: str

class TrilhaStatsResponse(BaseModel):
    """Schema for trilha statistics."""
    trilha_id: int
    titulo: str
    dificuldade: str
    total_enrollments: int
    total_content_items: int
    average_progress: float
    average_grade: float
    completion_rate: float
    total_study_time_hours: float

class PopularTrilhaResponse(BaseModel):
    """Schema for popular trilhas."""
    id: int
    titulo: str
    dificuldade: str
    enrollment_count: int

class TrilhaSearchResponse(BaseModel):
    """Schema for trilha search results."""
    trilhas: List[TrilhaResponse]
    count: int

class ProgressUpdateRequest(BaseModel):
    """Schema for progress update."""
    user_id: int = Field(..., description="User ID")
    conteudo_id: int = Field(..., description="Content ID")
    progresso: float = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    nota: Optional[float] = Field(None, ge=0, le=100, description="Grade/score (0-100)")
    tempo_estudo: Optional[int] = Field(None, ge=0, description="Study time in minutes")

class ProgressResponse(BaseModel):
    """Schema for progress response."""
    id: int
    user_id: int
    conteudo_id: int
    progresso: float
    nota: Optional[float]
    tempo_estudo: int
    updated_at: Optional[datetime]

class UserTrilhaProgressResponse(BaseModel):
    """Schema for user's trilha progress."""
    user_id: int
    trilha_id: int
    total_content: int
    completed_content: int
    completion_rate: float
    average_progress: float
    average_grade: float
    total_study_time_hours: float

