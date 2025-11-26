"""LLM service - manages LLM provider selection and usage"""

from typing import Optional, Dict, Any
from ai.providers import (
    BaseLLMProvider, OpenAIProvider, AnthropicProvider,
    BedrockProvider, OllamaProvider
)
from database import DatabaseManager
from core.encryption import Encryption
from config.settings import Settings

class LLMService:
    """Manages LLM provider selection and configuration"""
    
    _instance = None
    _current_provider: Optional[BaseLLMProvider] = None
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_user_llm_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's active LLM settings from database
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with LLM settings or None
        """
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT provider, model_name, api_key_encrypted, endpoint_url,
                           temperature, max_tokens, top_p
                    FROM llm_settings
                    WHERE user_id = %s AND is_active = TRUE
                    LIMIT 1
                """, (user_id,))
                
                result = cursor.fetchone()
                if result:
                    # Decrypt API key if present
                    if result['api_key_encrypted']:
                        result['api_key'] = Encryption.decrypt(result['api_key_encrypted'])
                    return result
                return None
        except Exception as e:
            print(f"Error fetching LLM settings: {e}")
            return None
    
    def get_provider(self, user_id: int) -> BaseLLMProvider:
        """Get LLM provider for user
        
        Args:
            user_id: User ID
            
        Returns:
            LLM provider instance
        """
        # Try to get user settings
        settings = self.get_user_llm_settings(user_id)
        
        if settings:
            provider_type = settings['provider']
            model_name = settings['model_name']
            temperature = float(settings.get('temperature', 0.7))
            max_tokens = settings.get('max_tokens', 2000)
            
            if provider_type == 'openai':
                api_key = settings.get('api_key') or Settings.OPENAI_API_KEY
                return OpenAIProvider(
                    api_key=api_key,
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            
            elif provider_type == 'anthropic':
                api_key = settings.get('api_key') or Settings.ANTHROPIC_API_KEY
                return AnthropicProvider(
                    api_key=api_key,
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            
            elif provider_type == 'bedrock':
                return BedrockProvider(
                    model_name=model_name,
                    region_name=Settings.AWS_REGION,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            
            elif provider_type == 'ollama':
                base_url = settings.get('endpoint_url') or Settings.OLLAMA_BASE_URL
                return OllamaProvider(
                    model_name=model_name,
                    base_url=base_url,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
        
        # Default fallback: try OpenAI if key is available
        if Settings.OPENAI_API_KEY:
            return OpenAIProvider(
                api_key=Settings.OPENAI_API_KEY,
                model_name="gpt-4",
                temperature=0.7,
                max_tokens=2000
            )
        
        # Fallback to Ollama (local)
        return OllamaProvider(
            model_name="llama3.2",
            base_url=Settings.OLLAMA_BASE_URL
        )
    
    def save_llm_settings(self, user_id: int, provider: str, model_name: str,
                         api_key: Optional[str] = None, endpoint_url: Optional[str] = None,
                         temperature: float = 0.7, max_tokens: int = 2000) -> bool:
        """Save LLM settings for user
        
        Args:
            user_id: User ID
            provider: Provider name (openai, anthropic, bedrock, ollama)
            model_name: Model name
            api_key: API key (will be encrypted)
            endpoint_url: Endpoint URL (for Ollama/Bedrock)
            temperature: Temperature
            max_tokens: Max tokens
            
        Returns:
            True if successful
        """
        try:
            # Encrypt API key if provided
            api_key_encrypted = None
            if api_key:
                api_key_encrypted = Encryption.encrypt(api_key)
            
            with DatabaseManager.get_cursor() as cursor:
                # Check if settings already exist for this user-provider combination
                cursor.execute("""
                    SELECT id FROM llm_settings
                    WHERE user_id = %s AND provider = %s
                """, (user_id, provider))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing settings
                    cursor.execute("""
                        UPDATE llm_settings
                        SET model = %s, model_name = %s, api_key_encrypted = %s, 
                            endpoint_url = %s, temperature = %s, max_tokens = %s,
                            is_active = TRUE, updated_at = NOW()
                        WHERE user_id = %s AND provider = %s
                    """, (model_name, model_name, api_key_encrypted, endpoint_url,
                          temperature, max_tokens, user_id, provider))
                    
                    # Deactivate other settings for this user
                    cursor.execute("""
                        UPDATE llm_settings
                        SET is_active = FALSE
                        WHERE user_id = %s AND provider != %s
                    """, (user_id, provider))
                else:
                    # Deactivate current settings
                    cursor.execute("""
                        UPDATE llm_settings
                        SET is_active = FALSE
                        WHERE user_id = %s
                    """, (user_id,))
                    
                    # Insert new settings
                    cursor.execute("""
                        INSERT INTO llm_settings
                        (user_id, provider, model, model_name, api_key_encrypted, endpoint_url,
                         temperature, max_tokens, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                    """, (user_id, provider, model_name, model_name, api_key_encrypted, endpoint_url,
                          temperature, max_tokens))
            
            return True
        except Exception as e:
            print(f"Error saving LLM settings: {e}")
            return False

