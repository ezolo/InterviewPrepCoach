"""Ollama local LLM provider implementation"""

import json
import re
from typing import Dict, Any, Optional
import requests
from .base_provider import BaseLLMProvider

class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(self, model_name: str = "llama3.2", 
                 base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(model_name, **kwargs)
        self.base_url = base_url.rstrip('/')
    
    def _strip_json_comments(self, text: str) -> str:
        """Remove comments from JSON string (// and /* */ style comments)
        
        Args:
            text: JSON string potentially containing comments
            
        Returns:
            JSON string with comments removed
        """
        # Remove single-line comments (// ...)
        # But preserve // inside strings
        lines = text.split('\n')
        result_lines = []
        in_string = False
        string_char = None
        
        for line in lines:
            cleaned_line = []
            i = 0
            while i < len(line):
                char = line[i]
                
                # Track string boundaries
                if char in ('"', "'") and (i == 0 or line[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
                
                # Only remove // if we're not in a string
                if not in_string and i < len(line) - 1 and line[i:i+2] == '//':
                    # Found comment, skip rest of line
                    break
                
                cleaned_line.append(char)
                i += 1
            
            result_lines.append(''.join(cleaned_line))
        
        # Remove multi-line comments (/* ... */)
        result = '\n'.join(result_lines)
        result = re.sub(r'/\*.*?\*/', '', result, flags=re.DOTALL)
        
        return result
    
    def _repair_json(self, text: str) -> str:
        """Attempt to repair common JSON issues
        
        Args:
            text: Potentially malformed JSON string
            
        Returns:
            Repaired JSON string
        """
        # Use the more comprehensive _fix_array_items method for array repair
        # This method handles nested structures and is more robust
        text = self._fix_array_items(text)
        
        return text
    
    def _fix_array_items(self, text: str) -> str:
        """Fix unquoted strings in JSON arrays (e.g., [..., SQL, ...] -> [..., "SQL", ...])"""
        # Pattern to find array items that might be missing quotes
        # Look for patterns like: "item", unquoted_item, "item"
        def fix_array(match):
            array_content = match.group(0)
            # Find all items in the array
            # Split by comma, but respect quoted strings
            items = []
            current = ""
            in_quotes = False
            quote_char = None
            depth = 0  # Track nested brackets/braces
            
            for i, char in enumerate(array_content):
                if char in ('"', "'") and (i == 0 or array_content[i-1] != '\\'):
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                        quote_char = None
                    current += char
                elif char == '[' and not in_quotes:
                    depth += 1
                    current += char
                elif char == ']' and not in_quotes:
                    depth -= 1
                    current += char
                elif char == '{' and not in_quotes:
                    depth += 1
                    current += char
                elif char == '}' and not in_quotes:
                    depth -= 1
                    current += char
                elif char == ',' and depth == 0 and not in_quotes:
                    items.append(current.strip())
                    current = ""
                else:
                    current += char
            
            if current.strip():
                items.append(current.strip())
            
            # Fix each item
            fixed_items = []
            for item in items:
                item = item.strip().rstrip(',')
                if not item:
                    continue
                # Already properly quoted
                if (item.startswith('"') and item.endswith('"')) or \
                   (item.startswith("'") and item.endswith("'")):
                    fixed_items.append(item)
                # Number, boolean, null, object, or array
                elif item.lower() in ('true', 'false', 'null') or \
                     item.startswith('{') or item.startswith('[') or \
                     (item.replace('.', '').replace('-', '').replace('e', '').replace('E', '').replace('+', '').isdigit()):
                    fixed_items.append(item)
                # Missing quotes - add them
                else:
                    # Remove any existing partial quotes
                    item = item.strip('"').strip("'")
                    fixed_items.append(f'"{item}"')
            
            return '[' + ', '.join(fixed_items) + ']'
        
        # Find all JSON arrays and fix them
        # Pattern: [ followed by content, ending with ]
        result = re.sub(r'\[[^\]]*\]', fix_array, text)
        return result
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text from prompt
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
        """
        try:
            # Build prompt - keep it simple for Ollama
            full_prompt = prompt
            if system_prompt:
                # System prompt now contains format instructions - preserve it fully (it's ~1500 chars)
                # Only truncate if it's extremely long (shouldn't happen with our prompts)
                system_truncated = system_prompt[:2000] if len(system_prompt) > 2000 else system_prompt
                full_prompt = f"{system_truncated}\n\n{prompt}"
            
            # Limit total prompt length to prevent 500 errors (Ollama can be sensitive to long prompts)
            # Use a more conservative limit for better reliability
            # Increased limit since we're now truncating input data instead
            max_prompt_length = 2000
            if len(full_prompt) > max_prompt_length:
                # Smart truncation: preserve system prompt and format instructions
                # System prompt is at the start, format instructions should be preserved
                # Truncate from the middle of the data section
                system_length = len(system_truncated) if system_prompt else 0
                reserved_length = system_length + 200  # Reserve space for system + format instructions
                data_section = prompt
                
                if len(full_prompt) > max_prompt_length:
                    # Truncate data section, keeping start and end
                    max_data_length = max_prompt_length - reserved_length - 100  # Buffer
                    if len(data_section) > max_data_length:
                        first_part = int(max_data_length * 0.6)
                        last_part = max_data_length - first_part - 50
                        data_section = data_section[:first_part] + "\n\n[... truncated ...]\n\n" + data_section[-last_part:]
                    
                    # Reconstruct with preserved system prompt
                    if system_prompt:
                        full_prompt = f"{system_truncated}\n\n{data_section}"
                    else:
                        full_prompt = data_section
                    
                    original_length = len(prompt) + (len(system_truncated) if system_prompt else 0)
                    print(f"[WARNING] Prompt truncated from {original_length} to {len(full_prompt)} chars (preserved format instructions)")
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False
            }
            
            # Add optional parameters only if they're set
            if self.temperature is not None:
                payload["options"] = {
                    "temperature": self.temperature,
                    "num_predict": 2000  # Limit output tokens to prevent memory issues
                }
            
            print(f"[DEBUG] Ollama request: model={self.model_name}, prompt_length={len(full_prompt)}")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=180
            )
            
            # Check for errors before parsing JSON
            if response.status_code != 200:
                error_detail = "Unknown error"
                error_json_data = None
                try:
                    error_json_data = response.json()
                    # Handle both dict and string error formats
                    if isinstance(error_json_data, dict):
                        error_detail = error_json_data.get('error', error_json_data.get('message', str(error_json_data)))
                    else:
                        error_detail = str(error_json_data)
                except:
                    error_detail = response.text[:200] if hasattr(response, 'text') else str(response.status_code)
                
                # Check for memory-related errors and provide helpful guidance
                error_lower = str(error_detail).lower()
                if 'memory' in error_lower or 'gpu' in error_lower or 'system memory' in error_lower:
                    # Check if it's already a small model
                    is_small_model = any(x in self.model_name.lower() for x in ['mini', '1b', '3b', 'phi'])
                    
                    if is_small_model:
                        # Already using small model - suggest CPU mode or freeing memory
                        helpful_msg = (
                            f"⚠️ Insufficient memory even for '{self.model_name}'. Solutions:\n"
                            f"1. Force CPU-only mode (Windows PowerShell):\n"
                            f"   $env:OLLAMA_NUM_GPU='0'\n"
                            f"   ollama serve\n"
                            f"2. Free up system memory:\n"
                            f"   • Close other applications\n"
                            f"   • Restart your computer\n"
                            f"3. Try tiny model: ollama pull tinyllama\n"
                            f"   (Then update Settings to use 'tinyllama')\n"
                            f"Original error: {error_detail}"
                        )
                    else:
                        # Using large model - suggest smaller ones
                        helpful_msg = (
                            f"⚠️ Insufficient memory to load model '{self.model_name}'. Solutions:\n"
                            f"1. Use smaller model (recommended):\n"
                            f"   • Run: ollama pull tinyllama (smallest)\n"
                            f"   • Or: ollama pull phi3:mini\n"
                            f"   • Then update Settings to use the smaller model\n"
                            f"2. Force CPU-only mode (Windows PowerShell):\n"
                            f"   $env:OLLAMA_NUM_GPU='0'\n"
                            f"   ollama serve\n"
                            f"3. Free up system memory\n"
                            f"Original error: {error_detail}"
                        )
                    print(f"[ERROR] {helpful_msg}")
                    return f"Error: {helpful_msg}"
                
                error_msg = f"Ollama server error {response.status_code}: {error_detail}"
                print(f"[ERROR] {error_msg}")
                return f"Error: {error_msg}"
            
            response.raise_for_status()
            result = response.json()
            
            if 'response' not in result:
                print(f"[ERROR] Ollama response missing 'response' key: {result}")
                return "Error: Invalid response format from Ollama"
            
            return result.get('response', '')
        
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Ollama. Make sure Ollama is running on http://localhost:11434"
            print(f"[ERROR] {error_msg}")
            return f"Error: {error_msg}"
        except requests.exceptions.HTTPError as e:
            error_detail = "Unknown error"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    # Handle both dict and string error formats
                    if isinstance(error_json, dict):
                        error_detail = error_json.get('error', error_json.get('message', str(error_json)))
                    else:
                        error_detail = str(error_json)
                except:
                    error_detail = e.response.text[:200] if hasattr(e.response, 'text') else str(e.response.status_code)
            
            # Check for memory-related errors
            error_lower = str(error_detail).lower()
            if 'memory' in error_lower or 'gpu' in error_lower or 'system memory' in error_lower:
                # Check if it's already a small model
                is_small_model = any(x in self.model_name.lower() for x in ['mini', '1b', '3b', 'phi'])
                
                if is_small_model:
                    # Already using small model - suggest CPU mode or freeing memory
                    helpful_msg = (
                        f"⚠️ Insufficient memory even for '{self.model_name}'. Solutions:\n"
                        f"1. Force CPU-only mode (Windows PowerShell):\n"
                        f"   $env:OLLAMA_NUM_GPU='0'\n"
                        f"   ollama serve\n"
                        f"2. Free up system memory:\n"
                        f"   • Close other applications\n"
                        f"   • Restart your computer\n"
                        f"3. Try tiny model: ollama pull tinyllama\n"
                        f"   (Then update Settings to use 'tinyllama')\n"
                        f"Original error: {error_detail}"
                    )
                else:
                    # Using large model - suggest smaller ones
                    helpful_msg = (
                        f"⚠️ Insufficient memory to load model '{self.model_name}'. Solutions:\n"
                        f"1. Use smaller model (recommended):\n"
                        f"   • Run: ollama pull tinyllama (smallest)\n"
                        f"   • Or: ollama pull phi3:mini\n"
                        f"   • Then update Settings to use the smaller model\n"
                        f"2. Force CPU-only mode (Windows PowerShell):\n"
                        f"   $env:OLLAMA_NUM_GPU='0'\n"
                        f"   ollama serve\n"
                        f"3. Free up system memory\n"
                        f"Original error: {error_detail}"
                    )
                print(f"[ERROR] {helpful_msg}")
                return f"Error: {helpful_msg}"
            
            error_msg = f"Ollama server error: {e.response.status_code if hasattr(e, 'response') and e.response else 'Unknown'}: {error_detail}"
            print(f"[ERROR] {error_msg}")
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Ollama API error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return f"Error: {error_msg}"
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate JSON response from prompt
        
        Args:
            prompt: User prompt (should request JSON format)
            system_prompt: Optional system prompt
            
        Returns:
            Parsed JSON response or error dict
        """
        response_text = ""
        try:
            if "JSON" not in prompt and "json" not in prompt:
                prompt += "\n\nRespond with valid JSON only."
            
            response_text = self.generate(prompt, system_prompt)
            
            # Check for errors in response
            if response_text.startswith("Error:"):
                return {"error": response_text, "raw_response": response_text}
            
            if not response_text or len(response_text.strip()) == 0:
                return {"error": "Empty response from Ollama", "raw_response": response_text}
            
            # Clean response - remove markdown code blocks
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            if not response_text:
                return {"error": "Empty response after cleaning", "raw_response": response_text}
            
            # If response doesn't start with [ or {, try to find JSON in the text
            # This handles cases where LLM adds explanatory text before JSON
            if not response_text.startswith(('[', '{')):
                # Look for first [ or { that starts valid JSON
                json_start = -1
                for i, char in enumerate(response_text):
                    if char in ['[', '{']:
                        # Check if this looks like the start of JSON (next char should be whitespace, newline, or quote/brace)
                        if i < len(response_text) - 1:
                            next_char = response_text[i+1]
                            if next_char in ['\n', '\r', '\t', ' ', '"', '{', '[']:
                                json_start = i
                                break
                
                if json_start > 0:
                    # Extract JSON part
                    response_text = response_text[json_start:]
                    print(f"[DEBUG] Extracted JSON starting at position {json_start}")
                elif json_start == -1:
                    # No JSON found, try to extract from common patterns
                    # Look for "Here are..." or similar intro text followed by JSON
                    # Try to find JSON array or object after colon or newline
                    json_match = re.search(r'[:\n]\s*(\[[\s\S]*\]|\{[\s\S]*\})', response_text)
                    if json_match:
                        response_text = json_match.group(1)
                        print(f"[DEBUG] Extracted JSON using regex pattern")
            
            # Remove JSON comments (// and /* */) that some LLMs add
            response_text = self._strip_json_comments(response_text)
            response_text = response_text.strip()
            
            # Fix invalid control characters (unescaped newlines, tabs, etc. in strings)
            # This is a common issue with LLM-generated JSON
            def fix_control_chars(text):
                """Fix unescaped control characters in JSON strings"""
                result = []
                in_string = False
                escape_next = False
                i = 0
                while i < len(text):
                    char = text[i]
                    if escape_next:
                        result.append(char)
                        escape_next = False
                    elif char == '\\':
                        result.append(char)
                        escape_next = True
                    elif char == '"':
                        in_string = not in_string
                        result.append(char)
                    elif in_string and char in ['\n', '\r', '\t']:
                        # Escape control characters in strings
                        if char == '\n':
                            result.append('\\n')
                        elif char == '\r':
                            result.append('\\r')
                        elif char == '\t':
                            result.append('\\t')
                    else:
                        result.append(char)
                    i += 1
                return ''.join(result)
            
            # Fix control characters before parsing
            response_text = fix_control_chars(response_text)
            
            # Fix percentage signs in numeric values (e.g., "score": 30% -> "score": 30)
            # This handles cases where LLMs add % to numbers in JSON values
            response_text = re.sub(r':\s*([0-9]+\.?[0-9]*)\s*%', r': \1', response_text)
            
            # Try parsing
            try:
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON parsing error: {e}")
                print(f"[DEBUG] Response text (first 500 chars): {response_text[:500]}")
                
                # Try to repair common issues
                try:
                    # First fix control characters
                    repaired = fix_control_chars(response_text)
                    
                    # Fix percentage signs in numeric values
                    repaired = re.sub(r':\s*([0-9]+\.?[0-9]*)\s*%', r': \1', repaired)
                    
                    # Fix missing opening quotes: , word" -> , "word" (most common issue)
                    repaired = re.sub(r',\s*([A-Za-z_][A-Za-z0-9_/() ]+?)"', r', "\1"', repaired)
                    # Fix missing opening quotes: [word" -> ["word"
                    repaired = re.sub(r'\[\s*([A-Za-z_][A-Za-z0-9_/() ]+?)"', r'["\1"', repaired)
                    # Fix missing opening quotes: , word, -> , "word",
                    repaired = re.sub(r',\s*([A-Za-z_][A-Za-z0-9_/() ]+?)\s*,', r', "\1",', repaired)
                    # Fix missing opening quotes at start: [word, -> ["word",
                    repaired = re.sub(r'\[\s*([A-Za-z_][A-Za-z0-9_/() ]+?)\s*,', r'["\1",', repaired)
                    # Fix missing closing quotes: , word] -> , "word"]
                    repaired = re.sub(r',\s*([A-Za-z_][A-Za-z0-9_/() ]+?)\s*\]', r', "\1"]', repaired)
                    
                    # Now apply the more comprehensive fix
                    repaired = self._fix_array_items(repaired)
                    repaired = self._strip_json_comments(repaired)
                    
                    print(f"[DEBUG] Attempting to parse repaired JSON...")
                    return json.loads(repaired)
                except Exception as repair_error:
                    print(f"[DEBUG] Repair attempt failed: {repair_error}")
                    import traceback
                    traceback.print_exc()
                    pass
                
                # Try to extract complete JSON object if response is truncated
                try:
                    # Find the last complete closing brace
                    last_brace = response_text.rfind('}')
                    if last_brace > 0:
                        # Find matching opening brace
                        first_brace = response_text.find('{')
                        if first_brace >= 0 and first_brace < last_brace:
                            potential_json = response_text[first_brace:last_brace + 1]
                            potential_json = self._strip_json_comments(potential_json)
                            
                            # Check for incomplete strings in arrays (common truncation issue)
                            # If we see an unclosed quote before the last brace, try to close it
                            lines = potential_json.split('\n')
                            fixed_lines = []
                            for i, line in enumerate(lines):
                                # Count unescaped quotes
                                quote_count = 0
                                escaped = False
                                for char in line:
                                    if escaped:
                                        escaped = False
                                        continue
                                    if char == '\\':
                                        escaped = True
                                        continue
                                    if char == '"':
                                        quote_count += 1
                                
                                # If odd number of quotes and line ends with comma or is in an array
                                if quote_count % 2 != 0 and ('[' in line or ',' in line):
                                    # Try to close the string if it looks incomplete
                                    if not line.rstrip().endswith('"') and not line.rstrip().endswith('",'):
                                        # Add closing quote and comma if needed
                                        stripped = line.rstrip()
                                        if stripped.endswith(','):
                                            line = stripped[:-1] + '",'
                                        else:
                                            line = stripped + '"'
                                fixed_lines.append(line)
                            potential_json = '\n'.join(fixed_lines)
                            
                            # Try to close any incomplete arrays/objects
                            # Count braces and brackets
                            open_braces = potential_json.count('{') - potential_json.count('}')
                            open_brackets = potential_json.count('[') - potential_json.count(']')
                            
                            # Close incomplete arrays first (remove trailing comma if present)
                            if open_brackets > 0:
                                potential_json = potential_json.rstrip().rstrip(',')
                                potential_json += ']' * open_brackets
                            
                            # Close incomplete objects
                            if open_braces > 0:
                                potential_json = potential_json.rstrip().rstrip(',')
                                potential_json += '}' * open_braces
                            
                            return json.loads(potential_json)
                except Exception as repair_error:
                    print(f"[DEBUG] Final repair attempt failed: {repair_error}")
                
                return {
                    "error": f"Failed to parse JSON response: {str(e)}",
                    "raw_response": response_text
                }
        
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return {
                "error": "Failed to parse JSON response",
                "raw_response": response_text
            }
        except Exception as e:
            print(f"Error: {e}")
            return {
                "error": str(e),
                "raw_response": response_text
            }
    
    def list_models(self) -> list:
        """List available Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            result = response.json()
            return [model['name'] for model in result.get('models', [])]
        except Exception as e:
            print(f"Error listing models: {e}")
            return []

