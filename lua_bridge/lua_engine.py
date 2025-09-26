"""
Lua Engine Bridge - Connects Python FastAPI with Lua business logic
This module provides the interface between Python and Lua core functionality
"""

import lupa
import os
import sys
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add lua_core to Python path
lua_core_path = Path(__file__).parent.parent / "lua_core"
sys.path.insert(0, str(lua_core_path))

class LuaEngine:
    """
    Main Lua Engine that bridges Python and Lua
    Provides access to all Lua-based business logic
    """
    
    def __init__(self):
        self.lua = lupa.LuaRuntime(unpack_returned_tuples=True)
        self.elearning = None
        self._initialize_lua_environment()
        self._setup_python_bridges()
    
    def _initialize_lua_environment(self):
        """Initialize Lua environment and load core modules"""
        try:
            # Set up Lua package path to include our lua_core directory
            lua_core_abs_path = str(lua_core_path.absolute()).replace('\\', '/')
            
            self.lua.execute(f"""
                package.path = package.path .. ";{lua_core_abs_path}/?.lua;{lua_core_abs_path}/?/init.lua"
                
                -- Mock json library for Lua
                json = {{
                    encode = function(data)
                        -- Simple JSON encoding (would use proper library in production)
                        if type(data) == "table" then
                            local result = "{{"
                            local first = true
                            for k, v in pairs(data) do
                                if not first then result = result .. "," end
                                first = false
                                result = result .. '"' .. tostring(k) .. '":' 
                                if type(v) == "string" then
                                    result = result .. '"' .. tostring(v) .. '"'
                                else
                                    result = result .. tostring(v)
                                end
                            end
                            result = result .. "}}"
                            return result
                        else
                            return tostring(data)
                        end
                    end,
                    decode = function(str)
                        -- Simple JSON decoding (would use proper library in production)
                        return {{}}
                    end
                }}
            """)
            
            # Load the main e-learning module
            elearning_result = self.lua.eval("require('init')")
            
            # Handle tuple result from require
            if isinstance(elearning_result, tuple):
                self.elearning = elearning_result[0]
            else:
                self.elearning = elearning_result
            
            # Initialize the platform
            if self.elearning and hasattr(self.elearning, 'init'):
                self.elearning.init()
            
            print("✅ Lua Engine initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize Lua environment: {e}")
            raise
    
    def _setup_python_bridges(self):
        """Setup bridges between Python and Lua for database and crypto operations"""
        
        # Database bridge
        class DatabaseBridge:
            def __init__(self, engine):
                self.engine = engine
            
            def execute(self, query: str, params: List = None):
                """Execute SQL query through Python SQLAlchemy"""
                from infrastructure.database.connection import get_db_session
                from sqlalchemy import text
                
                try:
                    with next(get_db_session()) as session:
                        result = session.execute(text(query), params or [])
                        
                        if query.strip().upper().startswith('SELECT'):
                            # For SELECT queries, return rows
                            rows = [dict(row._mapping) for row in result]
                            return {
                                'rows': rows,
                                'rowcount': len(rows)
                            }
                        else:
                            # For INSERT/UPDATE/DELETE, return metadata
                            session.commit()
                            return {
                                'lastrowid': result.lastrowid if hasattr(result, 'lastrowid') else None,
                                'rowcount': result.rowcount
                            }
                            
                except Exception as e:
                    print(f"Database error: {e}")
                    return None
        
        # Crypto bridge
        class CryptoBridge:
            @staticmethod
            def hash_password(password: str) -> str:
                """Hash password using Argon2"""
                from infrastructure.security.auth import SecurityManager
                security = SecurityManager()
                return security.get_password_hash(password)
            
            @staticmethod
            def verify_password(password: str, hashed: str) -> bool:
                """Verify password against hash"""
                from infrastructure.security.auth import SecurityManager
                security = SecurityManager()
                return security.verify_password(password, hashed)
            
            @staticmethod
            def generate_jwt_token(payload: Dict) -> str:
                """Generate JWT token"""
                from infrastructure.security.auth import SecurityManager
                security = SecurityManager()
                return security.create_access_token(data={"sub": payload.get("email", "")})
            
            @staticmethod
            def verify_jwt_token(token: str) -> Optional[Dict]:
                """Verify JWT token"""
                from infrastructure.security.auth import SecurityManager
                security = SecurityManager()
                try:
                    payload = security.decode_token(token)
                    return payload
                except:
                    return None
        
        # Set up the bridges in Lua
        db_bridge = DatabaseBridge(self)
        crypto_bridge = CryptoBridge()
        
        # Inject bridges into Lua environment (skip for now since db module is commented out)
        # if self.elearning and hasattr(self.elearning, 'db'):
        #     self.elearning.db.set_connection(db_bridge)
        
        # Setup crypto bridge functions
        self.lua.globals().python_hash_password = crypto_bridge.hash_password
        self.lua.globals().python_verify_password = crypto_bridge.verify_password
        self.lua.globals().python_generate_jwt = crypto_bridge.generate_jwt_token
        self.lua.globals().python_verify_jwt = crypto_bridge.verify_jwt_token
        
        # Update Lua crypto module to use Python bridges
        self.lua.execute("""
            local crypto = require('lua_core.utils.crypto')
            
            -- Override crypto functions to use Python bridges
            function crypto.hash_password(password)
                return python_hash_password(password)
            end
            
            function crypto.verify_password(password, hashed_password)
                return python_verify_password(password, hashed_password)
            end
            
            function crypto.generate_jwt_token(payload)
                return python_generate_jwt(payload)
            end
            
            function crypto.verify_jwt_token(token)
                return python_verify_jwt(token)
            end
        """)
    
    # User Management Methods
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user using Lua business logic"""
        try:
            if not self.elearning or not hasattr(self.elearning, 'users'):
                return {"success": False, "error": "Lua engine not properly initialized"}
            
            result = self.elearning.users.create_user(user_data)
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user using Lua business logic"""
        try:
            result = self.elearning.users.authenticate_user(email, password)
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID using Lua business logic"""
        try:
            result = self.elearning.users.get_user_by_id(user_id)
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_user_profile(self, user_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile using Lua business logic"""
        try:
            result = self.elearning.users.update_user_profile(user_id, update_data)
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user learning statistics using Lua business logic"""
        try:
            result = self.elearning.users.get_user_stats(user_id)
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Course Management Methods
    def create_course(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new course using Lua business logic"""
        try:
            result = self.elearning.courses.create_course(course_data)
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_courses(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get courses with filters using Lua business logic"""
        try:
            result = self.elearning.courses.get_courses(filters or {})
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_course_by_id(self, course_id: int) -> Dict[str, Any]:
        """Get course by ID using Lua business logic"""
        try:
            result = self.elearning.courses.get_course_by_id(course_id)
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def enroll_user(self, user_id: int, course_id: int) -> Dict[str, Any]:
        """Enroll user in course using Lua business logic"""
        try:
            result = self.elearning.courses.enroll_user(user_id, course_id)
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_courses(self, user_id: int) -> Dict[str, Any]:
        """Get user's enrolled courses using Lua business logic"""
        try:
            result = self.elearning.courses.get_user_courses(user_id)
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_progress(self, user_id: int, course_id: int, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update course progress using Lua business logic"""
        try:
            result = self.elearning.courses.update_progress(user_id, course_id, progress_data)
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_recommendations(self, user_id: int, limit: int = 5) -> Dict[str, Any]:
        """Get course recommendations using Lua business logic"""
        try:
            result = self.elearning.courses.get_recommendations(user_id, limit)
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_courses(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search courses using Lua business logic"""
        try:
            result = self.elearning.courses.search_courses(query, filters or {})
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # AI Assistant Methods
    def process_message(self, user_id: int, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process chatbot message using Lua AI logic"""
        try:
            result = self.elearning.ai.process_message(user_id, message, context or {})
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_conversation_history(self, user_id: int, limit: int = 10) -> Dict[str, Any]:
        """Get conversation history using Lua AI logic"""
        try:
            result = self.elearning.ai.get_conversation_history(user_id, limit)
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def clear_conversation_history(self, user_id: int) -> Dict[str, Any]:
        """Clear conversation history using Lua AI logic"""
        try:
            result = self.elearning.ai.clear_conversation_history(user_id)
            return self._lua_to_python(result)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Utility Methods
    def _lua_to_python(self, lua_obj) -> Any:
        """Convert Lua objects to Python objects"""
        if lua_obj is None:
            return None
        elif isinstance(lua_obj, (str, int, float, bool)):
            return lua_obj
        elif hasattr(lua_obj, 'items'):  # Lua table
            try:
                return {k: self._lua_to_python(v) for k, v in lua_obj.items()}
            except:
                return str(lua_obj)
        elif hasattr(lua_obj, '__iter__') and not isinstance(lua_obj, str):  # Lua array
            try:
                return [self._lua_to_python(item) for item in lua_obj]
            except:
                return str(lua_obj)
        else:
            return str(lua_obj)
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information"""
        try:
            config = self.elearning.config
            return self._lua_to_python(config)
        except Exception as e:
            return {"error": str(e)}

# Global Lua Engine instance
lua_engine = None

def get_lua_engine() -> LuaEngine:
    """Get or create the global Lua engine instance"""
    global lua_engine
    if lua_engine is None:
        lua_engine = LuaEngine()
    return lua_engine

def initialize_lua_engine():
    """Initialize the Lua engine on startup"""
    global lua_engine
    lua_engine = LuaEngine()
    return lua_engine
