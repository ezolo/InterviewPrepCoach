"""
LLM provider factory - Creates provider instances
"""
from typing import Optional
from ai.base_provider import LLMProvider
from ai.openai_provider import OpenAIProvider
from ai.anthropic_provider import AnthropicProvider
from ai.bedrock_provider import BedrockProvider
from ai.ollama_provider import OllamaProvider

class ProviderFactory:
    """Factory for creating LLM provider instances"""
    
    PROVIDERS = {
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'bedrock': BedrockProvider,
        'ollama': OllamaProvider,
    }
    
    @staticmethod
    def create_provider(
        provider_name: str,
        api_key: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Optional[LLMProvider]:
        """
        Create a provider instance
        
        Args:
            provider_name: Name of the provider ('openai', 'anthropic', 'bedrock', 'ollama')
            api_key: API key for the provider
            model: Model name
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments
            
        Returns:
            Provider instance or None if provider not found
        """
        provider_class = ProviderFactory.PROVIDERS.get(provider_name.lower())
        
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        return provider_class(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    @staticmethod
    def get_available_providers() -> list:
        """Get list of available provider names"""
        return list(ProviderFactory.PROVIDERS.keys())
    
    @staticmethod
    def get_models_for_provider(provider_name: str) -> list:
        """
        Get available models for a provider
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            List of model names
        """
        provider_class = ProviderFactory.PROVIDERS.get(provider_name.lower())
        
        if not provider_class:
            return []
        
        return provider_class.get_available_models()
