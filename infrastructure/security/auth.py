"""
Authentication and authorization module.
Infrastructure Layer - Security Package
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv

load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()

class SecurityManager:
    """
    Security manager for authentication and authorization.
    Implements security policies from the Security Package.
    """
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token.
        
        Args:
            data: Token payload data
            expires_delta: Token expiration time
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload data
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

class DataEncryption:
    """
    Data encryption utilities.
    Implements data protection from the Security Package.
    """
    
    @staticmethod
    def encrypt_sensitive_data(data: str) -> str:
        """Encrypt sensitive data (placeholder implementation)."""
        # In production, use proper encryption like Fernet
        return pwd_context.hash(data)
    
    @staticmethod
    def decrypt_sensitive_data(encrypted_data: str, original_data: str) -> bool:
        """Decrypt sensitive data (placeholder implementation)."""
        # In production, use proper decryption
        return pwd_context.verify(original_data, encrypted_data)

class SessionManager:
    """
    Session management utilities.
    Implements session handling from the Security Package.
    """
    
    def __init__(self):
        self.active_sessions = {}
    
    def create_session(self, user_id: int, token: str) -> str:
        """Create a new user session."""
        session_id = f"session_{user_id}_{datetime.utcnow().timestamp()}"
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "token": token,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        return session_id
    
    def validate_session(self, session_id: str) -> bool:
        """Validate if session is active and not expired."""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        # Check if session is older than 24 hours
        if datetime.utcnow() - session["created_at"] > timedelta(hours=24):
            del self.active_sessions[session_id]
            return False
        
        # Update last activity
        session["last_activity"] = datetime.utcnow()
        return True
    
    def destroy_session(self, session_id: str) -> bool:
        """Destroy a user session."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False

# Global instances
security_manager = SecurityManager()
session_manager = SessionManager()

def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to get current user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        User data from token payload
    """
    return security_manager.verify_token(credentials.credentials)
