
import tkinter as tk
from tkinter import ttk, scrolledtext, font
import os
from PIL import Image, ImageTk

class ModernChatInterface:
    def __init__(self, root, callback_functions=None):
        self.root = root
        self.callback_functions = callback_functions or {}
        
        # Configure the root window
        self.root.title("Protype.AI - Modern Interface")
        self.root.geometry("1000x700")
        
        # Check for dark mode preference (could be stored in a config file)
        self.dark_mode = True
        
        # Set color scheme based on mode
        self.setup_theme()
        
        # Create custom fonts
        self.setup_fonts()
        
        # Create main frame
        self.main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create sidebar (collapsible)
        self.setup_sidebar()
        
        # Create chat area
        self.setup_chat_area()
        
        # Create input area
        self.setup_input_area()
        
    def setup_theme(self):
        """Set up color scheme based on dark/light mode"""
        if self.dark_mode:
            self.colors = {
                "bg": "#1F2A44",  # Dark background
                "sidebar_bg": "#172035",  # Darker sidebar
                "user_bubble": "#3B82F6",  # Blue for user messages
                "ai_bubble": "#374151",  # Darker gray for AI
                "user_text": "#FFFFFF",  # White text for user
                "ai_text": "#F3F4F6",  # Light gray text for AI
                "input_bg": "#374151",  # Input background
                "input_text": "#FFFFFF",  # Input text
                "button": "#3B82F6",  # Button color
                "button_hover": "#2563EB",  # Button hover
                "divider": "#374151"  # Divider color
            }
        else:
            self.colors = {
                "bg": "#F7F7F8",  # Light background
                "sidebar_bg": "#EAEAEB",  # Light sidebar
                "user_bubble": "#DCF8C6",  # Green for user messages
                "ai_bubble": "#FFFFFF",  # White for AI messages
                "user_text": "#000000",  # Black text for user
                "ai_text": "#000000",  # Black text for AI
                "input_bg": "#FFFFFF",  # Input background
                "input_text": "#000000",  # Input text
                "button": "#0088CC",  # Button color
                "button_hover": "#006699",  # Button hover
                "divider": "#EAEAEB"  # Divider color
            }
    
    def setup_fonts(self):
        """Set up fonts for the interface"""
        # Try to use modern fonts if available
        available_fonts = font.families()
        
        body_font = "Roboto"
        if body_font not in available_fonts:
            body_font = "Segoe UI" if "Segoe UI" in available_fonts else "Arial"
            
        self.fonts = {
            "title": (body_font, 16, "bold"),
            "message": (body_font, 11),
            "message_bold": (body_font, 11, "bold"),
            "input": (body_font, 12)
        }
    
    def setup_sidebar(self):
        """Set up the collapsible sidebar"""
        # Sidebar container
        self.sidebar_frame = tk.Frame(self.main_frame, bg=self.colors["sidebar_bg"], width=50)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)
        
        # Sidebar is collapsed by default
        self.sidebar_expanded = False
        
        # Create toggle button for sidebar
        self.toggle_btn = tk.Button(self.sidebar_frame, text="☰", bg=self.colors["sidebar_bg"],
                                    fg=self.colors["ai_text"], font=self.fonts["title"],
                                    relief=tk.FLAT, command=self.toggle_sidebar)
        self.toggle_btn.pack(pady=10)
        
        # Create sidebar content (hidden initially)
        self.sidebar_content = tk.Frame(self.sidebar_frame, bg=self.colors["sidebar_bg"])
        
        # Add buttons to the sidebar
        sidebar_buttons = [
            ("💬 Chat", self.show_chat),
            ("📊 Dashboard", self.show_dashboard),
            ("⚙️ Settings", self.show_settings),
            ("🌓 Toggle Theme", self.toggle_theme)
        ]
        
        for text, command in sidebar_buttons:
            btn = tk.Button(self.sidebar_content, text=text, bg=self.colors["sidebar_bg"],
                           fg=self.colors["ai_text"], font=self.fonts["message"],
                           relief=tk.FLAT, anchor="w", command=command)
            btn.pack(fill=tk.X, padx=10, pady=5)
    
    def setup_chat_area(self):
        """Set up the main chat area"""
        # Chat container (takes 90% of the screen)
        self.chat_container = tk.Frame(self.main_frame, bg=self.colors["bg"])
        self.chat_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Chat display area with scrolling
        self.chat_display = scrolledtext.ScrolledText(self.chat_container, bg=self.colors["bg"],
                                                    fg=self.colors["ai_text"], font=self.fonts["message"],
                                                    wrap=tk.WORD, relief=tk.FLAT)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.chat_display.tag_configure("user", background=self.colors["user_bubble"], 
                                       foreground=self.colors["user_text"], lmargin1=20, lmargin2=20, rmargin=20)
        self.chat_display.tag_configure("ai", background=self.colors["ai_bubble"],
                                      foreground=self.colors["ai_text"], lmargin1=20, lmargin2=20, rmargin=20)
        self.chat_display.tag_configure("user_label", foreground=self.colors["user_bubble"], 
                                       font=self.fonts["message_bold"])
        self.chat_display.tag_configure("ai_label", foreground=self.colors["ai_bubble"],
                                      font=self.fonts["message_bold"])
        
        self.chat_display.config(state=tk.DISABLED)  # Make it read-only
        
        # Add welcome message
        self.add_message("Protype.AI", "Hello! I'm Protype.AI, ready to help. Ask me anything!", "ai")
    
    def setup_input_area(self):
        """Set up the input area at the bottom"""
        # Input container
        self.input_container = tk.Frame(self.main_frame, bg=self.colors["bg"], height=80)
        self.input_container.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # Text input field
        self.input_frame = tk.Frame(self.input_container, bg=self.colors["input_bg"],
                                   bd=1, relief=tk.SOLID, padx=10, pady=10)
        self.input_frame.pack(fill=tk.X, padx=20, side=tk.LEFT, expand=True)
        
        self.input_field = tk.Text(self.input_frame, bg=self.colors["input_bg"],
                                  fg=self.colors["input_text"], font=self.fonts["input"],
                                  height=2, relief=tk.FLAT, wrap=tk.WORD)
        self.input_field.pack(fill=tk.X, expand=True)
        self.input_field.bind("<Return>", self.on_enter_pressed)
        
        # Send button
        self.send_button = tk.Button(self.input_container, text="Send", bg=self.colors["button"],
                                    fg=self.colors["user_text"], font=self.fonts["message_bold"],
                                    relief=tk.FLAT, command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=20)
    
    def toggle_sidebar(self):
        """Toggle sidebar expansion"""
        if self.sidebar_expanded:
            # Collapse sidebar
            self.sidebar_content.pack_forget()
            self.sidebar_frame.config(width=50)
            self.sidebar_expanded = False
        else:
            # Expand sidebar
            self.sidebar_frame.config(width=200)
            self.sidebar_content.pack(fill=tk.BOTH, expand=True)
            self.sidebar_expanded = True
    
    def show_chat(self):
        """Switch to chat view"""
        print("Switching to chat view")
        # This is already the default view
    
    def show_dashboard(self):
        """Switch to dashboard view"""
        print("Switching to dashboard view")
        if 'show_dashboard' in self.callback_functions:
            self.callback_functions['show_dashboard']()
    
    def show_settings(self):
        """Show settings"""
        print("Showing settings")
        if 'show_settings' in self.callback_functions:
            self.callback_functions['show_settings']()
    
    def toggle_theme(self):
        """Toggle between light and dark mode"""
        self.dark_mode = not self.dark_mode
        self.setup_theme()
        
        # Update UI elements with new colors
        self.main_frame.config(bg=self.colors["bg"])
        self.sidebar_frame.config(bg=self.colors["sidebar_bg"])
        self.toggle_btn.config(bg=self.colors["sidebar_bg"], fg=self.colors["ai_text"])
        self.sidebar_content.config(bg=self.colors["sidebar_bg"])
        
        # Update all buttons in sidebar
        for child in self.sidebar_content.winfo_children():
            if isinstance(child, tk.Button):
                child.config(bg=self.colors["sidebar_bg"], fg=self.colors["ai_text"])
        
        # Update chat area
        self.chat_container.config(bg=self.colors["bg"])
        self.chat_display.config(bg=self.colors["bg"], fg=self.colors["ai_text"])
        
        # Update tags
        self.chat_display.tag_configure("user", background=self.colors["user_bubble"], 
                                      foreground=self.colors["user_text"])
        self.chat_display.tag_configure("ai", background=self.colors["ai_bubble"],
                                     foreground=self.colors["ai_text"])
        
        # Update input area
        self.input_container.config(bg=self.colors["bg"])
        self.input_frame.config(bg=self.colors["input_bg"])
        self.input_field.config(bg=self.colors["input_bg"], fg=self.colors["input_text"])
        self.send_button.config(bg=self.colors["button"], fg=self.colors["user_text"])
    
    def add_message(self, sender, message, message_type):
        """Add a new message to the chat"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add sender label
        if self.chat_display.index("end-1c") != "1.0":
            self.chat_display.insert(tk.END, "\n\n")
        
        sender_tag = f"{message_type}_label"
        self.chat_display.insert(tk.END, f"{sender}:\n", sender_tag)
        
        # Add message with appropriate styling
        self.chat_display.insert(tk.END, f"{message}\n", message_type)
        
        # Scroll to the bottom
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def on_enter_pressed(self, event):
        """Handle Enter key in the input field"""
        # Don't add a newline
        if not event.state & 0x4:  # Check if Shift is not pressed
            self.send_message()
            return "break"  # Prevents the default behavior
        return None
    
    def send_message(self):
        """Send message when button is clicked or Enter is pressed"""
        message = self.input_field.get("1.0", tk.END).strip()
        if not message:
            return
        
        # Clear input field
        self.input_field.delete("1.0", tk.END)
        
        # Add user message to chat
        self.add_message("You", message, "user")
        
        # Process message (this would call your AI logic)
        if 'process_message' in self.callback_functions:
            self.callback_functions['process_message'](message)
        else:
            # Default response if no callback provided
            self.add_message("Protype.AI", "I received your message. This is a placeholder response.", "ai")

# For testing the interface independently
if __name__ == "__main__":
    root = tk.Tk()
    app = ModernChatInterface(root)
    root.mainloop()
