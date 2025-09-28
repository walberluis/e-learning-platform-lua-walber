"""
AI Recommendations API endpoints.
Presentation Layer - API Package
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from presentation.api.schemas.chatbot_schemas import (
    RecommendationRequest, AIRecommendationResponse, LearningAnalysisRequest,
    LearningAnalysisResponse, ExternalContentSearch, ContentSearchResponse,
    PersonalizedContentResponse
)
from presentation.api.schemas.user_schemas import APIResponse
from business.ai.recommendation_engine import RecommendationEngine
from business.learning.content_delivery import ContentDelivery

router = APIRouter()
recommendation_engine = RecommendationEngine()
content_delivery = ContentDelivery()

@router.get("/{user_id}", response_model=APIResponse)
async def get_ai_recommendations(
    user_id: int,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of recommendations")
):
    """
    Get AI-powered personalized learning recommendations.
    
    - **user_id**: User ID to generate recommendations for
    - **limit**: Maximum number of recommendations (1-50)
    
    Uses Google Gemini AI to analyze user's learning profile, history, and patterns
    to generate intelligent, personalized learning recommendations.
    """
    result = await recommendation_engine.generate_personalized_recommendations(user_id)
    
    if not result["success"]:
        if "not found" in result.get("error", "").lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
    
    return APIResponse(
        success=True,
        data=result
    )

@router.get("/content/{user_id}", response_model=APIResponse)
async def get_personalized_content(
    user_id: int,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of recommendations")
):
    """
    Get personalized content recommendations from internal and external sources.
    
    - **user_id**: User ID to generate recommendations for
    - **limit**: Maximum number of recommendations (1-50)
    
    Combines internal learning paths with external content recommendations
    based on user's preferences and learning history.
    """
    result = await content_delivery.get_recommended_content(user_id, limit)
    
    if not result["success"]:
        if "not found" in result.get("error", "").lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
    
    return APIResponse(
        success=True,
        data=result
    )

@router.post("/analyze/{user_id}", response_model=APIResponse)
async def analyze_learning_patterns(
    user_id: int,
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days")
):
    """
    Analyze user's learning patterns using AI.
    
    - **user_id**: User ID to analyze
    - **period_days**: Number of days to include in analysis (1-365)
    
    Uses AI to analyze learning behavior, identify patterns, strengths,
    and areas for improvement, providing actionable insights.
    """
    result = await recommendation_engine.analyze_learning_patterns(user_id)
    
    if not result["success"]:
        if "not found" in result.get("error", "").lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
    
    return APIResponse(
        success=True,
        data=result
    )

@router.post("/search", response_model=APIResponse)
async def search_learning_content(search_data: ExternalContentSearch):
    """
    Search for learning content across internal and external sources.
    
    - **query**: Search query (2-100 characters)
    - **content_type**: Optional content type filter
    - **difficulty**: Optional difficulty level filter
    - **limit**: Maximum results (1-100)
    
    Searches both internal learning paths and external content providers
    to find relevant learning materials.
    """
    result = await content_delivery.search_content(
        search_data.query,
        search_data.content_type,
        search_data.difficulty,
        search_data.limit
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )
    
    # Calculate total results
    total_results = len(result["internal_content"]) + len(result["external_content"])
    
    return APIResponse(
        success=True,
        data={
            **result,
            "total_results": total_results,
            "search_query": search_data.query
        }
    )

@router.get("/trending", response_model=APIResponse)
async def get_trending_content(
    category: Optional[str] = Query(None, description="Content category filter"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
):
    """
    Get trending learning content from external providers.
    
    - **category**: Optional category filter (programming, data-science, design, etc.)
    - **limit**: Maximum number of results (1-50)
    
    Returns currently trending and popular learning content from external sources.
    """
    from data_access.external_services.content_provider import content_provider
    
    try:
        trending_content = await content_provider.get_trending_content(category, limit)
        
        return APIResponse(
            success=True,
            data={
                "trending_content": trending_content,
                "category": category or "all",
                "count": len(trending_content)
            }
        )
    except Exception as e:
        print(f"Error getting trending content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trending content"
        )

@router.get("/popular-trilhas", response_model=APIResponse)
async def get_popular_trilhas_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
):
    """
    Get popular learning paths (trilhas) as recommendations.
    
    - **limit**: Maximum number of results (1-50)
    
    Returns the most popular learning paths based on enrollment and completion rates.
    """
    from data_access.repositories.trilha_repository import TrilhaRepository
    trilha_repo = TrilhaRepository()
    
    try:
        popular_trilhas = await trilha_repo.get_popular_trilhas(limit)
        
        return APIResponse(
            success=True,
            data={
                "popular_trilhas": popular_trilhas,
                "count": len(popular_trilhas),
                "recommendation_type": "popularity_based"
            }
        )
    except Exception as e:
        print(f"Error getting popular trilhas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve popular trilhas"
        )

@router.get("/top-performers", response_model=APIResponse)
async def get_top_performers_insights(
    metric: str = Query("progress", description="Metric to rank by: progress, grade, study_time"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
):
    """
    Get insights from top-performing users for recommendations.
    
    - **metric**: Metric to rank by (progress, grade, study_time)
    - **limit**: Maximum number of results (1-50)
    
    Analyzes top performers to provide insights that can inform recommendations
    for other users.
    """
    from data_access.repositories.desempenho_repository import DesempenhoRepository
    desempenho_repo = DesempenhoRepository()
    
    valid_metrics = ["progress", "grade", "study_time"]
    if metric not in valid_metrics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid metric. Must be one of: {valid_metrics}"
        )
    
    try:
        top_performers = await desempenho_repo.get_top_performers(limit, metric)
        
        # Extract insights for recommendations
        insights = []
        if top_performers:
            avg_metric_value = sum(
                performer.get(f"average_{metric}", performer.get(f"total_{metric}_hours", 0))
                for performer in top_performers
            ) / len(top_performers)
            
            insights.append(f"Top performers average {avg_metric_value:.1f} in {metric}")
            insights.append(f"Consider focusing on {metric} improvement for better results")
        
        return APIResponse(
            success=True,
            data={
                "top_performers": top_performers,
                "metric": metric,
                "count": len(top_performers),
                "insights": insights
            }
        )
    except Exception as e:
        print(f"Error getting top performers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve top performers data"
        )

@router.get("/learning-paths/{user_id}", response_model=APIResponse)
async def get_recommended_learning_paths(
    user_id: int,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of paths")
):
    """
    Get recommended learning paths for a user.
    
    - **user_id**: User ID to generate paths for
    - **limit**: Maximum number of paths (1-20)
    
    Generates structured learning paths based on user's current level,
    interests, and learning goals.
    """
    from data_access.repositories.trilha_repository import TrilhaRepository
    trilha_repo = TrilhaRepository()
    
    try:
        recommended_trilhas = await trilha_repo.get_recommended_trilhas_for_user(user_id, limit)
        
        # Structure as learning paths
        learning_paths = []
        for trilha in recommended_trilhas:
            # Get trilha with content for path structure
            trilha_with_content = await trilha_repo.get_with_conteudos(trilha.id)
            
            path = {
                "trilha_id": trilha.id,
                "titulo": trilha.titulo,
                "dificuldade": trilha.dificuldade,
                "content_count": len(trilha_with_content.conteudos) if trilha_with_content else 0,
                "estimated_duration": len(trilha_with_content.conteudos) * 30 if trilha_with_content else 0,  # 30 min per content
                "recommendation_reason": f"Matches your learning level and interests"
            }
            learning_paths.append(path)
        
        return APIResponse(
            success=True,
            data={
                "user_id": user_id,
                "recommended_paths": learning_paths,
                "count": len(learning_paths)
            }
        )
    except Exception as e:
        print(f"Error getting recommended learning paths: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate learning path recommendations"
        )

