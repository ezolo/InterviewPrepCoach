"""
Resume and profile service
"""
import os
import json
from datetime import datetime
from typing import Optional, Dict, List
from database.connection import execute_query
from core.document_parser import DocumentParser
from core.text_extractor import TextExtractor
from core.file_manager import FileManager

class ResumeService:
    """Handle resume operations"""
    
    @staticmethod
    def upload_resume(user_id: int, file_path: str, resume_name: Optional[str] = None) -> Optional[int]:
        """
        Upload and parse resume
        
        Args:
            user_id: User ID
            file_path: Path to resume file
            resume_name: Optional custom name for the resume (defaults to file name)
            
        Returns:
            Resume ID or None
        """
        try:
            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"File not found: {file_path}")
            
            # Parse document
            text = DocumentParser.parse_file(file_path)
            if not text:
                raise ValueError("Could not extract text from resume")
            
            # Extract information
            skills = TextExtractor.extract_skills(text)
            email = TextExtractor.extract_email(text)
            phone = TextExtractor.extract_phone(text)
            years_exp = TextExtractor.extract_years_experience(text)
            education = TextExtractor.extract_education(text)
            
            parsed_data = {
                'skills': skills,
                'email': email,
                'phone': phone,
                'years_experience': years_exp,
                'education': education,
                'keywords': TextExtractor.extract_keywords(text)
            }
            
            # Save file
            saved_path = FileManager.save_file(
                file_path,
                FileManager.RESUMES_DIR
            )
            
            # Get file info
            file_info = DocumentParser.get_file_info(saved_path)
            
            # Use custom name if provided, otherwise use file name
            display_name = resume_name.strip() if resume_name and resume_name.strip() else file_info['name']
            
            # Insert into database
            query = """
            INSERT INTO resumes 
            (user_id, file_name, file_path, file_type, resume_text, extracted_text, parsed_data, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            resume_id = execute_query(
                query,
                (user_id, display_name, saved_path, file_info['type'], 
                 text, text, json.dumps(parsed_data), True),
                commit=True
            )
            
            # Sync resume_id column with id for code compatibility
            if resume_id:
                execute_query(
                    "UPDATE resumes SET resume_id = id WHERE id = %s",
                    (resume_id,),
                    commit=True
                )
            
            # Mark other resumes as inactive
            execute_query(
                "UPDATE resumes SET is_active = FALSE WHERE user_id = %s AND resume_id != %s",
                (user_id, resume_id),
                commit=True
            )
            
            return resume_id
        except Exception as e:
            print(f"Error uploading resume: {e}")
            return None
    
    @staticmethod
    def get_active_resume(user_id: int) -> Optional[Dict]:
        """Get user's active resume"""
        query = """
        SELECT * FROM resumes 
        WHERE user_id = %s AND is_active = TRUE 
        ORDER BY uploaded_at DESC LIMIT 1
        """
        return execute_query(query, (user_id,), fetch_one=True)
    
    @staticmethod
    def get_all_resumes(user_id: int) -> List[Dict]:
        """Get all resumes for user"""
        query = """
        SELECT * FROM resumes 
        WHERE user_id = %s 
        ORDER BY uploaded_at DESC
        """
        return execute_query(query, (user_id,), fetch_all=True) or []
    
    @staticmethod
    def get_resume_by_id(resume_id: int) -> Optional[Dict]:
        """Get resume by ID"""
        query = "SELECT * FROM resumes WHERE resume_id = %s"
        return execute_query(query, (resume_id,), fetch_one=True)
    
    @staticmethod
    def delete_resume(resume_id: int) -> bool:
        """Delete a resume"""
        try:
            # Get resume to delete file
            resume = ResumeService.get_resume_by_id(resume_id)
            if resume and resume.get('file_path'):
                FileManager.delete_file(resume['file_path'])
            
            # Delete from database
            execute_query(
                "DELETE FROM resumes WHERE resume_id = %s",
                (resume_id,),
                commit=True
            )
            return True
        except Exception as e:
            print(f"Error deleting resume: {e}")
            return False
    
    @staticmethod
    def get_user_resumes(user_id: int) -> List[Dict]:
        """Get all active resumes for a user"""
        query = """
        SELECT * FROM resumes 
        WHERE user_id = %s AND is_active = TRUE 
        ORDER BY uploaded_at DESC
        """
        return execute_query(query, (user_id,), fetch_all=True) or []