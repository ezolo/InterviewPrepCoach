"""
Validators for input validation and sanitization
"""
import os
import re
import validators as validator_lib
from typing import Tuple, Optional

class Validators:
    """Input validation and sanitization"""
    
    ALLOWED_FILE_EXTENSIONS = {'.pdf', '.docx', '.txt'}
    MAX_FILE_SIZE_MB = 10
    
    @staticmethod
    def validate_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file
        
        Args:
            file_path: Path to file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not os.path.exists(file_path):
            return False, \"File does not exist\"
        
        # Check file extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in Validators.ALLOWED_FILE_EXTENSIONS:
            return False, f\"Invalid file type. Allowed: {', '.join(Validators.ALLOWED_FILE_EXTENSIONS)}\"
        
        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > Validators.MAX_FILE_SIZE_MB:
            return False, f\"File too large. Maximum size: {Validators.MAX_FILE_SIZE_MB}MB\"
        
        return True, None
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not email:
            return False
        return validator_lib.email(email) == True
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not url:
            return False
        return validator_lib.url(url) == True
    
    @staticmethod
    def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize text input
        
        Args:
            text: Text to sanitize
            max_length: Maximum length (truncate if longer)
            
        Returns:
            Sanitized text
        """
        if not text:
            return \"\"
        
        # Remove potentially dangerous characters but keep basic punctuation
        text = re.sub(r'[<>{}]', '', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Truncate if needed
        if max_length and len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    @staticmethod
    def validate_temperature(temperature: float) -> bool:
        """
        Validate LLM temperature parameter
        
        Args:
            temperature: Temperature value
            
        Returns:
            True if valid, False otherwise
        """
        return 0.0 <= temperature <= 2.0
    
    @staticmethod
    def validate_max_tokens(max_tokens: int) -> bool:
        """
        Validate max tokens parameter
        
        Args:
            max_tokens: Max tokens value
            
        Returns:
            True if valid, False otherwise
        """
        return 1 <= max_tokens <= 100000
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to remove dangerous characters
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path separators and dangerous characters
        filename = re.sub(r'[/\\\\:*?\"<>|]', '_', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        # Ensure filename is not empty
        if not filename:
            filename = \"unnamed_file\"
        return filename
