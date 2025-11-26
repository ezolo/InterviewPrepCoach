"""
Document parser - Handles PDF, DOCX, and TXT files
"""
import os
from typing import Optional, Dict
import PyPDF2
import pdfplumber
from docx import Document

class DocumentParser:
    """Parse various document formats to extract text"""
    
    @staticmethod
    def parse_file(file_path: str) -> Optional[str]:
        """
        Parse a document and extract text
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text or None if parsing failed
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return DocumentParser._parse_pdf(file_path)
        elif file_ext == '.docx':
            return DocumentParser._parse_docx(file_path)
        elif file_ext == '.txt':
            return DocumentParser._parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        """Parse PDF file using pdfplumber (primary) and PyPDF2 (fallback)"""
        text = ""
        
        try:
            # Try pdfplumber first (better for formatted PDFs)
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if text.strip():
                return text
        except Exception as e:
            print(f"pdfplumber failed: {e}, trying PyPDF2...")
        
        try:
            # Fallback to PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            return text
        except Exception as e:
            print(f"PyPDF2 failed: {e}")
            return ""
    
    @staticmethod
    def _parse_docx(file_path: str) -> str:
        """Parse DOCX file"""
        try:
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            return text
        except Exception as e:
            print(f"Error parsing DOCX: {e}")
            return ""
    
    @staticmethod
    def _parse_txt(file_path: str) -> str:
        """Parse TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read()
            except Exception as e:
                print(f"Error parsing TXT: {e}")
                return ""
        except Exception as e:
            print(f"Error parsing TXT: {e}")
            return ""
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict:
        """Get file information"""
        if not os.path.exists(file_path):
            return {}
        
        file_stats = os.stat(file_path)
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        return {
            'name': file_name,
            'path': file_path,
            'type': file_ext,
            'size': file_stats.st_size,
            'size_mb': round(file_stats.st_size / (1024 * 1024), 2)
        }
