"""
Pydantic schemas for user-related API endpoints.
Presentation Layer - API Package
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    """Schema for user creation."""
    nome: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    senha: str = Field(..., min_length=6, description="User's password")
    perfil_aprend: Optional[str] = Field("beginner", description="Learning profile: beginner, intermediate, advanced")

class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

class UserUpdate(BaseModel):
    """Schema for user updates."""
    nome: Optional[str] = Field(None, min_length=2, max_length=100, description="User's full name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    perfil_aprend: Optional[str] = Field(None, description="Learning profile: beginner, intermediate, advanced")

class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    nome: str
    email: str
    perfil_aprend: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class TrilhaInfo(BaseModel):
    """Schema for trilha information in user responses."""
    id: int
    titulo: str
    dificuldade: str

class UserProfileResponse(BaseModel):
    """Schema for detailed user profile response."""
    id: int
    nome: str
    email: str
    perfil_aprend: Optional[str]
    created_at: Optional[datetime]
    enrolled_trilhas: List[TrilhaInfo]
    progress_summary: Dict[str, Any]
    learning_analytics: Dict[str, Any]

class UserSearchResponse(BaseModel):
    """Schema for user search results."""
    users: List[UserResponse]
    count: int

class UserRecommendationsResponse(BaseModel):
    """Schema for user recommendations."""
    user_id: int
    recommendations: List[Dict[str, Any]]
    generated_at: str

class APIResponse(BaseModel):
    """Generic API response schema."""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
