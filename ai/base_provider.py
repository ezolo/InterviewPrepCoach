"""
Base LLM provider - Abstract interface for all providers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: str, model: str, temperature: float = 0.7, max_tokens: int = 2000):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from the LLM
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Generated response text
        """
        pass
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Chat with the LLM using message history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Generated response text
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test the connection to the provider
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @staticmethod
    @abstractmethod
    def get_available_models() -> List[str]:
        """
        Get list of available models for this provider
        
        Returns:
            List of model names
        """
        pass
