"""
AI Chatbot API endpoints.
Presentation Layer - API Package
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from presentation.api.schemas.chatbot_schemas import (
    ChatMessage, ChatResponse, ConversationHistoryResponse
)
from presentation.api.schemas.user_schemas import APIResponse
from business.ai.chatbot_service import chatbot_service

router = APIRouter()

@router.post("/chat/{user_id}", response_model=APIResponse)
async def chat_with_bot(user_id: int, message_data: ChatMessage):
    """
    Send a message to the AI chatbot.
    
    - **user_id**: User ID for personalized responses
    - **message**: User's message (1-1000 characters)
    - **context**: Optional context for the conversation
    
    The chatbot uses Lua scripting for intent analysis and Google Gemini AI 
    for generating intelligent responses based on user's learning profile.
    """
    result = await chatbot_service.process_message(
        user_id, 
        message_data.message, 
        message_data.context
    )
    
    if not result["success"]:
        if "not found" in result.get("error", "").lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        else:
            # Return a fallback response instead of error for better UX
            return APIResponse(
                success=True,
                data={
                    "response": result.get("response", "I'm sorry, I'm having trouble understanding right now. Could you please try again?"),
                    "metadata": {
                        "intent": "error",
                        "confidence": 0.0,
                        "error": result.get("error")
                    }
                }
            )
    
    return APIResponse(
        success=True,
        data={
            "response": result["response"],
            "metadata": result["metadata"]
        }
    )

@router.get("/history/{user_id}", response_model=APIResponse)
async def get_conversation_history(
    user_id: int,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of conversation exchanges")
):
    """
    Get conversation history for a user.
    
    - **user_id**: User ID to get history for
    - **limit**: Maximum number of exchanges to return (1-50)
    
    Returns the most recent conversation exchanges between the user and the chatbot.
    """
    result = await chatbot_service.get_conversation_history(user_id, limit)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history"
        )
    
    return APIResponse(
        success=True,
        data=result
    )

@router.delete("/history/{user_id}", response_model=APIResponse)
async def clear_conversation_history(user_id: int):
    """
    Clear conversation history for a user.
    
    - **user_id**: User ID to clear history for
    
    This will permanently delete all conversation history for the specified user.
    """
    result = await chatbot_service.clear_conversation_history(user_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear conversation history"
        )
    
    return APIResponse(
        success=True,
        message=result["message"]
    )

@router.post("/quick-help/{user_id}", response_model=APIResponse)
async def get_quick_help(user_id: int, topic: str = Query(..., description="Help topic")):
    """
    Get quick help on a specific topic.
    
    - **user_id**: User ID for personalized help
    - **topic**: Topic to get help about
    
    Provides quick, contextual help using the AI chatbot without storing 
    the interaction in conversation history.
    """
    # Create a help-focused message
    help_message = f"Can you help me understand {topic}?"
    
    result = await chatbot_service.process_message(
        user_id, 
        help_message, 
        {"type": "quick_help", "topic": topic}
    )
    
    if not result["success"]:
        return APIResponse(
            success=True,
            data={
                "response": f"I can help you with {topic}! Here are some key points to get you started. For more detailed information, please ask me specific questions about this topic.",
                "metadata": {
                    "intent": "help",
                    "topic": topic,
                    "type": "quick_help"
                }
            }
        )
    
    return APIResponse(
        success=True,
        data={
            "response": result["response"],
            "metadata": {
                **result["metadata"],
                "type": "quick_help",
                "topic": topic
            }
        }
    )

@router.get("/intents", response_model=APIResponse)
async def get_supported_intents():
    """
    Get list of supported chatbot intents and capabilities.
    
    Returns information about what the chatbot can help with and 
    the types of questions it can answer.
    """
    intents = {
        "recommendation": {
            "description": "Get personalized learning recommendations",
            "examples": ["What should I learn next?", "Recommend me a course", "Help me find content"]
        },
        "progress": {
            "description": "Check learning progress and statistics",
            "examples": ["How am I doing?", "Show my progress", "What are my stats?"]
        },
        "help": {
            "description": "Get help and explanations on topics",
            "examples": ["Explain Python", "How does machine learning work?", "What is React?"]
        },
        "greeting": {
            "description": "General greetings and conversation starters",
            "examples": ["Hello", "Hi there", "Good morning"]
        },
        "course_info": {
            "description": "Get information about courses and content",
            "examples": ["Tell me about this course", "What courses are available?", "Course details"]
        },
        "completion": {
            "description": "Celebrate achievements and get next steps",
            "examples": ["I completed a course", "I finished this module", "What's next?"]
        }
    }
    
    capabilities = [
        "Personalized learning recommendations using AI",
        "Progress tracking and analytics",
        "Educational content explanations",
        "Learning path guidance",
        "Motivational support and encouragement",
        "Course and content information",
        "Study habit recommendations"
    ]
    
    return APIResponse(
        success=True,
        data={
            "supported_intents": intents,
            "capabilities": capabilities,
            "ai_features": [
                "Intent recognition using Lua scripting",
                "Response generation using Google Gemini AI",
                "Context-aware conversations",
                "Personalized responses based on user profile"
            ]
        }
    )

@router.post("/feedback/{user_id}", response_model=APIResponse)
async def submit_chatbot_feedback(
    user_id: int,
    rating: int = Query(..., ge=1, le=5, description="Rating from 1-5"),
    feedback: Optional[str] = Query(None, description="Optional feedback text"),
    conversation_id: Optional[str] = Query(None, description="Conversation ID for context")
):
    """
    Submit feedback about chatbot interaction.
    
    - **user_id**: User ID providing feedback
    - **rating**: Rating from 1 (poor) to 5 (excellent)
    - **feedback**: Optional text feedback
    - **conversation_id**: Optional conversation ID for context
    
    This helps improve the chatbot's responses and user experience.
    """
    # In a real system, this would store feedback in a database
    # For now, we'll just log it and return success
    
    feedback_data = {
        "user_id": user_id,
        "rating": rating,
        "feedback": feedback,
        "conversation_id": conversation_id,
        "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
    }
    
    print(f"Chatbot feedback received: {feedback_data}")
    
    return APIResponse(
        success=True,
        message="Thank you for your feedback! It helps us improve the chatbot experience.",
        data={"feedback_id": f"feedback_{user_id}_{rating}"}
    )

