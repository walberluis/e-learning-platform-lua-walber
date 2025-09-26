"""
Chatbot Service using Lua scripting and Gemini AI.
Business Logic Layer - AI Package
"""

import lupa
from typing import Dict, Any, List, Optional
from datetime import datetime
from business.ai.recommendation_engine import RecommendationEngine
from data_access.repositories.usuario_repository import UsuarioRepository
from infrastructure.integration.gemini_client import gemini_client
from infrastructure.integration.message_queue import analytics_service

class ChatbotService:
    """
    AI-powered chatbot service with Lua scripting support.
    Implements chatbot functionality from the AI Package.
    """
    
    def __init__(self):
        self.lua = lupa.LuaRuntime(unpack_returned_tuples=True)
        self.recommendation_engine = RecommendationEngine()
        self.usuario_repository = UsuarioRepository()
        self.conversation_history = {}  # In-memory storage for demo
        self._initialize_lua_environment()
    
    def _initialize_lua_environment(self):
        """Initialize Lua environment with helper functions."""
        lua_code = """
        -- Chatbot helper functions in Lua
        
        function analyze_user_intent(message)
            local message_lower = string.lower(message)
            
            -- Intent patterns
            local intents = {
                recommendation = {"recommend", "suggest", "what should", "help me find"},
                progress = {"progress", "how am i doing", "my performance", "stats"},
                help = {"help", "how to", "explain", "what is"},
                greeting = {"hello", "hi", "hey", "good morning", "good afternoon"},
                course_info = {"course", "trilha", "content", "material"},
                completion = {"complete", "finish", "done", "completed"}
            }
            
            for intent, patterns in pairs(intents) do
                for _, pattern in ipairs(patterns) do
                    if string.find(message_lower, pattern) then
                        return intent
                    end
                end
            end
            
            return "general"
        end
        
        function extract_keywords(message)
            local keywords = {}
            local message_lower = string.lower(message)
            
            -- Common learning topics
            local topics = {
                "python", "javascript", "java", "programming", "web development",
                "data science", "machine learning", "ai", "database", "sql",
                "react", "angular", "vue", "nodejs", "backend", "frontend"
            }
            
            for _, topic in ipairs(topics) do
                if string.find(message_lower, topic) then
                    table.insert(keywords, topic)
                end
            end
            
            return keywords
        end
        
        function generate_response_template(intent, user_name)
            local templates = {
                recommendation = "Hi " .. user_name .. "! I'd be happy to recommend some learning content for you.",
                progress = "Let me check your learning progress, " .. user_name .. ".",
                help = "I'm here to help you, " .. user_name .. "! Let me explain that for you.",
                greeting = "Hello " .. user_name .. "! How can I assist you with your learning today?",
                course_info = "I can provide information about courses and learning materials, " .. user_name .. ".",
                completion = "Great job on your progress, " .. user_name .. "! Let me help you with next steps.",
                general = "I understand, " .. user_name .. ". Let me help you with that."
            }
            
            return templates[intent] or templates.general
        end
        
        function calculate_response_confidence(intent, keywords_count, user_context)
            local base_confidence = 0.7
            
            -- Increase confidence based on clear intent
            if intent ~= "general" then
                base_confidence = base_confidence + 0.1
            end
            
            -- Increase confidence based on keywords found
            if keywords_count > 0 then
                base_confidence = base_confidence + (keywords_count * 0.05)
            end
            
            -- Increase confidence if user context is available
            if user_context and user_context.learning_level then
                base_confidence = base_confidence + 0.1
            end
            
            return math.min(base_confidence, 1.0)
        end
        
        function format_learning_recommendation(trilha_data)
            local formatted = "📚 **" .. trilha_data.titulo .. "**\\n"
            formatted = formatted .. "🎯 Difficulty: " .. trilha_data.dificuldade .. "\\n"
            formatted = formatted .. "📖 Perfect for your learning level!\\n"
            return formatted
        end
        """
        
        self.lua.execute(lua_code)
    
    async def process_message(self, user_id: int, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process user message and generate appropriate response.
        
        Args:
            user_id: User ID
            message: User's message
            context: Additional context
            
        Returns:
            Chatbot response with metadata
        """
        try:
            # Get user information
            user = await self.usuario_repository.get_by_id(user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Analyze message using Lua
            intent = self.lua.globals().analyze_user_intent(message)
            keywords = list(self.lua.globals().extract_keywords(message))
            
            # Generate response template
            response_template = self.lua.globals().generate_response_template(intent, user.nome)
            
            # Calculate confidence
            user_context = {"learning_level": user.perfil_aprend}
            confidence = self.lua.globals().calculate_response_confidence(intent, len(keywords), user_context)
            
            # Generate detailed response based on intent
            detailed_response = await self._generate_intent_response(user_id, intent, keywords, message, context)
            
            # Combine template with detailed response
            full_response = f"{response_template}\n\n{detailed_response}"
            
            # Store conversation history
            self._store_conversation(user_id, message, full_response, intent)
            
            # Track chatbot interaction
            await analytics_service.track_event(
                "chatbot_message_processed",
                user_id,
                {
                    "intent": intent,
                    "keywords": keywords,
                    "confidence": confidence,
                    "message_length": len(message)
                }
            )
            
            return {
                "success": True,
                "response": full_response,
                "metadata": {
                    "intent": intent,
                    "keywords": keywords,
                    "confidence": confidence,
                    "user_name": user.nome,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            print(f"Error processing chatbot message: {e}")
            return {
                "success": False,
                "error": "Failed to process message",
                "response": "I'm sorry, I'm having trouble understanding right now. Could you please try again?"
            }
    
    async def _generate_intent_response(self, user_id: int, intent: str, keywords: List[str], 
                                      original_message: str, context: Dict[str, Any] = None) -> str:
        """
        Generate detailed response based on detected intent.
        
        Args:
            user_id: User ID
            intent: Detected intent
            keywords: Extracted keywords
            original_message: Original user message
            context: Additional context
            
        Returns:
            Detailed response string
        """
        try:
            if intent == "recommendation":
                return await self._handle_recommendation_request(user_id, keywords)
            elif intent == "progress":
                return await self._handle_progress_request(user_id)
            elif intent == "help":
                return await self._handle_help_request(keywords, original_message)
            elif intent == "greeting":
                return await self._handle_greeting(user_id)
            elif intent == "course_info":
                return await self._handle_course_info_request(keywords)
            elif intent == "completion":
                return await self._handle_completion_request(user_id)
            else:
                return await self._handle_general_request(user_id, original_message, context)
        except Exception as e:
            print(f"Error generating intent response: {e}")
            return "I understand your question, but I'm having trouble generating a detailed response right now."
    
    async def _handle_recommendation_request(self, user_id: int, keywords: List[str]) -> str:
        """Handle recommendation requests."""
        try:
            # Get AI-powered recommendations
            recommendations = await self.recommendation_engine.generate_personalized_recommendations(user_id)
            
            if not recommendations.get("success"):
                return "I'm having trouble generating recommendations right now. Please try again later."
            
            # Format recommendations using Lua
            response = "Here are my personalized recommendations for you:\n\n"
            
            structured_recs = recommendations.get("structured_recommendations", {})
            content_recs = structured_recs.get("content_recommendations", [])
            
            for i, rec in enumerate(content_recs[:3], 1):  # Top 3 recommendations
                trilha_data = {"titulo": rec["titulo"], "dificuldade": rec["dificuldade"]}
                formatted_rec = self.lua.globals().format_learning_recommendation(trilha_data)
                response += f"{i}. {formatted_rec}\n"
            
            # Add AI insights
            ai_insights = recommendations.get("ai_recommendations", "")
            if ai_insights:
                response += f"\n🤖 **AI Insights:**\n{ai_insights[:200]}..."
            
            return response
        except Exception as e:
            print(f"Error handling recommendation request: {e}")
            return "I'd love to recommend some content for you! Let me gather some information about your learning preferences."
    
    async def _handle_progress_request(self, user_id: int) -> str:
        """Handle progress inquiry requests."""
        try:
            from data_access.repositories.desempenho_repository import DesempenhoRepository
            desempenho_repo = DesempenhoRepository()
            
            analytics = await desempenho_repo.get_learning_analytics(user_id)
            
            if not analytics:
                return "I don't have enough data about your progress yet. Start learning some content and I'll be able to track your progress!"
            
            response = "📊 **Your Learning Progress:**\n\n"
            response += f"🎯 Completion Rate: {analytics.get('completion_rate', 0)}%\n"
            response += f"📚 Total Activities: {analytics.get('total_activities', 0)}\n"
            response += f"⭐ Average Grade: {analytics.get('average_grade_all_time', 0):.1f}/100\n"
            response += f"⏱️ Total Study Time: {analytics.get('total_study_time_hours', 0):.1f} hours\n"
            response += f"🔥 Learning Streak: {analytics.get('learning_streak', 0)} days\n\n"
            
            # Add motivational message
            completion_rate = analytics.get('completion_rate', 0)
            if completion_rate > 80:
                response += "🌟 Excellent work! You're doing great with completing your learning content!"
            elif completion_rate > 60:
                response += "👍 Good progress! Try to complete more content to boost your learning effectiveness."
            else:
                response += "💪 Keep going! Focus on completing the content you start for better learning outcomes."
            
            return response
        except Exception as e:
            print(f"Error handling progress request: {e}")
            return "I can help you track your learning progress! Complete some learning activities and I'll show you detailed statistics."
    
    async def _handle_help_request(self, keywords: List[str], original_message: str) -> str:
        """Handle help and explanation requests."""
        # Use Gemini AI for detailed explanations
        help_context = {
            "user_name": "Student",
            "keywords": keywords,
            "question": original_message
        }
        
        ai_response = await gemini_client.generate_chatbot_response(original_message, help_context)
        
        return f"📖 **Here's what I can explain:**\n\n{ai_response}\n\nIs there anything specific you'd like me to elaborate on?"
    
    async def _handle_greeting(self, user_id: int) -> str:
        """Handle greeting messages."""
        user = await self.usuario_repository.get_by_id(user_id)
        
        greetings = [
            f"Welcome back! Ready to continue your learning journey?",
            f"Great to see you! What would you like to learn today?",
            f"Hello! I'm here to help you with your learning goals.",
            f"Hi there! Let's make today a productive learning day!"
        ]
        
        import random
        greeting = random.choice(greetings)
        
        return f"{greeting}\n\n💡 I can help you with:\n• Finding new courses\n• Tracking your progress\n• Answering questions\n• Providing recommendations"
    
    async def _handle_course_info_request(self, keywords: List[str]) -> str:
        """Handle course information requests."""
        response = "📚 **Course Information:**\n\n"
        
        if keywords:
            response += f"I found information related to: {', '.join(keywords)}\n\n"
        
        response += "I can help you find courses in various topics including:\n"
        response += "• Programming (Python, JavaScript, Java)\n"
        response += "• Web Development (React, Angular, Node.js)\n"
        response += "• Data Science & AI\n"
        response += "• Database Management\n"
        response += "• And many more!\n\n"
        response += "What specific topic interests you?"
        
        return response
    
    async def _handle_completion_request(self, user_id: int) -> str:
        """Handle completion-related requests."""
        return "🎉 **Congratulations on your progress!**\n\nCompleting learning content is a great achievement! Here's what you can do next:\n\n• Review what you've learned\n• Apply your knowledge in practice\n• Move on to more advanced topics\n• Share your achievement with others\n\nWould you like me to recommend your next learning step?"
    
    async def _handle_general_request(self, user_id: int, message: str, context: Dict[str, Any] = None) -> str:
        """Handle general requests using AI."""
        # Get conversation history for context
        history = self.conversation_history.get(user_id, [])
        
        # Prepare context for AI
        ai_context = {
            "user_name": "Student",
            "conversation_history": history[-3:],  # Last 3 exchanges
            "current_context": context or {}
        }
        
        # Generate AI response
        ai_response = await gemini_client.generate_chatbot_response(message, ai_context)
        
        return ai_response
    
    def _store_conversation(self, user_id: int, user_message: str, bot_response: str, intent: str):
        """Store conversation history."""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_message": user_message,
            "bot_response": bot_response,
            "intent": intent
        })
        
        # Keep only last 10 exchanges
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
    
    async def get_conversation_history(self, user_id: int, limit: int = 10) -> Dict[str, Any]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of exchanges to return
            
        Returns:
            Conversation history
        """
        history = self.conversation_history.get(user_id, [])
        
        return {
            "success": True,
            "user_id": user_id,
            "conversation_count": len(history),
            "history": history[-limit:] if history else []
        }
    
    async def clear_conversation_history(self, user_id: int) -> Dict[str, Any]:
        """
        Clear conversation history for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Clear operation result
        """
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
        
        return {"success": True, "message": "Conversation history cleared"}

# Global instance
chatbot_service = ChatbotService()
