"""
LLM settings service - Manage LLM provider configuration
"""
import json
from typing import Optional, Dict
from database.connection import execute_query
from core.encryption import get_encryptor
from ai.provider_factory import ProviderFactory

class LLMSettingsService:
    """Handle LLM settings operations"""
    
    @staticmethod
    def save_settings(user_id: int, provider: str, model: str, api_key: str,
                     temperature: float = 0.7, max_tokens: int = 2000,
                     additional_config: Dict = None) -> Optional[int]:
        """
        Save LLM settings
        
        Args:
            user_id: User ID
            provider: Provider name
            model: Model name
            api_key: API key (will be encrypted)
            temperature: Temperature setting
            max_tokens: Max tokens setting
            additional_config: Additional provider-specific config
            
        Returns:
            Settings ID or None
        """
        try:
            encryptor = get_encryptor()
            encrypted_key = encryptor.encrypt(api_key)
            
            # Deactivate existing settings
            execute_query(
                "UPDATE llm_settings SET is_active = FALSE WHERE user_id = %s",
                (user_id,),
                commit=True
            )
            
            # Insert new settings
            query = """
            INSERT INTO llm_settings 
            (user_id, provider, model, api_key_encrypted, temperature, max_tokens, 
             additional_config, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            config_json = json.dumps(additional_config) if additional_config else None
            
            return execute_query(
                query,
                (user_id, provider, model, encrypted_key, temperature, max_tokens,
                 config_json, True),
                commit=True
            )
        except Exception as e:
            print(f"Error saving settings: {e}")
            return None
    
    @staticmethod
    def get_active_settings(user_id: int) -> Optional[Dict]:
        """Get user's active LLM settings"""
        query = """
        SELECT * FROM llm_settings 
        WHERE user_id = %s AND is_active = TRUE 
        ORDER BY created_at DESC LIMIT 1
        """
        return execute_query(query, (user_id,), fetch_one=True)
    
    @staticmethod
    def get_decrypted_settings(user_id: int) -> Optional[Dict]:
        """
        Get settings with decrypted API key
        
        Returns:
            Settings dict with decrypted api_key or None
        """
        settings = LLMSettingsService.get_active_settings(user_id)
        
        if not settings:
            return None
        
        try:
            encryptor = get_encryptor()
            settings['api_key'] = encryptor.decrypt(settings['api_key_encrypted'])
            return settings
        except Exception as e:
            print(f"Error decrypting settings: {e}")
            return None
    
    @staticmethod
    def test_connection(provider: str, model: str, api_key: str, **kwargs) -> bool:
        """
        Test connection to LLM provider
        
        Args:
            provider: Provider name
            model: Model name
            api_key: API key
            **kwargs: Additional provider-specific arguments
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            provider_instance = ProviderFactory.create_provider(
                provider_name=provider,
                api_key=api_key,
                model=model,
                **kwargs
            )
            
            return provider_instance.test_connection()
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    @staticmethod
    def get_available_providers() -> list:
        """Get list of available LLM providers"""
        return ProviderFactory.get_available_providers()
    
    @staticmethod
    def get_models_for_provider(provider: str) -> list:
        """Get available models for a provider"""
        return ProviderFactory.get_models_for_provider(provider)
