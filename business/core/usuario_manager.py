"""
Usuario Manager - Core business logic for user management.
Business Logic Layer - Core Package
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from data_access.repositories.usuario_repository import UsuarioRepository
from data_access.repositories.desempenho_repository import DesempenhoRepository
from infrastructure.security.auth import SecurityManager
from infrastructure.integration.message_queue import notification_service, analytics_service

class UsuarioManager:
    """
    Core business logic for user management.
    Implements user-related operations from the Core Package.
    """
    
    def __init__(self):
        self.usuario_repository = UsuarioRepository()
        self.desempenho_repository = DesempenhoRepository()
        self.security_manager = SecurityManager()
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user with business validation.
        
        Args:
            user_data: User registration data
            
        Returns:
            Result dictionary with user info or error
        """
        try:
            # Validate required fields
            required_fields = ["nome", "email"]
            for field in required_fields:
                if not user_data.get(field):
                    return {"success": False, "error": f"Field '{field}' is required"}
            
            # Check if email already exists
            existing_user = await self.usuario_repository.get_by_email(user_data["email"])
            if existing_user:
                return {"success": False, "error": "Email already registered"}
            
            # Validate email format
            if not self._is_valid_email(user_data["email"]):
                return {"success": False, "error": "Invalid email format"}
            
            # Hash password if provided
            if user_data.get("senha"):
                # Limit password to 72 bytes for bcrypt compatibility
                password = user_data["senha"]
                if len(password.encode('utf-8')) > 72:
                    password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
                user_data["senha"] = self.security_manager.get_password_hash(password)
            
            # Set default learning profile if not provided
            if not user_data.get("perfil_aprend"):
                user_data["perfil_aprend"] = "beginner"
            
            # Create user
            user = await self.usuario_repository.create(user_data)
            if not user:
                return {"success": False, "error": "Failed to create user"}
            
            # Track user creation event
            await analytics_service.track_event(
                "user_created",
                user.id,
                {"email": user.email, "perfil_aprend": user.perfil_aprend}
            )
            
            # Send welcome notification
            await notification_service.send_notification(
                "welcome",
                user.email,
                {"user_name": user.nome, "user_id": user.id}
            )
            
            return {
                "success": True,
                "user": {
                    "id": user.id,
                    "nome": user.nome,
                    "email": user.email,
                    "perfil_aprend": user.perfil_aprend,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
            }
        except Exception as e:
            print(f"Error creating user: {e}")
            return {"success": False, "error": "Internal server error"}
    
    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and return access token.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Result dictionary with token and user info or error
        """
        try:
            # Get user by email
            user = await self.usuario_repository.get_by_email(email)
            if not user:
                return {"success": False, "error": "Invalid email or password"}
            
            # Verify password (limit to 72 bytes for bcrypt compatibility)
            password_limited = password
            if len(password.encode('utf-8')) > 72:
                password_limited = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
            
            if not user.senha or not self.security_manager.verify_password(password_limited, user.senha):
                return {"success": False, "error": "Invalid email or password"}
            
            # Create access token
            token_data = {"sub": str(user.id), "user_id": user.id, "email": user.email}
            access_token = self.security_manager.create_access_token(data=token_data)
            
            # Convert user to dict and remove password
            user_data = {
                "id": user.id,
                "nome": user.nome,
                "email": user.email,
                "perfil_aprend": user.perfil_aprend,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            
            return {
                "success": True,
                "token": access_token,
                "user": user_data
            }
            
        except Exception as e:
            return {"success": False, "error": f"Authentication failed: {str(e)}"}
    
    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive user profile with learning data.
        
        Args:
            user_id: User ID
            
        Returns:
            User profile dictionary
        """
        try:
            # Get user with relationships
            user = await self.usuario_repository.get_with_trilhas(user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Get progress summary
            progress_summary = await self.usuario_repository.get_user_progress_summary(user_id)
            
            # Get learning analytics
            analytics = await self.desempenho_repository.get_learning_analytics(user_id)
            
            return {
                "success": True,
                "profile": {
                    "id": user.id,
                    "nome": user.nome,
                    "email": user.email,
                    "perfil_aprend": user.perfil_aprend,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "enrolled_trilhas": [
                        {
                            "id": trilha.id,
                            "titulo": trilha.titulo,
                            "dificuldade": trilha.dificuldade
                        }
                        for trilha in user.trilhas
                    ],
                    "progress_summary": progress_summary,
                    "learning_analytics": analytics
                }
            }
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return {"success": False, "error": "Internal server error"}
    
    async def update_user_profile(self, user_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user profile with validation.
        
        Args:
            user_id: User ID
            update_data: Data to update
            
        Returns:
            Update result
        """
        try:
            # Validate email if being updated
            if "email" in update_data:
                if not self._is_valid_email(update_data["email"]):
                    return {"success": False, "error": "Invalid email format"}
                
                # Check if new email already exists
                existing_user = await self.usuario_repository.get_by_email(update_data["email"])
                if existing_user and existing_user.id != user_id:
                    return {"success": False, "error": "Email already in use"}
            
            # Validate learning profile
            if "perfil_aprend" in update_data:
                valid_profiles = ["beginner", "intermediate", "advanced"]
                if update_data["perfil_aprend"] not in valid_profiles:
                    return {"success": False, "error": f"Invalid learning profile. Must be one of: {valid_profiles}"}
            
            # Update user
            updated_user = await self.usuario_repository.update(user_id, update_data)
            if not updated_user:
                return {"success": False, "error": "Failed to update user or user not found"}
            
            # Track profile update event
            await analytics_service.track_event(
                "profile_updated",
                user_id,
                {"updated_fields": list(update_data.keys())}
            )
            
            return {
                "success": True,
                "user": {
                    "id": updated_user.id,
                    "nome": updated_user.nome,
                    "email": updated_user.email,
                    "perfil_aprend": updated_user.perfil_aprend,
                    "updated_at": updated_user.updated_at.isoformat() if updated_user.updated_at else None
                }
            }
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return {"success": False, "error": "Internal server error"}
    
    async def search_users(self, search_term: str, limit: int = 50) -> Dict[str, Any]:
        """
        Search users with business logic.
        
        Args:
            search_term: Search term
            limit: Maximum results
            
        Returns:
            Search results
        """
        try:
            if len(search_term) < 2:
                return {"success": False, "error": "Search term must be at least 2 characters"}
            
            users = await self.usuario_repository.search_users(search_term, limit)
            
            return {
                "success": True,
                "users": [
                    {
                        "id": user.id,
                        "nome": user.nome,
                        "email": user.email,
                        "perfil_aprend": user.perfil_aprend
                    }
                    for user in users
                ],
                "count": len(users)
            }
        except Exception as e:
            print(f"Error searching users: {e}")
            return {"success": False, "error": "Internal server error"}
    
    async def get_user_learning_recommendations(self, user_id: int) -> Dict[str, Any]:
        """
        Get personalized learning recommendations for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Recommendations dictionary
        """
        try:
            # Get user profile and learning history
            user = await self.usuario_repository.get_with_desempenhos(user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Analyze learning patterns
            learning_analytics = await self.desempenho_repository.get_learning_analytics(user_id)
            
            # Generate recommendations based on user data
            recommendations = await self._generate_user_recommendations(user, learning_analytics)
            
            return {
                "success": True,
                "user_id": user_id,
                "recommendations": recommendations,
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error getting user recommendations: {e}")
            return {"success": False, "error": "Internal server error"}
    
    async def _generate_user_recommendations(self, user, analytics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendations based on user data.
        
        Args:
            user: User object
            analytics: Learning analytics data
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Recommendation based on learning profile
        if user.perfil_aprend == "beginner":
            recommendations.append({
                "type": "learning_path",
                "title": "Foundational Learning Path",
                "description": "Start with basic concepts to build a strong foundation",
                "priority": "high",
                "reason": "Matches your beginner learning profile"
            })
        elif user.perfil_aprend == "intermediate":
            recommendations.append({
                "type": "skill_advancement",
                "title": "Intermediate Skill Building",
                "description": "Advance your skills with intermediate-level content",
                "priority": "high",
                "reason": "Perfect for your intermediate level"
            })
        else:  # advanced
            recommendations.append({
                "type": "expert_content",
                "title": "Advanced Specialization",
                "description": "Explore cutting-edge topics and specialized content",
                "priority": "high",
                "reason": "Matches your advanced learning profile"
            })
        
        # Recommendation based on activity level
        if analytics.get("recent_activities", 0) < 3:
            recommendations.append({
                "type": "engagement",
                "title": "Get Back on Track",
                "description": "Resume your learning journey with short, engaging content",
                "priority": "medium",
                "reason": "Low recent activity detected"
            })
        
        # Recommendation based on completion rate
        completion_rate = analytics.get("completion_rate", 0)
        if completion_rate < 50:
            recommendations.append({
                "type": "motivation",
                "title": "Focus on Completion",
                "description": "Try shorter content pieces to build momentum",
                "priority": "medium",
                "reason": f"Current completion rate is {completion_rate}%"
            })
        
        # Study time recommendation
        daily_study_time = analytics.get("daily_average_study_time", 0)
        if daily_study_time < 0.5:  # Less than 30 minutes per day
            recommendations.append({
                "type": "study_habit",
                "title": "Increase Study Time",
                "description": "Try to dedicate at least 30 minutes daily to learning",
                "priority": "low",
                "reason": f"Current daily average is {daily_study_time:.1f} hours"
            })
        
        return recommendations
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    async def delete_user(self, user_id: int) -> Dict[str, Any]:
        """
        Delete user with proper cleanup.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            Deletion result
        """
        try:
            # Check if user exists
            user = await self.usuario_repository.get_by_id(user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # In a real system, you might want to:
            # 1. Archive user data instead of deleting
            # 2. Clean up related data (performances, enrollments)
            # 3. Send notification about account deletion
            
            # For now, just delete the user
            deleted = await self.usuario_repository.delete(user_id)
            if not deleted:
                return {"success": False, "error": "Failed to delete user"}
            
            # Track deletion event
            await analytics_service.track_event(
                "user_deleted",
                user_id,
                {"email": user.email}
            )
            
            return {"success": True, "message": "User deleted successfully"}
        except Exception as e:
            print(f"Error deleting user: {e}")
            return {"success": False, "error": "Internal server error"}
