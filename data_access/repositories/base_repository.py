"""
Base repository pattern implementation.
Data Access Layer - Repository Package
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from infrastructure.database.connection import get_database

T = TypeVar('T')

class BaseRepository(Generic[T], ABC):
    """
    Abstract base repository implementing common CRUD operations.
    Follows Repository pattern from the Data Access Layer.
    """
    
    def __init__(self, model_class: type, db_session: Session = None):
        self.model_class = model_class
        self.db_session = db_session
    
    def get_db(self) -> Session:
        """Get database session."""
        if self.db_session:
            return self.db_session
        return next(get_database())
    
    async def create(self, entity_data: Dict[str, Any]) -> Optional[T]:
        """
        Create a new entity.
        
        Args:
            entity_data: Dictionary with entity data
            
        Returns:
            Created entity or None if failed
        """
        try:
            db = self.get_db()
            entity = self.model_class(**entity_data)
            db.add(entity)
            db.commit()
            db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error creating {self.model_class.__name__}: {e}")
            return None
    
    async def get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Get entity by ID.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Entity or None if not found
        """
        try:
            db = self.get_db()
            return db.query(self.model_class).filter(self.model_class.id == entity_id).first()
        except SQLAlchemyError as e:
            print(f"Error getting {self.model_class.__name__} by ID {entity_id}: {e}")
            return None
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Get all entities with pagination.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities
        """
        try:
            db = self.get_db()
            return db.query(self.model_class).offset(offset).limit(limit).all()
        except SQLAlchemyError as e:
            print(f"Error getting all {self.model_class.__name__}: {e}")
            return []
    
    async def update(self, entity_id: int, update_data: Dict[str, Any]) -> Optional[T]:
        """
        Update an entity.
        
        Args:
            entity_id: Entity ID
            update_data: Dictionary with update data
            
        Returns:
            Updated entity or None if failed
        """
        try:
            db = self.get_db()
            entity = db.query(self.model_class).filter(self.model_class.id == entity_id).first()
            
            if not entity:
                return None
            
            for key, value in update_data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            
            db.commit()
            db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error updating {self.model_class.__name__} {entity_id}: {e}")
            return None
    
    async def delete(self, entity_id: int) -> bool:
        """
        Delete an entity.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            True if deleted successfully
        """
        try:
            db = self.get_db()
            entity = db.query(self.model_class).filter(self.model_class.id == entity_id).first()
            
            if not entity:
                return False
            
            db.delete(entity)
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error deleting {self.model_class.__name__} {entity_id}: {e}")
            return False
    
    async def exists(self, entity_id: int) -> bool:
        """
        Check if entity exists.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            True if entity exists
        """
        try:
            db = self.get_db()
            return db.query(self.model_class).filter(self.model_class.id == entity_id).first() is not None
        except SQLAlchemyError as e:
            print(f"Error checking existence of {self.model_class.__name__} {entity_id}: {e}")
            return False
    
    async def count(self) -> int:
        """
        Count total number of entities.
        
        Returns:
            Total count of entities
        """
        try:
            db = self.get_db()
            return db.query(self.model_class).count()
        except SQLAlchemyError as e:
            print(f"Error counting {self.model_class.__name__}: {e}")
            return 0
    
    async def find_by_criteria(self, criteria: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[T]:
        """
        Find entities by criteria.
        
        Args:
            criteria: Dictionary with search criteria
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities matching criteria
        """
        try:
            db = self.get_db()
            query = db.query(self.model_class)
            
            for key, value in criteria.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            
            return query.offset(offset).limit(limit).all()
        except SQLAlchemyError as e:
            print(f"Error finding {self.model_class.__name__} by criteria: {e}")
            return []

class RepositoryManager:
    """
    Repository manager for handling database transactions across multiple repositories.
    Implements Unit of Work pattern.
    """
    
    def __init__(self):
        self.db_session: Optional[Session] = None
        self.repositories: Dict[str, BaseRepository] = {}
    
    def __enter__(self):
        """Start database transaction."""
        self.db_session = next(get_database())
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End database transaction."""
        if exc_type is not None:
            self.db_session.rollback()
        else:
            self.db_session.commit()
        self.db_session.close()
    
    def get_repository(self, repository_class: type) -> BaseRepository:
        """
        Get repository instance with shared database session.
        
        Args:
            repository_class: Repository class
            
        Returns:
            Repository instance
        """
        repo_name = repository_class.__name__
        if repo_name not in self.repositories:
            self.repositories[repo_name] = repository_class(db_session=self.db_session)
        return self.repositories[repo_name]
    
    def commit(self):
        """Commit current transaction."""
        if self.db_session:
            self.db_session.commit()
    
    def rollback(self):
        """Rollback current transaction."""
        if self.db_session:
            self.db_session.rollback()

