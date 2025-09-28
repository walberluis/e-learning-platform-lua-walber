"""
Usuario (User) repository implementation.
Data Access Layer - Repository Package
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from data_access.repositories.base_repository import BaseRepository
from infrastructure.database.models import Usuario, Trilha, Desempenho

class UsuarioRepository(BaseRepository[Usuario]):
    """
    Repository for Usuario (User) entity operations.
    Implements specific user-related database operations.
    """
    
    def __init__(self, db_session: Session = None):
        super().__init__(Usuario, db_session)
    
    async def get_by_email(self, email: str) -> Optional[Usuario]:
        """
        Get user by email address.
        
        Args:
            email: User email address
            
        Returns:
            Usuario entity or None if not found
        """
        try:
            db = self.get_db()
            return db.query(Usuario).filter(Usuario.email == email).first()
        except Exception as e:
            print(f"Error getting user by email {email}: {e}")
            return None
    
    async def get_with_trilhas(self, user_id: int) -> Optional[Usuario]:
        """
        Get user with their enrolled trilhas (learning paths).
        
        Args:
            user_id: User ID
            
        Returns:
            Usuario with trilhas loaded or None if not found
        """
        try:
            db = self.get_db()
            return db.query(Usuario).options(joinedload(Usuario.trilhas)).filter(Usuario.id == user_id).first()
        except Exception as e:
            print(f"Error getting user with trilhas {user_id}: {e}")
            return None
    
    async def get_with_desempenhos(self, user_id: int) -> Optional[Usuario]:
        """
        Get user with their performance records.
        
        Args:
            user_id: User ID
            
        Returns:
            Usuario with desempenhos loaded or None if not found
        """
        try:
            db = self.get_db()
            return db.query(Usuario).options(joinedload(Usuario.desempenhos)).filter(Usuario.id == user_id).first()
        except Exception as e:
            print(f"Error getting user with desempenhos {user_id}: {e}")
            return None
    
    async def search_users(self, search_term: str, limit: int = 50) -> List[Usuario]:
        """
        Search users by name or email.
        
        Args:
            search_term: Search term to match against name or email
            limit: Maximum number of results
            
        Returns:
            List of matching users
        """
        try:
            db = self.get_db()
            search_pattern = f"%{search_term}%"
            return db.query(Usuario).filter(
                or_(
                    Usuario.nome.ilike(search_pattern),
                    Usuario.email.ilike(search_pattern)
                )
            ).limit(limit).all()
        except Exception as e:
            print(f"Error searching users with term '{search_term}': {e}")
            return []
    
    async def get_users_by_learning_profile(self, perfil_aprend: str) -> List[Usuario]:
        """
        Get users by learning profile.
        
        Args:
            perfil_aprend: Learning profile type
            
        Returns:
            List of users with matching learning profile
        """
        try:
            db = self.get_db()
            return db.query(Usuario).filter(Usuario.perfil_aprend == perfil_aprend).all()
        except Exception as e:
            print(f"Error getting users by learning profile '{perfil_aprend}': {e}")
            return []
    
    async def add_trilha_to_user(self, user_id: int, trilha_id: int) -> bool:
        """
        Add a trilha (learning path) to a user.
        
        Args:
            user_id: User ID
            trilha_id: Trilha ID
            
        Returns:
            True if added successfully
        """
        try:
            db = self.get_db()
            user = db.query(Usuario).filter(Usuario.id == user_id).first()
            trilha = db.query(Trilha).filter(Trilha.id == trilha_id).first()
            
            if not user or not trilha:
                return False
            
            if trilha not in user.trilhas:
                user.trilhas.append(trilha)
                db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            print(f"Error adding trilha {trilha_id} to user {user_id}: {e}")
            return False
    
    async def remove_trilha_from_user(self, user_id: int, trilha_id: int) -> bool:
        """
        Remove a trilha from a user.
        
        Args:
            user_id: User ID
            trilha_id: Trilha ID
            
        Returns:
            True if removed successfully
        """
        try:
            db = self.get_db()
            user = db.query(Usuario).filter(Usuario.id == user_id).first()
            trilha = db.query(Trilha).filter(Trilha.id == trilha_id).first()
            
            if not user or not trilha:
                return False
            
            if trilha in user.trilhas:
                user.trilhas.remove(trilha)
                db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            print(f"Error removing trilha {trilha_id} from user {user_id}: {e}")
            return False
    
    async def get_user_progress_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's learning progress summary.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with progress summary
        """
        try:
            db = self.get_db()
            user = db.query(Usuario).options(
                joinedload(Usuario.trilhas),
                joinedload(Usuario.desempenhos)
            ).filter(Usuario.id == user_id).first()
            
            if not user:
                return {}
            
            total_trilhas = len(user.trilhas)
            total_desempenhos = len(user.desempenhos)
            
            if total_desempenhos > 0:
                avg_progress = sum(d.progresso for d in user.desempenhos) / total_desempenhos
                avg_grade = sum(d.nota for d in user.desempenhos if d.nota is not None) / len([d for d in user.desempenhos if d.nota is not None]) if any(d.nota is not None for d in user.desempenhos) else 0
                total_study_time = sum(d.tempo_estudo for d in user.desempenhos)
            else:
                avg_progress = 0
                avg_grade = 0
                total_study_time = 0
            
            return {
                "user_id": user_id,
                "nome": user.nome,
                "email": user.email,
                "perfil_aprend": user.perfil_aprend,
                "total_trilhas": total_trilhas,
                "total_activities": total_desempenhos,
                "average_progress": round(avg_progress, 2),
                "average_grade": round(avg_grade, 2),
                "total_study_time_minutes": total_study_time,
                "total_study_time_hours": round(total_study_time / 60, 2)
            }
        except Exception as e:
            print(f"Error getting progress summary for user {user_id}: {e}")
            return {}
    
    async def get_active_users(self, days: int = 30) -> List[Usuario]:
        """
        Get users who have been active in the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of active users
        """
        try:
            from datetime import datetime, timedelta
            db = self.get_db()
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            return db.query(Usuario).join(Desempenho).filter(
                Desempenho.updated_at >= cutoff_date
            ).distinct().all()
        except Exception as e:
            print(f"Error getting active users: {e}")
            return []
    
    async def update_learning_profile(self, user_id: int, perfil_aprend: str) -> Optional[Usuario]:
        """
        Update user's learning profile.
        
        Args:
            user_id: User ID
            perfil_aprend: New learning profile
            
        Returns:
            Updated user or None if failed
        """
        return await self.update(user_id, {"perfil_aprend": perfil_aprend})

