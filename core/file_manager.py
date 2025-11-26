"""
File manager - Handle file operations and storage
"""
import os
import shutil
from datetime import datetime
from typing import Optional

class FileManager:
    """Manage file operations and storage"""
    
    # Base data directory
    DATA_DIR = "data"
    
    # Subdirectories
    RESUMES_DIR = os.path.join(DATA_DIR, "resumes")
    JOB_DESCRIPTIONS_DIR = os.path.join(DATA_DIR, "job_descriptions")
    DOCUMENTS_DIR = os.path.join(DATA_DIR, "documents")
    AUDIO_DIR = os.path.join(DATA_DIR, "recordings", "audio")
    VIDEO_DIR = os.path.join(DATA_DIR, "recordings", "video")
    LOGS_DIR = os.path.join(DATA_DIR, "logs")
    CODE_SUBMISSIONS_DIR = os.path.join(DATA_DIR, "code_submissions")
    
    @staticmethod
    def ensure_directories():
        """Create all required directories if they don't exist"""
        directories = [
            FileManager.RESUMES_DIR,
            FileManager.JOB_DESCRIPTIONS_DIR,
            FileManager.DOCUMENTS_DIR,
            FileManager.AUDIO_DIR,
            FileManager.VIDEO_DIR,
            FileManager.LOGS_DIR,
            FileManager.CODE_SUBMISSIONS_DIR,
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    @staticmethod
    def save_file(source_path: str, destination_dir: str, new_filename: Optional[str] = None) -> str:
        """
        Save file to destination directory
        
        Args:
            source_path: Source file path
            destination_dir: Destination directory
            new_filename: Optional new filename (keeps original if None)
            
        Returns:
            Path to saved file
        """
        os.makedirs(destination_dir, exist_ok=True)
        
        if new_filename:
            filename = new_filename
        else:
            filename = os.path.basename(source_path)
        
        # Add timestamp if file exists
        destination_path = os.path.join(destination_dir, filename)
        if os.path.exists(destination_path):
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}{ext}"
            destination_path = os.path.join(destination_dir, filename)
        
        shutil.copy2(source_path, destination_path)
        return destination_path
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Delete a file
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        Get file size in bytes
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes
        """
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0
    
    @staticmethod
    def list_files(directory: str, extension: Optional[str] = None) -> list:
        """
        List files in directory
        
        Args:
            directory: Directory to list
            extension: Filter by extension (e.g., '.pdf')
            
        Returns:
            List of file paths
        """
        if not os.path.exists(directory):
            return []
        
        files = []
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                if extension is None or filename.endswith(extension):
                    files.append(file_path)
        
        return files

# Initialize directories on import
FileManager.ensure_directories()
