"""
Content management API endpoints.
Presentation Layer - API Package
"""

from fastapi import APIRouter, HTTPException, status, Query, UploadFile, File, Body
from typing import Optional, List
from presentation.api.schemas.user_schemas import APIResponse
from data_access.repositories.trilha_repository import TrilhaRepository
from data_access.external_services.content_provider import content_provider, assessment_api
from infrastructure.integration.file_storage import file_storage
from infrastructure.integration.gemini_client import gemini_client

router = APIRouter()
trilha_repository = TrilhaRepository()

@router.get("/external/search", response_model=APIResponse)
async def search_external_content(
    query: str = Query(..., min_length=2, description="Search query"),
    content_type: Optional[str] = Query(None, description="Content type filter"),
    difficulty: Optional[str] = Query(None, description="Difficulty level filter"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """
    Search external content providers for learning materials.
    
    - **query**: Search query (minimum 2 characters)
    - **content_type**: Optional content type filter (video, article, course, etc.)
    - **difficulty**: Optional difficulty filter (beginner, intermediate, advanced)
    - **limit**: Maximum number of results (1-100)
    """
    try:
        external_content = await content_provider.search_content(query, content_type, difficulty)
        
        # Limit results
        limited_content = external_content[:limit]
        
        return APIResponse(
            success=True,
            data={
                "content": limited_content,
                "count": len(limited_content),
                "query": query,
                "filters": {
                    "content_type": content_type,
                    "difficulty": difficulty
                }
            }
        )
    except Exception as e:
        print(f"Error searching external content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search external content"
        )

@router.get("/external/{content_id}", response_model=APIResponse)
async def get_external_content_details(content_id: str):
    """
    Get detailed information about external content.
    
    - **content_id**: External content ID
    """
    try:
        content_details = await content_provider.get_content_details(content_id)
        
        if not content_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="External content not found"
            )
        
        return APIResponse(
            success=True,
            data=content_details
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting external content details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content details"
        )

@router.get("/trending", response_model=APIResponse)
async def get_trending_content(
    category: Optional[str] = Query(None, description="Content category"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """
    Get trending content from external providers.
    
    - **category**: Optional category filter
    - **limit**: Maximum number of results (1-50)
    """
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

@router.get("/assessments/{topic}", response_model=APIResponse)
async def get_assessments_for_topic(
    topic: str,
    difficulty: str = Query("intermediate", description="Difficulty level")
):
    """
    Get assessments/quizzes for a specific topic.
    
    - **topic**: Learning topic
    - **difficulty**: Difficulty level (beginner, intermediate, advanced)
    """
    valid_difficulties = ["beginner", "intermediate", "advanced"]
    if difficulty not in valid_difficulties:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid difficulty. Must be one of: {valid_difficulties}"
        )
    
    try:
        assessments = await assessment_api.get_assessments_for_topic(topic, difficulty)
        
        return APIResponse(
            success=True,
            data={
                "assessments": assessments,
                "topic": topic,
                "difficulty": difficulty,
                "count": len(assessments)
            }
        )
    except Exception as e:
        print(f"Error getting assessments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve assessments"
        )

@router.post("/assessments/{assessment_id}/submit", response_model=APIResponse)
async def submit_assessment(
    assessment_id: str,
    user_id: int = Query(..., description="User ID"),
    score: float = Query(..., ge=0, le=100, description="Assessment score"),
    answers: List[dict] = Body(..., description="User answers")
):
    """
    Submit assessment results.
    
    - **assessment_id**: Assessment ID
    - **user_id**: User ID
    - **score**: Assessment score (0-100)
    - **answers**: List of user answers
    """
    try:
        result = await assessment_api.submit_assessment_result(
            assessment_id, user_id, score, answers
        )
        
        return APIResponse(
            success=True,
            data=result
        )
    except Exception as e:
        print(f"Error submitting assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit assessment"
        )

@router.post("/upload", response_model=APIResponse)
async def upload_content_file(
    file: UploadFile = File(...),
    content_type: str = Query("courses", description="Content type category"),
    description: Optional[str] = Query(None, description="File description")
):
    """
    Upload a content file.
    
    - **file**: File to upload
    - **content_type**: Content category (courses, profiles, temp, exports)
    - **description**: Optional file description
    """
    valid_content_types = ["courses", "profiles", "temp", "exports"]
    if content_type not in valid_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type. Must be one of: {valid_content_types}"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Save file
        result = await file_storage.save_file(file_content, file.filename, content_type)
        
        if result["status"] != "success":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        # Add description if provided
        if description:
            result["description"] = description
        
        return APIResponse(
            success=True,
            message="File uploaded successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )

@router.get("/files", response_model=APIResponse)
async def list_content_files(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results")
):
    """
    List uploaded content files.
    
    - **content_type**: Optional content type filter
    - **limit**: Maximum number of files (1-500)
    """
    try:
        files = await file_storage.list_files(content_type, limit)
        
        return APIResponse(
            success=True,
            data={
                "files": files,
                "count": len(files),
                "content_type_filter": content_type
            }
        )
    except Exception as e:
        print(f"Error listing files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list files"
        )

@router.delete("/files/{file_path:path}", response_model=APIResponse)
async def delete_content_file(file_path: str):
    """
    Delete a content file.
    
    - **file_path**: Path to the file to delete
    """
    try:
        deleted = await file_storage.delete_file(file_path)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return APIResponse(
            success=True,
            message="File deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )

@router.post("/analyze", response_model=APIResponse)
async def analyze_content_with_ai(
    content: str = Query(..., description="Content to analyze"),
    content_type: str = Query("text", description="Type of content")
):
    """
    Analyze learning content using AI.
    
    - **content**: Content to analyze
    - **content_type**: Type of content (text, video, etc.)
    
    Uses Google Gemini AI to analyze content and provide insights about
    difficulty level, topics covered, and learning objectives.
    """
    valid_content_types = ["text", "video", "audio", "document"]
    if content_type not in valid_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type. Must be one of: {valid_content_types}"
        )
    
    try:
        analysis = await gemini_client.analyze_learning_content(content, content_type)
        
        return APIResponse(
            success=True,
            data=analysis
        )
    except Exception as e:
        print(f"Error analyzing content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze content"
        )

@router.get("/storage/stats", response_model=APIResponse)
async def get_storage_statistics():
    """
    Get storage usage statistics.
    
    Returns information about file storage usage, including total files,
    storage space used, and other relevant metrics.
    """
    try:
        stats = file_storage.get_storage_stats()
        
        return APIResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        print(f"Error getting storage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve storage statistics"
        )

@router.get("/types", response_model=APIResponse)
async def get_supported_content_types():
    """
    Get list of supported content types and their descriptions.
    
    Returns information about what types of content are supported
    by the system and their characteristics.
    """
    content_types = {
        "video": {
            "description": "Video-based learning content",
            "supported_formats": [".mp4", ".avi", ".mov", ".wmv"],
            "max_size_mb": 100,
            "features": ["Progress tracking", "Playback speed control", "Subtitles"]
        },
        "text": {
            "description": "Text-based articles and documents",
            "supported_formats": [".pdf", ".doc", ".docx", ".txt"],
            "max_size_mb": 10,
            "features": ["Reading progress", "Bookmarks", "Notes"]
        },
        "quiz": {
            "description": "Interactive quizzes and assessments",
            "supported_formats": ["JSON", "Interactive"],
            "max_size_mb": 1,
            "features": ["Auto-grading", "Instant feedback", "Multiple attempts"]
        },
        "exercise": {
            "description": "Practical exercises and projects",
            "supported_formats": ["Various"],
            "max_size_mb": 50,
            "features": ["Code submission", "Peer review", "Solution comparison"]
        }
    }
    
    return APIResponse(
        success=True,
        data={
            "supported_types": content_types,
            "total_types": len(content_types)
        }
    )
