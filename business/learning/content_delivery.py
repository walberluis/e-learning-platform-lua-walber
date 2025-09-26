"""
Content Delivery Service - Learning content management and delivery.
Business Logic Layer - Learning Package
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from data_access.repositories.trilha_repository import TrilhaRepository
from data_access.repositories.usuario_repository import UsuarioRepository
from data_access.repositories.desempenho_repository import DesempenhoRepository
from data_access.external_services.content_provider import content_provider
from infrastructure.integration.message_queue import analytics_service, notification_service

class ContentDelivery:
    """
    Content delivery service for managing learning content.
    Implements content delivery from the Learning Package.
    """
    
    def __init__(self):
        self.trilha_repository = TrilhaRepository()
        self.usuario_repository = UsuarioRepository()
        self.desempenho_repository = DesempenhoRepository()
    
    async def get_trilha_content(self, trilha_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get trilha content with user progress if provided.
        
        Args:
            trilha_id: Trilha ID
            user_id: User ID (optional for progress tracking)
            
        Returns:
            Trilha content with progress information
        """
        try:
            # Get trilha with content
            trilha = await self.trilha_repository.get_with_conteudos(trilha_id)
            if not trilha:
                return {"success": False, "error": "Trilha not found"}
            
            # Prepare content list
            content_list = []
            for conteudo in trilha.conteudos:
                content_item = {
                    "id": conteudo.id,
                    "titulo": conteudo.titulo,
                    "tipo": conteudo.tipo,
                    "material": conteudo.material,
                    "created_at": conteudo.created_at.isoformat() if conteudo.created_at else None
                }
                
                # Add progress information if user is provided
                if user_id:
                    desempenho = await self.desempenho_repository.get_user_content_performance(user_id, conteudo.id)
                    if desempenho:
                        content_item["progress"] = {
                            "progresso": desempenho.progresso,
                            "nota": desempenho.nota,
                            "tempo_estudo": desempenho.tempo_estudo,
                            "last_accessed": desempenho.updated_at.isoformat() if desempenho.updated_at else None
                        }
                    else:
                        content_item["progress"] = {
                            "progresso": 0,
                            "nota": None,
                            "tempo_estudo": 0,
                            "last_accessed": None
                        }
                
                content_list.append(content_item)
            
            # Track content access
            if user_id:
                await analytics_service.track_event(
                    "trilha_accessed",
                    user_id,
                    {"trilha_id": trilha_id, "trilha_titulo": trilha.titulo}
                )
            
            return {
                "success": True,
                "trilha": {
                    "id": trilha.id,
                    "titulo": trilha.titulo,
                    "dificuldade": trilha.dificuldade,
                    "created_at": trilha.created_at.isoformat() if trilha.created_at else None,
                    "content_count": len(content_list),
                    "conteudos": content_list
                }
            }
        except Exception as e:
            print(f"Error getting trilha content: {e}")
            return {"success": False, "error": "Internal server error"}
    
    async def enroll_user_in_trilha(self, user_id: int, trilha_id: int) -> Dict[str, Any]:
        """
        Enroll user in a trilha (learning path).
        
        Args:
            user_id: User ID
            trilha_id: Trilha ID
            
        Returns:
            Enrollment result
        """
        try:
            # Validate user and trilha exist
            user = await self.usuario_repository.get_by_id(user_id)
            trilha = await self.trilha_repository.get_by_id(trilha_id)
            
            if not user:
                return {"success": False, "error": "User not found"}
            if not trilha:
                return {"success": False, "error": "Trilha not found"}
            
            # Check if already enrolled
            user_with_trilhas = await self.usuario_repository.get_with_trilhas(user_id)
            if any(t.id == trilha_id for t in user_with_trilhas.trilhas):
                return {"success": False, "error": "User already enrolled in this trilha"}
            
            # Enroll user
            enrolled = await self.usuario_repository.add_trilha_to_user(user_id, trilha_id)
            if not enrolled:
                return {"success": False, "error": "Failed to enroll user"}
            
            # Track enrollment
            await analytics_service.track_event(
                "trilha_enrollment",
                user_id,
                {"trilha_id": trilha_id, "trilha_titulo": trilha.titulo}
            )
            
            # Send enrollment notification
            await notification_service.send_notification(
                "enrollment_confirmation",
                user.email,
                {
                    "user_name": user.nome,
                    "trilha_titulo": trilha.titulo,
                    "trilha_id": trilha_id
                }
            )
            
            return {
                "success": True,
                "message": f"Successfully enrolled in {trilha.titulo}",
                "enrollment": {
                    "user_id": user_id,
                    "trilha_id": trilha_id,
                    "enrolled_at": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            print(f"Error enrolling user in trilha: {e}")
            return {"success": False, "error": "Internal server error"}
    
    async def update_content_progress(self, user_id: int, conteudo_id: int, 
                                    progresso: float, nota: Optional[float] = None, 
                                    tempo_estudo: Optional[int] = None) -> Dict[str, Any]:
        """
        Update user's progress on content.
        
        Args:
            user_id: User ID
            conteudo_id: Content ID
            progresso: Progress percentage (0-100)
            nota: Grade/score (optional)
            tempo_estudo: Study time in minutes (optional)
            
        Returns:
            Update result
        """
        try:
            # Validate progress value
            if not 0 <= progresso <= 100:
                return {"success": False, "error": "Progress must be between 0 and 100"}
            
            # Validate grade if provided
            if nota is not None and not 0 <= nota <= 100:
                return {"success": False, "error": "Grade must be between 0 and 100"}
            
            # Update progress
            desempenho = await self.desempenho_repository.update_progress(
                user_id, conteudo_id, progresso, nota, tempo_estudo
            )
            
            if not desempenho:
                return {"success": False, "error": "Failed to update progress"}
            
            # Check if content was completed
            if progresso >= 100:
                await self._handle_content_completion(user_id, conteudo_id, desempenho)
            
            # Track progress update
            await analytics_service.track_event(
                "progress_updated",
                user_id,
                {
                    "conteudo_id": conteudo_id,
                    "progresso": progresso,
                    "nota": nota,
                    "tempo_estudo": tempo_estudo
                }
            )
            
            return {
                "success": True,
                "progress": {
                    "id": desempenho.id,
                    "user_id": user_id,
                    "conteudo_id": conteudo_id,
                    "progresso": desempenho.progresso,
                    "nota": desempenho.nota,
                    "tempo_estudo": desempenho.tempo_estudo,
                    "updated_at": desempenho.updated_at.isoformat() if desempenho.updated_at else None
                }
            }
        except Exception as e:
            print(f"Error updating content progress: {e}")
            return {"success": False, "error": "Internal server error"}
    
    async def _handle_content_completion(self, user_id: int, conteudo_id: int, desempenho) -> None:
        """
        Handle content completion logic.
        
        Args:
            user_id: User ID
            conteudo_id: Content ID
            desempenho: Performance record
        """
        try:
            # Get user and content info
            user = await self.usuario_repository.get_by_id(user_id)
            
            # Send completion notification
            await notification_service.send_notification(
                "content_completed",
                user.email,
                {
                    "user_name": user.nome,
                    "conteudo_id": conteudo_id,
                    "nota": desempenho.nota,
                    "tempo_estudo": desempenho.tempo_estudo
                }
            )
            
            # Check if trilha is completed
            await self._check_trilha_completion(user_id, conteudo_id)
            
        except Exception as e:
            print(f"Error handling content completion: {e}")
    
    async def _check_trilha_completion(self, user_id: int, conteudo_id: int) -> None:
        """
        Check if user completed entire trilha.
        
        Args:
            user_id: User ID
            conteudo_id: Content ID that was just completed
        """
        try:
            # Get the trilha this content belongs to
            from infrastructure.database.models import Conteudo
            from infrastructure.database.connection import get_database
            
            db = next(get_database())
            conteudo = db.query(Conteudo).filter(Conteudo.id == conteudo_id).first()
            if not conteudo:
                return
            
            trilha_id = conteudo.trilha_id
            
            # Get user's progress on this trilha
            trilha_progress = await self.desempenho_repository.get_user_trilha_progress(user_id, trilha_id)
            
            # Check if trilha is completed (100% completion rate)
            if trilha_progress.get("completion_rate", 0) >= 100:
                user = await self.usuario_repository.get_by_id(user_id)
                trilha = await self.trilha_repository.get_by_id(trilha_id)
                
                # Send trilha completion notification
                await notification_service.send_notification(
                    "trilha_completed",
                    user.email,
                    {
                        "user_name": user.nome,
                        "trilha_titulo": trilha.titulo,
                        "trilha_id": trilha_id,
                        "completion_stats": trilha_progress
                    }
                )
                
                # Track trilha completion
                await analytics_service.track_event(
                    "trilha_completed",
                    user_id,
                    {"trilha_id": trilha_id, "trilha_titulo": trilha.titulo}
                )
        except Exception as e:
            print(f"Error checking trilha completion: {e}")
    
    async def get_user_learning_path(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's complete learning path with progress.
        
        Args:
            user_id: User ID
            
        Returns:
            Learning path information
        """
        try:
            # Get user with enrolled trilhas
            user = await self.usuario_repository.get_with_trilhas(user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Get progress for each trilha
            learning_path = []
            for trilha in user.trilhas:
                trilha_progress = await self.desempenho_repository.get_user_trilha_progress(user_id, trilha.id)
                
                learning_path.append({
                    "trilha": {
                        "id": trilha.id,
                        "titulo": trilha.titulo,
                        "dificuldade": trilha.dificuldade
                    },
                    "progress": trilha_progress
                })
            
            return {
                "success": True,
                "user_id": user_id,
                "learning_path": learning_path,
                "total_enrolled_trilhas": len(learning_path)
            }
        except Exception as e:
            print(f"Error getting user learning path: {e}")
            return {"success": False, "error": "Internal server error"}
    
    async def search_content(self, query: str, content_type: Optional[str] = None, 
                           difficulty: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        """
        Search for learning content across internal and external sources.
        
        Args:
            query: Search query
            content_type: Filter by content type
            difficulty: Filter by difficulty level
            limit: Maximum results
            
        Returns:
            Search results
        """
        try:
            results = {"success": True, "internal_content": [], "external_content": []}
            
            # Search internal trilhas
            internal_trilhas = await self.trilha_repository.search_trilhas(query, limit // 2)
            for trilha in internal_trilhas:
                if not difficulty or trilha.dificuldade == difficulty:
                    results["internal_content"].append({
                        "id": trilha.id,
                        "titulo": trilha.titulo,
                        "dificuldade": trilha.dificuldade,
                        "type": "trilha",
                        "source": "internal"
                    })
            
            # Search external content
            external_content = await content_provider.search_content(query, content_type, difficulty)
            results["external_content"] = external_content[:limit // 2]
            
            # Track search event
            await analytics_service.track_event(
                "content_search",
                None,  # Anonymous search
                {
                    "query": query,
                    "content_type": content_type,
                    "difficulty": difficulty,
                    "results_count": len(results["internal_content"]) + len(results["external_content"])
                }
            )
            
            return results
        except Exception as e:
            print(f"Error searching content: {e}")
            return {"success": False, "error": "Internal server error"}
    
    async def get_recommended_content(self, user_id: int, limit: int = 10) -> Dict[str, Any]:
        """
        Get personalized content recommendations for user.
        
        Args:
            user_id: User ID
            limit: Maximum recommendations
            
        Returns:
            Content recommendations
        """
        try:
            # Get user profile
            user = await self.usuario_repository.get_by_id(user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Get recommended trilhas based on user profile
            recommended_trilhas = await self.trilha_repository.get_recommended_trilhas_for_user(user_id, limit)
            
            # Get external content recommendations
            external_recommendations = await content_provider.get_trending_content(
                category="programming",  # Default category
                limit=limit // 2
            )
            
            recommendations = {
                "success": True,
                "user_id": user_id,
                "internal_recommendations": [
                    {
                        "id": trilha.id,
                        "titulo": trilha.titulo,
                        "dificuldade": trilha.dificuldade,
                        "type": "trilha",
                        "source": "internal",
                        "reason": f"Matches your {user.perfil_aprend} level"
                    }
                    for trilha in recommended_trilhas
                ],
                "external_recommendations": external_recommendations,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Track recommendation generation
            await analytics_service.track_event(
                "recommendations_generated",
                user_id,
                {"recommendation_count": len(recommended_trilhas) + len(external_recommendations)}
            )
            
            return recommendations
        except Exception as e:
            print(f"Error getting recommended content: {e}")
            return {"success": False, "error": "Internal server error"}
