"""Base class for LLM providers"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, model_name: str, temperature: float = 0.7, 
                 max_tokens: int = 2000, **kwargs):
        """Initialize provider
        
        Args:
            model_name: Name of the model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_params = kwargs
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text from prompt
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate JSON response from prompt
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Parsed JSON response
        """
        pass
    
    def format_messages(self, prompt: str, system_prompt: Optional[str] = None) -> list:
        """Format messages for chat-based models
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            List of message dictionaries
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

