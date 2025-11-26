"""Settings view for LLM configuration"""

import flet as ft
from ui.styles.theme import AppTheme
from services.llm_service import LLMService
from ai.providers.ollama_provider import OllamaProvider
from core.auth import SessionManager
from config.settings import Settings

class SettingsView:
    """Application settings view"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.user_id = SessionManager.get_user_id()
        try:
            self.llm_service = LLMService.get_instance()
        except Exception as e:
            print(f"[WARNING] Could not initialize LLMService: {e}")
            self.llm_service = None
        
    def build(self) -> ft.Container:
        """Build settings view"""
        try:
            print("[INFO] Building Settings view...")
            
            # Header
            header = ft.Container(
                content=ft.Column([
                    ft.Text("⚙️ Settings", size=28, weight=ft.FontWeight.BOLD),
                    ft.Text("Configure LLM providers and application settings",
                           size=14, color="grey")
                ], spacing=8),
                padding=AppTheme.PADDING_MEDIUM
            )
            
            # LLM Provider selection
            self.provider_dropdown = ft.Dropdown(
                label="LLM Provider",
                options=[
                    ft.dropdown.Option("openai", "OpenAI"),
                    ft.dropdown.Option("anthropic", "Anthropic (Claude)"),
                    ft.dropdown.Option("bedrock", "AWS Bedrock"),
                    ft.dropdown.Option("ollama", "Ollama (Local)"),
                ],
                on_change=self._on_provider_change,
                width=300
            )
            
            # Model selection
            self.model_dropdown = ft.Dropdown(
                label="Model",
                width=300
            )
            
            # API Key
            self.api_key_field = ft.TextField(
                label="API Key",
                password=True,
                can_reveal_password=True,
                width=400
            )
            
            # Endpoint URL (for Ollama/Bedrock)
            self.endpoint_field = ft.TextField(
                label="Endpoint URL",
                width=400,
                visible=False
            )
            
            # Temperature
            self.temperature_slider = ft.Slider(
                label="Temperature",
                min=0,
                max=1,
                divisions=10,
                value=0.7,
                width=400
            )
            
            self.temperature_value = ft.Text("0.7")
            self.temperature_slider.on_change = lambda e: self._update_slider_value(
                self.temperature_value, e.control.value
            )
            
            # Max tokens
            self.max_tokens_field = ft.TextField(
                label="Max Tokens",
                value="2000",
                keyboard_type=ft.KeyboardType.NUMBER,
                width=200
            )
            
            # Save button
            self.save_button = ft.ElevatedButton(
                text="Save Settings",
                icon=ft.Icons.SAVE,
                on_click=self._on_save,
                style=ft.ButtonStyle(bgcolor=AppTheme.PRIMARY, color="white")
            )
            
            # Test connection button
            self.test_button = ft.OutlinedButton(
                text="Test Connection",
                icon=ft.Icons.CABLE,
                on_click=self._on_test_connection
            )
            
            # Status message container (visible feedback)
            self.status_icon = ft.Icon(ft.Icons.INFO, size=20, color=ft.Colors.BLUE)
            self.status_text = ft.Text("", size=14, expand=True)
            self.status_container = ft.Container(
                content=ft.Row([
                    self.status_icon,
                    self.status_text
                ], spacing=10),
                padding=12,
                border_radius=5,
                visible=False,
                bgcolor=ft.Colors.BLUE_50,
                border=ft.border.all(1, ft.Colors.BLUE_200)
            )
            
            # LLM Settings form
            llm_settings = ft.Container(
                content=ft.Column([
                    ft.Text("LLM Provider Configuration", size=20, weight=ft.FontWeight.BOLD),
                    self.provider_dropdown,
                    self.model_dropdown,
                    self.api_key_field,
                    self.endpoint_field,
                    ft.Row([
                        ft.Column([
                            ft.Text("Temperature"),
                            self.temperature_slider,
                            self.temperature_value
                        ], spacing=4),
                    ]),
                    self.max_tokens_field,
                    self.status_container,  # Add status container
                    ft.Row([
                        self.save_button,
                        self.test_button
                    ], spacing=12)
                ], spacing=16),
                **AppTheme.card_style()
            )
            
            # About section
            about_section = ft.Container(
                content=ft.Column([
                    ft.Text("About", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("Interview Prep AI v1.0", size=14),
                    ft.Text("Your AI-powered career companion", size=12, color="grey"),
                    ft.Divider(),
                    ft.Text("Supported Providers:", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text("• OpenAI (GPT-4, GPT-3.5)", size=12),
                    ft.Text("• Anthropic (Claude 3)", size=12),
                    ft.Text("• AWS Bedrock", size=12),
                    ft.Text("• Ollama (Local LLMs)", size=12),
                ], spacing=8),
                **AppTheme.card_style()
            )
            
            # Load current settings
            try:
                self._load_current_settings()
            except Exception as load_error:
                print(f"[ERROR] Error loading settings: {load_error}")
                import traceback
                traceback.print_exc()
            
            # Main content
            content = ft.Column([
                header,
                ft.Divider(),
                llm_settings,
                about_section
            ], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)
            
            print("[INFO] Settings view built successfully")
            
            return ft.Container(
                content=content,
                padding=AppTheme.PADDING_MEDIUM,
                expand=True
            )
        except Exception as e:
            print(f"[ERROR] Error building Settings view: {e}")
            import traceback
            traceback.print_exc()
            # Return error container
            return ft.Container(
                content=ft.Column([
                    ft.Text("⚙️ Settings", size=28, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Error loading settings: {str(e)}", color=ft.Colors.RED),
                    ft.Text("Please refresh the page", color="grey")
                ], spacing=16),
                padding=AppTheme.PADDING_MEDIUM,
                expand=True
            )
    
    def _on_provider_change(self, e):
        """Handle provider selection change"""
        provider = e.control.value if hasattr(e, 'control') else e
        
        if provider:
            # Clear current model selection
            self.model_dropdown.value = None
            
            # Update provider options
            self._update_provider_options(provider)
            
            # Select first option
            if self.model_dropdown.options:
                self.model_dropdown.value = self.model_dropdown.options[0].key
            
            # Clear API key and endpoint when switching providers
            self.api_key_field.value = ""
            if provider not in ['ollama', 'bedrock']:
                self.endpoint_field.value = ""
            
            self.page.update()
    
    def _update_slider_value(self, text_control, value):
        """Update slider value display"""
        text_control.value = f"{value:.1f}"
        text_control.update()
    
    def _load_current_settings(self):
        """Load current LLM settings"""
        try:
            if not self.llm_service:
                # If LLM service not available, set defaults
                self.provider_dropdown.value = "ollama"
                self._update_provider_options("ollama")
                if self.model_dropdown.options:
                    self.model_dropdown.value = self.model_dropdown.options[0].key
                return
            
            settings = self.llm_service.get_user_llm_settings(self.user_id)
            
            if settings:
                self.provider_dropdown.value = settings['provider']
                # Update model options based on provider
                self._update_provider_options(settings['provider'])
                self.model_dropdown.value = settings['model_name']
                self.temperature_slider.value = float(settings.get('temperature', 0.7))
                self.temperature_value.value = f"{self.temperature_slider.value:.1f}"
                self.max_tokens_field.value = str(settings.get('max_tokens', 2000))
                
                if settings.get('endpoint_url'):
                    self.endpoint_field.value = settings['endpoint_url']
            else:
                # Set defaults
                self.provider_dropdown.value = "ollama"  # Default to Ollama since user has it
                self._update_provider_options("ollama")
                if self.model_dropdown.options:
                    self.model_dropdown.value = self.model_dropdown.options[0].key
        except Exception as e:
            print(f"[ERROR] Error loading settings: {e}")
            import traceback
            traceback.print_exc()
            # Set safe defaults
            self.provider_dropdown.value = "ollama"
            self._update_provider_options("ollama")
    
    def _update_provider_options(self, provider: str):
        """Update model options and field visibility based on provider"""
        if provider == "openai":
            self.model_dropdown.options = [
                ft.dropdown.Option("gpt-4", "GPT-4"),
                ft.dropdown.Option("gpt-4-turbo-preview", "GPT-4 Turbo"),
                ft.dropdown.Option("gpt-3.5-turbo", "GPT-3.5 Turbo"),
            ]
            self.api_key_field.visible = True
            self.endpoint_field.visible = False
        elif provider == "anthropic":
            self.model_dropdown.options = [
                ft.dropdown.Option("claude-3-opus-20240229", "Claude 3 Opus"),
                ft.dropdown.Option("claude-3-sonnet-20240229", "Claude 3 Sonnet"),
                ft.dropdown.Option("claude-3-haiku-20240307", "Claude 3 Haiku"),
            ]
            self.api_key_field.visible = True
            self.endpoint_field.visible = False
        elif provider == "bedrock":
            self.model_dropdown.options = [
                ft.dropdown.Option("anthropic.claude-3-sonnet-20240229-v1:0", "Claude 3 Sonnet"),
                ft.dropdown.Option("anthropic.claude-v2", "Claude 2"),
                ft.dropdown.Option("amazon.titan-text-express-v1", "Titan Text Express"),
            ]
            self.api_key_field.visible = False
            self.endpoint_field.visible = True
            self.endpoint_field.label = "AWS Region"
        elif provider == "ollama":
            # Try to get available models from Ollama
            try:
                base_url = self.endpoint_field.value if self.endpoint_field.value else Settings.OLLAMA_BASE_URL
                ollama = OllamaProvider(base_url=base_url)
                models = ollama.list_models()
                if models:
                    self.model_dropdown.options = [
                        ft.dropdown.Option(m, m) for m in models
                    ]
                else:
                    # Fallback to common models
                    self.model_dropdown.options = [
                        ft.dropdown.Option("llama3.2:latest", "Llama 3.2 (Latest)"),
                        ft.dropdown.Option("llama3.2", "Llama 3.2"),
                        ft.dropdown.Option("llama3:latest", "Llama 3 (Latest)"),
                        ft.dropdown.Option("llama3", "Llama 3"),
                        ft.dropdown.Option("mistral", "Mistral"),
                    ]
            except Exception as ex:
                print(f"[WARNING] Could not fetch Ollama models: {ex}")
                # Fallback to common models
                self.model_dropdown.options = [
                    ft.dropdown.Option("llama3.2:latest", "Llama 3.2 (Latest)"),
                    ft.dropdown.Option("llama3.2", "Llama 3.2"),
                    ft.dropdown.Option("llama3:latest", "Llama 3 (Latest)"),
                    ft.dropdown.Option("llama3", "Llama 3"),
                    ft.dropdown.Option("mistral", "Mistral"),
                ]
            self.api_key_field.visible = False
            self.endpoint_field.visible = True
            self.endpoint_field.label = "Ollama URL"
            if not self.endpoint_field.value:
                self.endpoint_field.value = Settings.OLLAMA_BASE_URL
    
    def _on_save(self, e):
        """Save LLM settings"""
        provider = self.provider_dropdown.value
        model = self.model_dropdown.value
        api_key = self.api_key_field.value.strip() if self.api_key_field.visible and self.api_key_field.value else None
        endpoint = self.endpoint_field.value.strip() if self.endpoint_field.visible and self.endpoint_field.value else None
        temperature = self.temperature_slider.value
        max_tokens = int(self.max_tokens_field.value) if self.max_tokens_field.value else 2000
        
        # Validation
        if not provider or not model:
            self._show_error("Please select provider and model")
            return
        
        # Validate API key for providers that require it
        if provider in ['openai', 'anthropic']:
            if not api_key:
                self._show_error(f"API key is required for {provider.title()}")
                return
        
        # Validate endpoint URL for Ollama/Bedrock
        if provider in ['ollama', 'bedrock']:
            if not endpoint:
                self._show_error(f"Endpoint URL is required for {provider.title()}")
                return
            # Basic URL validation
            if not (endpoint.startswith('http://') or endpoint.startswith('https://')):
                self._show_error("Endpoint URL must start with http:// or https://")
                return
        
        print(f"[INFO] Saving LLM settings: provider={provider}, model={model}")
        
        success = self.llm_service.save_llm_settings(
            self.user_id,
            provider,
            model,
            api_key,
            endpoint,
            temperature,
            max_tokens
        )
        
        print(f"[INFO] Save result: {success}")
        
        if success:
            self._show_success("✅ Settings saved successfully!")
            print("[INFO] Success snackbar shown")
        else:
            self._show_error("❌ Error saving settings. Please try again.")
            print("[INFO] Error snackbar shown")
    
    def _on_test_connection(self, e):
        """Test LLM connection using form values"""
        self.test_button.disabled = True
        self.test_button.text = "Testing..."
        self.page.update()
        
        try:
            # Get values from form (not saved settings)
            provider = self.provider_dropdown.value
            model = self.model_dropdown.value
            api_key = self.api_key_field.value.strip() if self.api_key_field.visible and self.api_key_field.value else None
            endpoint = self.endpoint_field.value.strip() if self.endpoint_field.visible and self.endpoint_field.value else None
            temperature = self.temperature_slider.value
            max_tokens = int(self.max_tokens_field.value) if self.max_tokens_field.value else 2000
            
            # Validation
            if not provider or not model:
                self._show_error("Please select provider and model first")
                self.test_button.text = "Test Connection"
                self.test_button.disabled = False
                self.page.update()
                return
            
            if provider in ['openai', 'anthropic'] and not api_key:
                self._show_error(f"API key is required for {provider.title()}")
                self.test_button.text = "Test Connection"
                self.test_button.disabled = False
                self.page.update()
                return
            
            if provider in ['ollama', 'bedrock'] and not endpoint:
                self._show_error(f"Endpoint URL is required for {provider.title()}")
                self.test_button.text = "Test Connection"
                self.test_button.disabled = False
                self.page.update()
                return
            
            # Create provider instance with form values
            from ai.providers import OpenAIProvider, AnthropicProvider, BedrockProvider, OllamaProvider
            
            if provider == 'openai':
                test_provider = OpenAIProvider(
                    api_key=api_key,
                    model_name=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            elif provider == 'anthropic':
                test_provider = AnthropicProvider(
                    api_key=api_key,
                    model_name=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            elif provider == 'bedrock':
                # Extract region from endpoint or use default
                region = endpoint if endpoint else 'us-east-1'
                test_provider = BedrockProvider(
                    model_name=model,
                    region_name=region,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            elif provider == 'ollama':
                # For Ollama, first test if server is reachable
                try:
                    import requests
                    test_url = f"{endpoint.rstrip('/')}/api/tags"
                    print(f"[DEBUG] Testing Ollama server connection: {test_url}")
                    server_response = requests.get(test_url, timeout=5)
                    if server_response.status_code != 200:
                        self._show_error(f"❌ Ollama server returned {server_response.status_code}. Please check if Ollama is running.")
                        self.test_button.text = "Test Connection"
                        self.test_button.disabled = False
                        self.page.update()
                        return
                    
                    # Check if model exists
                    available_models = server_response.json().get('models', [])
                    model_names = [m.get('name', '') for m in available_models]
                    
                    # Try to match model (with or without :latest)
                    model_found = False
                    actual_model = None
                    # Normalize model name (remove :latest for comparison)
                    model_base = model.replace(':latest', '')
                    
                    for m in model_names:
                        m_base = m.replace(':latest', '')
                        # Match if base names are the same
                        if m_base == model_base or m == model or model == m:
                            model_found = True
                            # Use the actual model name from server
                            actual_model = m
                            print(f"[DEBUG] Model matched: requested='{model}', found='{m}', using='{actual_model}'")
                            break
                    
                    if not model_found and model_names:
                        # Model not found, suggest available models
                        suggestions = ', '.join(model_names[:3])
                        self._show_error(f"❌ Model '{model}' not found. Available models: {suggestions}")
                        self.test_button.text = "Test Connection"
                        self.test_button.disabled = False
                        self.page.update()
                        return
                    elif not model_found:
                        # No models available
                        self._show_error("❌ No models found in Ollama. Please pull a model first (e.g., 'ollama pull llama3.2')")
                        self.test_button.text = "Test Connection"
                        self.test_button.disabled = False
                        self.page.update()
                        return
                    
                    # Use actual model name from server
                    test_model = actual_model if actual_model else model
                    print(f"[DEBUG] Using model: {test_model} (requested: {model})")
                    
                except requests.exceptions.ConnectionError:
                    self._show_error(f"❌ Cannot connect to Ollama server at {endpoint}. Please check if Ollama is running.")
                    self.test_button.text = "Test Connection"
                    self.test_button.disabled = False
                    self.page.update()
                    return
                except Exception as e:
                    print(f"[WARNING] Could not verify model, proceeding with test: {e}")
                    test_model = model
                
                test_provider = OllamaProvider(
                    model_name=test_model,
                    base_url=endpoint,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                self._show_error(f"Unknown provider: {provider}")
                self.test_button.text = "Test Connection"
                self.test_button.disabled = False
                self.page.update()
                return
            
            # Test connection with a simple prompt (same as coach service uses)
            test_model_name = test_model if provider == 'ollama' and 'test_model' in locals() else model
            print(f"[DEBUG] Testing connection: provider={provider}, model={test_model_name}")
            # Use same simple prompt format that works in coach service
            test_prompt = "Hello"
            response = test_provider.generate(test_prompt, system_prompt=None)
            
            print(f"[DEBUG] Test response received: {response[:200] if response else 'None'}")
            
            # Re-enable button before checking response
            self.test_button.text = "Test Connection"
            self.test_button.disabled = False
            
            # Check if response contains error indicators
            if not response:
                self._show_error("❌ No response received from provider")
                self.page.update()
                print(f"[DEBUG] Test connection failed: No response")
            elif "error" in response.lower() or "Error:" in response:
                # Extract error message
                error_msg = response
                if "Ollama server error: 500" in error_msg:
                    self._show_error("❌ Ollama server error (500). Please check if Ollama server is running.")
                elif "500" in error_msg:
                    self._show_error("❌ Server error (500). Please check if the service is running.")
                elif "401" in error_msg or "unauthorized" in error_msg.lower():
                    self._show_error("❌ Authentication failed. Please check your API key.")
                elif "404" in error_msg or "not found" in error_msg.lower():
                    self._show_error(f"❌ Model '{model}' not found. Please check the model name.")
                else:
                    # Show first 100 chars of error
                    error_display = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
                    self._show_error(f"❌ Connection failed: {error_display}")
                self.page.update()
                print(f"[DEBUG] Test connection failed: {error_msg}")
            else:
                # Re-enable button first (before showing dialog)
                self.test_button.text = "Test Connection"
                self.test_button.disabled = False
                
                # Show success message (this will update the page with dialog)
                self._show_success("✅ Connection successful! Provider is working correctly.")
                print(f"[DEBUG] Test connection successful: {response[:50]}")
                
        except Exception as ex:
            error_msg = str(ex)
            print(f"[ERROR] Test connection error: {ex}")
            import traceback
            traceback.print_exc()
            
            # Provide user-friendly error messages
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                self._show_error("❌ Authentication failed. Please check your API key.")
            elif "404" in error_msg or "not found" in error_msg.lower():
                self._show_error(f"❌ Model '{model}' not found. Please check the model name.")
            elif "500" in error_msg or "server error" in error_msg.lower():
                self._show_error("❌ Server error. Please check if the service is running (e.g., Ollama server).")
            elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                self._show_error("❌ Connection failed. Please check your network and endpoint URL.")
            else:
                self._show_error(f"❌ Error: {error_msg[:100]}")
        
        finally:
            self.test_button.text = "Test Connection"
            self.test_button.disabled = False
            self.page.update()
    
    def _show_error(self, message: str):
        """Show error message in UI - use dialog as primary method"""
        try:
            print(f"[DEBUG] Showing error message: {message}")
            
            # Primary: Show error dialog (always visible)
            error_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED, size=32),
                    ft.Text("Error", size=18, weight=ft.FontWeight.BOLD)
                ], spacing=10),
                content=ft.Text(message, size=14),
                actions=[
                    ft.ElevatedButton("OK", on_click=lambda _: self._close_error_dialog(error_dialog))
                ],
                modal=True
            )
            self.page.dialog = error_dialog
            error_dialog.open = True
            self.page.update()
            print(f"[DEBUG] Error dialog opened")
            
            # Secondary: Update status container if it exists
            if hasattr(self, 'status_container') and hasattr(self, 'status_text'):
                try:
                    self.status_text.value = message
                    self.status_text.color = ft.Colors.RED
                    self.status_icon.name = ft.Icons.ERROR
                    self.status_icon.color = ft.Colors.RED
                    self.status_container.bgcolor = ft.Colors.RED_50
                    self.status_container.border = ft.border.all(1, ft.Colors.RED_200)
                    self.status_container.visible = True
                    self.status_text.update()
                    self.status_icon.update()
                    self.status_container.update()
                except:
                    pass
            
            # Tertiary: Try snackbar
            try:
                snackbar = ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=ft.Colors.RED,
                    duration=5000
                )
                self.page.snack_bar = snackbar
                self.page.snack_bar.open = True
            except:
                pass
            
            self.page.update()
        except Exception as ex:
            print(f"[ERROR] Failed to show error message: {ex}")
            import traceback
            traceback.print_exc()
    
    def _close_error_dialog(self, dialog: ft.AlertDialog):
        """Close error dialog"""
        dialog.open = False
        self.page.dialog = None
        self.page.update()
    
    def _show_success(self, message: str):
        """Show success message in UI - use dialog as primary method"""
        try:
            print(f"[DEBUG] Showing success message: {message}")
            
            # Primary: Show success dialog (always visible)
            success_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=32),
                    ft.Text("Success", size=18, weight=ft.FontWeight.BOLD)
                ], spacing=10),
                content=ft.Text(message, size=14),
                actions=[
                    ft.ElevatedButton("OK", on_click=lambda _: self._close_success_dialog(success_dialog))
                ],
                modal=True
            )
            # Check if page is still valid
            if not hasattr(self, 'page') or self.page is None:
                print("[WARNING] Page is not available, skipping success message")
                return
            
            # Set dialog and open it
            self.page.dialog = success_dialog
            success_dialog.open = True
            print(f"[DEBUG] Success dialog opened")
            
            # Safely update page - use try/except to handle event loop issues
            try:
                if hasattr(self.page, 'update'):
                    self.page.update()
                    print(f"[DEBUG] Page updated after showing success dialog")
            except RuntimeError as e:
                if "Event loop is closed" in str(e):
                    print("[WARNING] Event loop is closed, but dialog should still be visible")
                    # Dialog is already set, so it should appear on next interaction
                else:
                    print(f"[WARNING] Error updating page: {e}")
            except Exception as e:
                print(f"[WARNING] Unexpected error updating page: {e}")
            
            # Secondary: Update status container if it exists
            if hasattr(self, 'status_container') and hasattr(self, 'status_text'):
                try:
                    self.status_text.value = message
                    self.status_text.color = ft.Colors.GREEN
                    self.status_icon.name = ft.Icons.CHECK_CIRCLE
                    self.status_icon.color = ft.Colors.GREEN
                    self.status_container.bgcolor = ft.Colors.GREEN_50
                    self.status_container.border = ft.border.all(1, ft.Colors.GREEN_200)
                    self.status_container.visible = True
                    self.status_text.update()
                    self.status_icon.update()
                    self.status_container.update()
                except:
                    pass
            
            # Tertiary: Try snackbar
            try:
                snackbar = ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=ft.Colors.GREEN,
                    duration=3000
                )
                self.page.snack_bar = snackbar
                self.page.snack_bar.open = True
            except:
                pass
        except Exception as ex:
            print(f"[ERROR] Failed to show success message: {ex}")
            import traceback
            traceback.print_exc()
    
    def _close_success_dialog(self, dialog: ft.AlertDialog):
        """Close success dialog"""
        dialog.open = False
        self.page.dialog = None
        self.page.update()
