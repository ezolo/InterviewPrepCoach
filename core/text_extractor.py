"""
Text extractor - Extract structured information from text
"""
import re
from typing import List, Optional, Dict

class TextExtractor:
    """Extract structured information from text"""
    
    # Common skills patterns
    SKILLS_PATTERNS = [
        # Programming languages
        r'\b(Python|Java|JavaScript|TypeScript|C\+\+|C#|Ruby|PHP|Swift|Kotlin|Go|Rust|R|MATLAB|Scala|Perl)\b',
        # Web technologies
        r'\b(HTML|CSS|React|Angular|Vue\.js|Node\.js|Django|Flask|FastAPI|Express|Spring|\.NET|Laravel)\b',
        # Databases
        r'\b(MySQL|PostgreSQL|MongoDB|Redis|SQLite|Oracle|SQL Server|DynamoDB|Cassandra|Neo4j)\b',
        # Cloud & DevOps
        r'\b(AWS|Azure|GCP|Docker|Kubernetes|Jenkins|GitLab|GitHub|CI/CD|Terraform|Ansible)\b',
        # Data Science & ML
        r'\b(TensorFlow|PyTorch|Scikit-learn|Pandas|NumPy|Keras|Machine Learning|Deep Learning|NLP|Computer Vision)\b',
        # Tools & Other
        r'\b(Git|Jira|Agile|Scrum|REST API|GraphQL|Microservices|Linux|Unix|Bash|PowerShell)\b',
    ]
    
    @staticmethod
    def extract_skills(text: str) -> List[str]:
        """
        Extract skills from text
        
        Args:
            text: Text to extract skills from
            
        Returns:
            List of unique skills found
        """
        skills = set()
        
        for pattern in TextExtractor.SKILLS_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.update(match.strip() for match in matches)
        
        return sorted(list(skills))
    
    @staticmethod
    def extract_email(text: str) -> Optional[str]:
        """
        Extract email address from text
        
        Args:
            text: Text to extract email from
            
        Returns:
            First email found or None
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    @staticmethod
    def extract_phone(text: str) -> Optional[str]:
        """
        Extract phone number from text
        
        Args:
            text: Text to extract phone from
            
        Returns:
            First phone number found or None
        """
        # Matches various phone formats
        phone_patterns = [
            r'\+?1?\s*\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})',  # US format
            r'\+?\d{1,3}[\s.-]?\(?\d{1,4}\)?[\s.-]?\d{1,4}[\s.-]?\d{1,9}',  # International
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    @staticmethod
    def extract_years_experience(text: str) -> Optional[int]:
        """
        Extract years of experience from text
        
        Args:
            text: Text to extract experience from
            
        Returns:
            Number of years or None
        """
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'experience\s*:?\s*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*yrs?\s+(?:of\s+)?experience',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return None
    
    @staticmethod
    def extract_education(text: str) -> List[str]:
        """
        Extract education degrees from text
        
        Args:
            text: Text to extract education from
            
        Returns:
            List of education degrees found
        """
        degrees = []
        degree_patterns = [
            r'\b(Bachelor(?:\'s)?|B\.?S\.?|B\.?A\.?|B\.?Sc\.?)\b',
            r'\b(Master(?:\'s)?|M\.?S\.?|M\.?A\.?|M\.?Sc\.?|MBA)\b',
            r'\b(Ph\.?D\.?|Doctorate)\b',
            r'\b(Associate(?:\'s)?|A\.?S\.?|A\.?A\.?)\b',
        ]
        
        for pattern in degree_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            degrees.extend(matches)
        
        return list(set(degrees))
    
    @staticmethod
    def extract_keywords(text: str, top_n: int = 20) -> List[str]:
        """
        Extract top keywords from text
        
        Args:
            text: Text to extract keywords from
            top_n: Number of top keywords to return
            
        Returns:
            List of keywords
        """
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                     'can', 'could', 'may', 'might', 'must', 'this', 'that', 'these', 'those'}
        
        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        
        # Filter stop words and count
        word_freq = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, _ in sorted_words[:top_n]]
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean text by removing extra whitespace and special characters
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text

# Convenience functions (for backwards compatibility)
def extract_skills(text: str) -> List[str]:
    """Extract skills from text"""
    return TextExtractor.extract_skills(text)

def extract_email(text: str) -> Optional[str]:
    """Extract email from text"""
    return TextExtractor.extract_email(text)

def extract_phone(text: str) -> Optional[str]:
    """Extract phone from text"""
    return TextExtractor.extract_phone(text)

def extract_years_experience(text: str) -> Optional[int]:
    """Extract years of experience from text"""
    return TextExtractor.extract_years_experience(text)

def extract_education(text: str) -> List[str]:
    """Extract education degrees from text"""
    return TextExtractor.extract_education(text)

def clean_text(text: str) -> str:
    """Clean text"""
    return TextExtractor.clean_text(text)