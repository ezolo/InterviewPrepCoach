"""File upload component"""

import flet as ft
import os
from typing import Callable, List, Optional

class FileUploadComponent:
    """Reusable file upload component"""
    
    def __init__(self, label: str, allowed_extensions: List[str],
                 on_file_selected: Callable, help_text: Optional[str] = None):
        """
        Args:
            label: Label for the upload button
            allowed_extensions: List of allowed file extensions (e.g., ['.pdf', '.docx'])
            on_file_selected: Callback when file is selected (receives file_path, file_name)
            help_text: Optional help text to display
        """
        self.label = label
        self.allowed_extensions = allowed_extensions
        self.on_file_selected = on_file_selected
        self.help_text = help_text
        self.selected_file = None
        self.file_picker = None
        self.status_text = None
        self._page = None
        
    def build(self, page: ft.Page = None) -> ft.Container:
        """Build file upload UI"""
        # Store page reference
        self._page = page
        
        # Create file picker (desktop mode)
        # IMPORTANT: We'll set file_type when calling pick_files to show files
        self.file_picker = ft.FilePicker(
            on_result=self._on_file_pick_result
        )
        
        # Add file picker to page overlay if page is provided
        # This MUST be done before using the file picker
        if page:
            if self.file_picker not in page.overlay:
                page.overlay.append(self.file_picker)
                # Update page to ensure file picker is registered
                page.update()
        
        # Create status text
        self.status_text = ft.Text("No file selected", size=12, color="grey")
        
        # Create upload button
        upload_button = ft.ElevatedButton(
            text=self.label,
            icon=ft.Icons.UPLOAD_FILE,
            on_click=self._on_upload_click,
            style=ft.ButtonStyle(
                padding=15
            )
        )
        
        # Build content
        content_controls = []
        
        if self.help_text:
            content_controls.append(
                ft.Text(self.help_text, size=12, color="grey600")
            )
        
        content_controls.extend([
            upload_button,
            self.status_text
        ])
        
        content = ft.Column(content_controls, spacing=8)
        
        return ft.Container(
            content=content,
            padding=15
        )
    
    
    def _on_file_pick_result(self, e: ft.FilePickerResultEvent):
        """Handle file picker result"""
        print(f"[DEBUG] File picker result event received")
        print(f"[DEBUG] Result path: {e.path}")
        print(f"[DEBUG] Result files: {e.files}")
        print(f"[DEBUG] Result data: {e.data}")
        
        # Check if files were selected
        if e.files and len(e.files) > 0:
            file = e.files[0]
            file_name = getattr(file, 'name', None) or "Unknown"
            file_path = getattr(file, 'path', None) or e.path
            
            print(f"[DEBUG] Selected file - name: {file_name}, path: {file_path}")
            
            # Try to get path from different sources
            if not file_path:
                # Try accessing file object attributes
                if hasattr(file, 'path'):
                    file_path = file.path
                elif hasattr(file, 'name'):
                    # In some cases, we might need to construct path
                    file_path = None
            
            # If we have a file path, validate and use it
            if file_path and os.path.exists(file_path):
                # Validate file extension only if allowed_extensions is specified and not empty
                if self.allowed_extensions and len(self.allowed_extensions) > 0:
                    file_ext = os.path.splitext(file_name)[1].lower()
                    if file_ext not in [ext.lower() for ext in self.allowed_extensions]:
                        print(f"[WARNING] File extension {file_ext} not in allowed extensions")
                        if self.status_text and self._page:
                            try:
                                allowed = ", ".join(self.allowed_extensions)
                                self.status_text.value = f"[ERROR] Invalid file type. Allowed: {allowed}"
                                self.status_text.color = "red"
                                self.status_text.update()
                            except AssertionError:
                                # Status text not on page
                                pass
                        return
                
                print(f"[DEBUG] [OK] File found at: {file_path}")
                self.selected_file = file_path
                if self.status_text and self._page:
                    try:
                        self.status_text.value = f"[OK] Selected: {file_name}"
                        self.status_text.color = "green"
                        self.status_text.update()
                    except AssertionError:
                        # Status text not on page (e.g., in coach view attachment)
                        pass
                
                # Call the callback
                if self.on_file_selected:
                    try:
                        self.on_file_selected(file_path, file_name)
                    except Exception as ex:
                        print(f"[ERROR] Error in file selection callback: {ex}")
                        import traceback
                        traceback.print_exc()
                        if self.status_text and self._page:
                            try:
                                self.status_text.value = f"[ERROR] Error: {str(ex)}"
                                self.status_text.color = "red"
                                self.status_text.update()
                            except AssertionError:
                                # Status text not on page
                                pass
            elif file_path:
                # Path provided but file doesn't exist
                print(f"[WARNING] File path provided but file doesn't exist: {file_path}")
                if self.status_text and self._page:
                    try:
                        self.status_text.value = f"[ERROR] File not found at path"
                        self.status_text.color = "red"
                        self.status_text.update()
                    except AssertionError:
                        pass
            else:
                # No file path available
                print(f"[WARNING] No file path available")
                if self.status_text and self._page:
                    try:
                        self.status_text.value = f"[ERROR] Could not get file path"
                        self.status_text.color = "red"
                        self.status_text.update()
                    except AssertionError:
                        pass
        elif e.path:
            # Sometimes Flet provides path directly
            print(f"[DEBUG] Using path directly from result: {e.path}")
            if os.path.exists(e.path):
                file_name = os.path.basename(e.path)
                
                # Validate file extension
                file_ext = os.path.splitext(file_name)[1].lower()
                if self.allowed_extensions and file_ext not in [ext.lower() for ext in self.allowed_extensions]:
                    print(f"[WARNING] File extension {file_ext} not in allowed extensions")
                    if self.status_text:
                        allowed = ", ".join(self.allowed_extensions)
                        self.status_text.value = f"[ERROR] Invalid file type. Allowed: {allowed}"
                        self.status_text.color = "red"
                        self.status_text.update()
                    return
                
                self.selected_file = e.path
                if self.status_text:
                    self.status_text.value = f"[OK] Selected: {file_name}"
                    self.status_text.color = "green"
                    self.status_text.update()
                
                if self.on_file_selected:
                    try:
                        self.on_file_selected(e.path, file_name)
                    except Exception as ex:
                        print(f"[ERROR] Error in callback: {ex}")
                        import traceback
                        traceback.print_exc()
        else:
            # User cancelled or no file selected
            print("[DEBUG] No file selected (user cancelled or dialog closed)")
            self.selected_file = None
            if self.status_text:
                self.status_text.value = "No file selected"
                self.status_text.color = "grey"
                self.status_text.update()
    
    
    def _on_upload_click(self, e):
        """Handle upload button click"""
        print(f"[DEBUG] Upload button clicked")
        
        if not self.file_picker:
            print("[ERROR] File picker not initialized")
            if self.status_text:
                self.status_text.value = "[ERROR] File picker not ready"
                self.status_text.color = "red"
                self.status_text.update()
            return
        
        # Ensure file picker is in page overlay and page is updated
        if self._page:
            if self.file_picker not in self._page.overlay:
                print("[DEBUG] Adding file picker to overlay")
                self._page.overlay.append(self.file_picker)
            
            # Update page to ensure file picker is ready
            self._page.update()
        
        try:
            print(f"[DEBUG] Opening file picker with extensions: {self.allowed_extensions}")
            
            # Convert extensions - remove leading dots
            dialog_extensions = [ext.lstrip('.') for ext in self.allowed_extensions] if self.allowed_extensions else None
            
            # CRITICAL: Pass file_type=ANY to pick_files() to show FILES, not folders
            # Without this, Windows might show only folders
            if dialog_extensions:
                # Show files with extension filter
                self.file_picker.pick_files(
                    file_type=ft.FilePickerFileType.CUSTOM,
                    allowed_extensions=dialog_extensions,
                    allow_multiple=False
                )
            else:
                # Show ALL files (any type)
                self.file_picker.pick_files(
                    file_type=ft.FilePickerFileType.ANY,
                    allow_multiple=False
                )
            
            print("[DEBUG] File picker pick_files() called successfully")
        except Exception as ex:
            print(f"[ERROR] Failed to open file picker: {ex}")
            import traceback
            traceback.print_exc()
            if self.status_text:
                self.status_text.value = f"❌ Error: {str(ex)}"
                self.status_text.color = "red"
                self.status_text.update()
    
    def get_file_picker(self):
        """Get the file picker control"""
        return self.file_picker
    
    def add_to_page(self, page: ft.Page):
        """Add file picker to page overlay"""
        self._page = page
        if self.file_picker and self.file_picker not in page.overlay:
            page.overlay.append(self.file_picker)
            page.update()
