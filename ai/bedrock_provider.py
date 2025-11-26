"""
AWS Bedrock provider implementation
"""
from typing import List, Dict, Optional
import json
import boto3
from ai.base_provider import LLMProvider

class BedrockProvider(LLMProvider):
    """AWS Bedrock provider"""
    
    def __init__(self, api_key: str, model: str = "anthropic.claude-3-sonnet-20240229-v1:0", 
                 temperature: float = 0.7, max_tokens: int = 2000,
                 region: str = "us-east-1"):
        # For Bedrock, api_key format is "access_key:secret_key"
        super().__init__(api_key, model, temperature, max_tokens)
        
        if ":" in api_key:
            access_key, secret_key = api_key.split(":", 1)
        else:
            access_key = api_key
            secret_key = ""
        
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using AWS Bedrock"""
        try:
            # Format depends on model type
            if "anthropic.claude" in self.model:
                return self._generate_claude(prompt, system_prompt)
            elif "amazon.titan" in self.model:
                return self._generate_titan(prompt, system_prompt)
            else:
                raise ValueError(f"Unsupported model: {self.model}")
        except Exception as e:
            raise Exception(f"Bedrock API error: {str(e)}")
    
    def _generate_claude(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate using Claude models on Bedrock"""
        messages = [{"role": "user", "content": prompt}]
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": messages
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        response = self.client.invoke_model(
            modelId=self.model,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
    
    def _generate_titan(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate using Titan models on Bedrock"""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        body = {
            "inputText": full_prompt,
            "textGenerationConfig": {
                "maxTokenCount": self.max_tokens,
                "temperature": self.temperature,
            }
        }
        
        response = self.client.invoke_model(
            modelId=self.model,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['results'][0]['outputText']
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat with message history"""
        try:
            if "anthropic.claude" in self.model:
                # Extract system message if present
                system_prompt = None
                chat_messages = []
                
                for msg in messages:
                    if msg["role"] == "system":
                        system_prompt = msg["content"]
                    else:
                        chat_messages.append(msg)
                
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "messages": chat_messages
                }
                
                if system_prompt:
                    body["system"] = system_prompt
                
                response = self.client.invoke_model(
                    modelId=self.model,
                    body=json.dumps(body)
                )
                
                response_body = json.loads(response['body'].read())
                return response_body['content'][0]['text']
            else:
                # For non-Claude models, concatenate messages
                full_prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                return self.generate(full_prompt)
        except Exception as e:
            raise Exception(f"Bedrock API error: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test Bedrock connection"""
        try:
            self.client.list_foundation_models()
            return True
        except Exception as e:
            print(f"Bedrock connection test failed: {e}")
            return False
    
    @staticmethod
    def get_available_models() -> List[str]:
        """Get available Bedrock models"""
        return [
            "anthropic.claude-3-opus-20240229-v1:0",
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "anthropic.claude-3-haiku-20240307-v1:0",
            "anthropic.claude-v2:1",
            "anthropic.claude-v2",
            "amazon.titan-text-express-v1",
            "amazon.titan-text-lite-v1",
        ]
