"""
Ollama provider implementation (local LLMs)
"""
from typing import List, Dict, Optional
import httpx
from ai.base_provider import LLMProvider

class OllamaProvider(LLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(self, api_key: str = "not_needed", model: str = "llama3", 
                 temperature: float = 0.7, max_tokens: int = 2000,
                 base_url: str = "http://localhost:11434"):
        super().__init__(api_key, model, temperature, max_tokens)
        self.base_url = base_url.rstrip('/')
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using Ollama API"""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\\n\\n{prompt}"
            
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                },
                timeout=120.0
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat with message history"""
        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                },
                timeout=120.0
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test Ollama connection"""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Ollama connection test failed: {e}")
            return False
    
    @staticmethod
    def get_available_models() -> List[str]:
        """Get available Ollama models (common ones)"""
        return [
            "llama3",
            "llama2",
            "mistral",
            "mixtral",
            "phi3",
            "gemma",
            "codellama",
            "neural-chat",
        ]
