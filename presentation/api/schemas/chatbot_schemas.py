"""
Pydantic schemas for chatbot-related API endpoints.
Presentation Layer - API Package
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    """Schema for chat message."""
    message: str = Field(..., min_length=1, max_length=1000, description="User's message")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the conversation")

class ChatResponse(BaseModel):
    """Schema for chatbot response."""
    response: str = Field(..., description="Chatbot's response")
    metadata: Dict[str, Any] = Field(..., description="Response metadata including intent, confidence, etc.")

class ConversationHistory(BaseModel):
    """Schema for conversation history entry."""
    timestamp: str
    user_message: str
    bot_response: str
    intent: str

class ConversationHistoryResponse(BaseModel):
    """Schema for conversation history response."""
    user_id: int
    conversation_count: int
    history: List[ConversationHistory]

class RecommendationRequest(BaseModel):
    """Schema for recommendation request."""
    user_id: int = Field(..., description="User ID for personalized recommendations")
    limit: Optional[int] = Field(10, ge=1, le=50, description="Maximum number of recommendations")

class ContentRecommendation(BaseModel):
    """Schema for content recommendation."""
    type: str = Field(..., description="Recommendation type")
    id: int = Field(..., description="Content ID")
    titulo: str = Field(..., description="Content title")
    dificuldade: str = Field(..., description="Difficulty level")
    reason: str = Field(..., description="Reason for recommendation")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    source: str = Field(..., description="Recommendation source")

class HabitRecommendation(BaseModel):
    """Schema for learning habit recommendation."""
    type: str = Field(..., description="Habit type")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Recommendation description")
    current_value: str = Field(..., description="Current user value")
    target_value: str = Field(..., description="Target value")
    priority: str = Field(..., description="Priority level")

class StructuredRecommendations(BaseModel):
    """Schema for structured recommendations."""
    content_recommendations: List[ContentRecommendation]
    habit_recommendations: List[HabitRecommendation]
    ai_insights: str
    total_recommendations: int

class AIRecommendationResponse(BaseModel):
    """Schema for AI recommendation response."""
    user_id: int
    ai_recommendations: str
    structured_recommendations: StructuredRecommendations
    generated_at: str
    model_used: str

class LearningAnalysisRequest(BaseModel):
    """Schema for learning pattern analysis request."""
    user_id: int = Field(..., description="User ID for analysis")
    period_days: Optional[int] = Field(30, ge=1, le=365, description="Analysis period in days")

class LearningStrength(BaseModel):
    """Schema for learning strength."""
    area: str
    description: str

class LearningImprovement(BaseModel):
    """Schema for learning improvement area."""
    area: str
    description: str
    suggestion: str

class LearningAnalysis(BaseModel):
    """Schema for learning pattern analysis."""
    user_id: int
    learning_style: str
    strengths: List[str]
    areas_for_improvement: List[str]
    ai_insights: str
    analysis_date: str

class LearningAnalysisResponse(BaseModel):
    """Schema for learning analysis response."""
    analysis: LearningAnalysis

class ExternalContentSearch(BaseModel):
    """Schema for external content search."""
    query: str = Field(..., min_length=2, max_length=100, description="Search query")
    content_type: Optional[str] = Field(None, description="Content type filter")
    difficulty: Optional[str] = Field(None, description="Difficulty level filter")
    limit: Optional[int] = Field(20, ge=1, le=100, description="Maximum results")

class ExternalContent(BaseModel):
    """Schema for external content item."""
    id: str
    title: str
    description: str
    content_type: str
    difficulty: str
    duration_minutes: int
    provider: str
    url: str
    rating: float
    source: str

class ContentSearchResponse(BaseModel):
    """Schema for content search response."""
    internal_content: List[Dict[str, Any]]
    external_content: List[ExternalContent]
    total_results: int

class PersonalizedContentResponse(BaseModel):
    """Schema for personalized content recommendations."""
    user_id: int
    internal_recommendations: List[ContentRecommendation]
    external_recommendations: List[ExternalContent]
    generated_at: str

