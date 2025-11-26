"""Anthropic Claude provider implementation"""

import json
from typing import Dict, Any, Optional
from anthropic import Anthropic
from .base_provider import BaseLLMProvider

class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self, api_key: str, model_name: str = "claude-3-sonnet-20240229", **kwargs):
        super().__init__(model_name, **kwargs)
        self.client = Anthropic(api_key=api_key)
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text from prompt
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
        """
        try:
            kwargs = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self.client.messages.create(**kwargs)
            
            return response.content[0].text
        
        except Exception as e:
            print(f"Anthropic API error: {e}")
            return f"Error generating response: {str(e)}"
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate JSON response from prompt
        
        Args:
            prompt: User prompt (should request JSON format)
            system_prompt: Optional system prompt
            
        Returns:
            Parsed JSON response
        """
        response_text = ""
        try:
            if "JSON" not in prompt and "json" not in prompt:
                prompt += "\n\nRespond with valid JSON only."
            
            response_text = self.generate(prompt, system_prompt)
            
            # Clean response
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            return json.loads(response_text)
        
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return {
                "error": f"Failed to parse JSON response: {e}",
                "raw_response": response_text
            }
        except Exception as e:
            print(f"Error: {e}")
            return {
                "error": str(e),
                "raw_response": response_text
            }

