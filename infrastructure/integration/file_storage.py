"""
File storage service for handling uploads and content management.
Infrastructure Layer - Integration Package
"""

import os
import aiofiles
import hashlib
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path
import mimetypes
from dotenv import load_dotenv

load_dotenv()

class FileStorage:
    """
    File storage service for managing uploaded content and learning materials.
    Implements file management from the Integration Package.
    """
    
    def __init__(self):
        self.upload_dir = Path(os.getenv("UPLOAD_DIR", "./uploads"))
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
        self.allowed_extensions = {
            'image': {'.jpg', '.jpeg', '.png', '.gif', '.webp'},
            'video': {'.mp4', '.avi', '.mov', '.wmv', '.flv'},
            'document': {'.pdf', '.doc', '.docx', '.txt', '.rtf'},
            'audio': {'.mp3', '.wav', '.ogg', '.m4a'},
            'archive': {'.zip', '.rar', '.7z', '.tar', '.gz'}
        }
        
        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different content types
        for content_type in ['courses', 'profiles', 'temp', 'exports']:
            (self.upload_dir / content_type).mkdir(exist_ok=True)
    
    async def save_file(self, file_content: bytes, filename: str, content_type: str = 'temp') -> Dict[str, str]:
        """
        Save uploaded file to storage.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            content_type: Type of content (courses, profiles, temp, exports)
            
        Returns:
            Dictionary with file information
        """
        try:
            # Validate file size
            if len(file_content) > self.max_file_size:
                return {
                    "status": "error",
                    "message": f"File size exceeds maximum allowed size of {self.max_file_size} bytes"
                }
            
            # Validate file extension
            file_extension = Path(filename).suffix.lower()
            if not self._is_allowed_extension(file_extension):
                return {
                    "status": "error",
                    "message": f"File extension {file_extension} is not allowed"
                }
            
            # Generate unique filename
            file_hash = hashlib.md5(file_content).hexdigest()
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{file_hash}{file_extension}"
            
            # Determine file path
            file_path = self.upload_dir / content_type / unique_filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Get file info
            file_info = await self.get_file_info(str(file_path))
            
            return {
                "status": "success",
                "filename": unique_filename,
                "original_filename": filename,
                "file_path": str(file_path),
                "relative_path": f"{content_type}/{unique_filename}",
                "file_size": len(file_content),
                "content_type": content_type,
                "mime_type": file_info.get("mime_type"),
                "upload_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error saving file: {str(e)}"
            }
    
    async def get_file(self, file_path: str) -> Optional[bytes]:
        """
        Retrieve file content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content as bytes or None if not found
        """
        try:
            full_path = self.upload_dir / file_path if not Path(file_path).is_absolute() else Path(file_path)
            
            if not full_path.exists():
                return None
            
            async with aiofiles.open(full_path, 'rb') as f:
                return await f.read()
                
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file was deleted successfully
        """
        try:
            full_path = self.upload_dir / file_path if not Path(file_path).is_absolute() else Path(file_path)
            
            if full_path.exists():
                full_path.unlink()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False
    
    async def get_file_info(self, file_path: str) -> Dict[str, str]:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            full_path = Path(file_path)
            
            if not full_path.exists():
                return {"status": "error", "message": "File not found"}
            
            stat = full_path.stat()
            mime_type, _ = mimetypes.guess_type(str(full_path))
            
            return {
                "status": "success",
                "filename": full_path.name,
                "file_size": stat.st_size,
                "mime_type": mime_type or "application/octet-stream",
                "created_date": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": full_path.suffix.lower()
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Error getting file info: {str(e)}"}
    
    async def list_files(self, content_type: str = None, limit: int = 100) -> List[Dict]:
        """
        List files in storage.
        
        Args:
            content_type: Filter by content type (courses, profiles, etc.)
            limit: Maximum number of files to return
            
        Returns:
            List of file information dictionaries
        """
        try:
            files = []
            search_dir = self.upload_dir / content_type if content_type else self.upload_dir
            
            if not search_dir.exists():
                return []
            
            for file_path in search_dir.rglob('*'):
                if file_path.is_file() and len(files) < limit:
                    file_info = await self.get_file_info(str(file_path))
                    if file_info.get("status") == "success":
                        file_info["relative_path"] = str(file_path.relative_to(self.upload_dir))
                        files.append(file_info)
            
            return files
            
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    def _is_allowed_extension(self, extension: str) -> bool:
        """Check if file extension is allowed."""
        for file_type, extensions in self.allowed_extensions.items():
            if extension in extensions:
                return True
        return False
    
    def get_storage_stats(self) -> Dict[str, int]:
        """Get storage statistics."""
        try:
            total_files = 0
            total_size = 0
            
            for file_path in self.upload_dir.rglob('*'):
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "max_file_size_mb": round(self.max_file_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            print(f"Error getting storage stats: {e}")
            return {"error": str(e)}

# Global instance
file_storage = FileStorage()

