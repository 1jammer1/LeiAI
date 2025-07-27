import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
from time import sleep
import threading

# Conditional imports with fallback handling
try:
    import pyautogui
    from pyopengltk import OpenGLFrame as RealOpenGLFrame
    import live2d.v2 as live2d
    # import live2d.v3 as live2d  # Uncomment for v3 models
    LIVE2D_AVAILABLE = True
    OPENGL_AVAILABLE = True
except ImportError as e:
    LIVE2D_AVAILABLE = False
    OPENGL_AVAILABLE = False
    print(f"Warning: Live2D dependencies not found: {e}")
    print("Please install with: pip install pyopengltk pyautogui live2d")
    
    # Create fallback base class when OpenGLFrame is not available
    class RealOpenGLFrame:
        def __init__(self, master, **kw):
            self.master = master
            self.width = kw.get('width', 400)
            self.height = kw.get('height', 300)
        
        def pack(self, **kw):
            pass
        
        def bind(self, event, callback):
            pass
        
        def winfo_rootx(self):
            return 0
        
        def winfo_rooty(self):
            return 0

class Live2DOpenGLFrame:
    """OpenGL Frame for Live2D model rendering with fallback support"""
    
    def __init__(self, master, **kw):
        # Set fallback status first, before calling parent __init__
        self.is_fallback = not OPENGL_AVAILABLE
        self.model = None
        self.model_path = None
        self.is_initialized = False
        self.width = kw.get('width', 400)
        self.height = kw.get('height', 300)
        self.master = master
        
        if self.is_fallback:
            # Create fallback canvas when OpenGL is not available
            self.fallback_canvas = tk.Canvas(
                master,
                bg='#1e1e1e',
                highlightthickness=0,
                width=self.width,
                height=self.height
            )
            self.show_fallback_message()
        else:
            # Initialize the real OpenGL frame
            self.opengl_frame = RealOpenGLFrame(master, **kw)
        
    def pack(self, **kw):
        if self.is_fallback:
            self.fallback_canvas.pack(**kw)
        else:
            self.opengl_frame.pack(**kw)
    
    def bind(self, event, callback):
        if self.is_fallback:
            self.fallback_canvas.bind(event, callback)
        else:
            self.opengl_frame.bind(event, callback)
    
    def winfo_rootx(self):
        if self.is_fallback:
            return self.fallback_canvas.winfo_rootx() if hasattr(self.fallback_canvas, 'winfo_rootx') else 0
        else:
            return self.opengl_frame.winfo_rootx()
    
    def winfo_rooty(self):
        if self.is_fallback:
            return self.fallback_canvas.winfo_rooty() if hasattr(self.fallback_canvas, 'winfo_rooty') else 0
        else:
            return self.opengl_frame.winfo_rooty()
    
    def show_fallback_message(self):
        """Show fallback message when OpenGL is not available"""
        if hasattr(self, 'fallback_canvas'):
            self.fallback_canvas.create_text(
                self.width // 2, self.height // 2,
                text="Live2D Dependencies Missing\n\n" +
                     "Required packages:\n" +
                     "• pip install pyopengltk\n" +
                     "• pip install pyautogui\n" +
                     "• pip install live2d\n\n" +
                     "The text input below still works!",
                fill='#ff6b6b',
                font=('Arial', 11, 'bold'),
                justify=tk.CENTER
            )
            
            # Add decorative border
            self.fallback_canvas.create_rectangle(
                10, 10, self.width - 10, self.height - 10,
                outline='#ff6b6b', width=2
            )
        
    def initgl(self):
        """Initialize OpenGL states when the frame is created"""
        if not LIVE2D_AVAILABLE or self.is_fallback:
            return
            
        try:
            # Clean up previous model if exists
            if self.model:
                del self.model
            live2d.dispose()

            # Initialize Live2D
            live2d.init()
            live2d.glewInit()
            
            self.is_initialized = True
            
            # Load model if path is set
            if self.model_path and os.path.exists(self.model_path):
                self.load_model(self.model_path)
                
        except Exception as e:
            print(f"OpenGL initialization error: {e}")
            self.is_initialized = False

    def load_model(self, model_path):
        """Load a Live2D model"""
        if self.is_fallback:
            return False
            
        if not self.is_initialized:
            self.model_path = model_path
            return False
            
        try:
            self.model = live2d.LAppModel()
            self.model.LoadModelJson(model_path)
            self.model.Resize(self.width, self.height)
            self.model_path = model_path
            return True
        except Exception as e:
            print(f"Model loading error: {e}")
            return False

    def redraw(self):
        """Render a single frame"""
        if self.is_fallback or not self.is_initialized or not self.model:
            return
            
        try:
            live2d.clearBuffer()

            # Get mouse position relative to this frame
            try:
                screen_x, screen_y = pyautogui.position()
                x = screen_x - self.winfo_rootx()
                y = screen_y - self.winfo_rooty()
            except:
                x, y = 0, 0

            self.model.Update()
            self.model.Drag(x, y)
            self.model.Draw()
            
            # Control frame rate
            sleep(1 / 60)
            
        except Exception as e:
            print(f"Rendering error: {e}")

    def start_random_motion(self):
        """Start a random motion"""
        if self.is_fallback:
            return
            
        if self.model:
            try:
                self.model.StartRandomMotion()
            except Exception as e:
                print(f"Motion error: {e}")

    def cleanup(self):
        """Cleanup Live2D resources"""
        if self.is_fallback:
            return
            
        if self.model:
            del self.model
            self.model = None
        if self.is_initialized:
            live2d.dispose()

class Live2DApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Live2D Python App with OpenGL")
        self.root.geometry("900x700")
        self.root.configure(bg='#2b2b2b')
        
        # Initialize components
        self.opengl_frame = None
        self.model_loaded = False
        
        self.setup_ui()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """Set up the user interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top section - Model display area
        self.setup_model_area(main_frame)
        
        # Middle section - Controls
        self.setup_controls(main_frame)
        
        # Bottom section - Text input
        self.setup_text_input(main_frame)
        
    def setup_model_area(self, parent):
        """Set up the Live2D model display area"""
        model_frame = tk.LabelFrame(
            parent, 
            text="Live2D Model (OpenGL)" if OPENGL_AVAILABLE else "Live2D Model (Dependencies Missing)", 
            bg='#3b3b3b', 
            fg='white', 
            font=('Arial', 12, 'bold')
        )
        model_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Always create the frame (it will handle fallback internally)
        self.opengl_frame = Live2DOpenGLFrame(
            model_frame,
            width=600,
            height=400
        )
        self.opengl_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Bind mouse click for random motion
        self.opengl_frame.bind("<Button-1>", self.on_model_click)
        
        # Status label
        if LIVE2D_AVAILABLE and OPENGL_AVAILABLE:
            self.status_label = tk.Label(
                model_frame, 
                text="✅ OpenGL initialized. Click 'Load Model' to get started.",
                bg='#3b3b3b', 
                fg='#4CAF50',
                font=('Arial', 10)
            )
        else:
            missing_packages = []
            if not OPENGL_AVAILABLE:
                missing_packages.extend(['pyopengltk', 'pyautogui'])
            if not LIVE2D_AVAILABLE:
                missing_packages.append('live2d')
            
            self.status_label = tk.Label(
                model_frame, 
                text=f"❌ Missing packages: {', '.join(missing_packages)}",
                bg='#3b3b3b', 
                fg='#ff6b6b',
                font=('Arial', 10)
            )
            
        self.status_label.pack(pady=5)
    
    def setup_controls(self, parent):
        """Set up control buttons"""
        control_frame = tk.Frame(parent, bg='#2b2b2b')
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Load model button
        self.load_button = tk.Button(
            control_frame,
            text="Load Model" if LIVE2D_AVAILABLE else "Install Dependencies",
            command=self.load_model if LIVE2D_AVAILABLE else self.show_install_help,
            bg='#4CAF50' if LIVE2D_AVAILABLE else '#ff6b6b',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=5
        )
        self.load_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Random motion button
        self.motion_button = tk.Button(
            control_frame,
            text="Random Motion",
            command=self.trigger_motion,
            bg='#2196F3',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=5,
            state=tk.DISABLED if not LIVE2D_AVAILABLE else tk.DISABLED
        )
        self.motion_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Animation toggle button
        self.anim_button = tk.Button(
            control_frame,
            text="Start Animation",
            command=self.toggle_animation,
            bg='#FF9800',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=5,
            state=tk.DISABLED if not LIVE2D_AVAILABLE else tk.DISABLED
        )
        self.anim_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Model info button
        self.info_button = tk.Button(
            control_frame,
            text="Model Info",
            command=self.show_model_info,
            bg='#9C27B0',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=5,
            state=tk.DISABLED if not LIVE2D_AVAILABLE else tk.DISABLED
        )
        self.info_button.pack(side=tk.LEFT)
    
    def setup_text_input(self, parent):
        """Set up the text input area at the bottom"""
        text_frame = tk.LabelFrame(
            parent, 
            text="Interactive Text Input (Always Available)", 
            bg='#3b3b3b', 
            fg='white', 
            font=('Arial', 12, 'bold')
        )
        text_frame.pack(fill=tk.X, pady=(0, 0))
        
        # Text input container
        input_container = tk.Frame(text_frame, bg='#3b3b3b')
        input_container.pack(fill=tk.X, padx=10, pady=10)
        
        # Text entry field
        self.text_entry = tk.Entry(
            input_container,
            font=('Arial', 12),
            bg='#1e1e1e',
            fg='white',
            insertbackground='white',
            relief=tk.FLAT,
            borderwidth=2
        )
        self.text_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.text_entry.bind('<Return>', self.on_text_submit)
        
        # Send button
        self.send_button = tk.Button(
            input_container,
            text="Send",
            command=self.on_text_submit,
            bg='#9C27B0',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Output text area
        output_container = tk.Frame(text_frame, bg='#3b3b3b')
        output_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Scrollable text output
        self.text_output = tk.Text(
            output_container,
            height=6,
            font=('Arial', 10),
            bg='#1e1e1e',
            fg='#cccccc',
            insertbackground='white',
            relief=tk.FLAT,
            borderwidth=1,
            wrap=tk.WORD
        )
        
        # Scrollbar for text output
        scrollbar = tk.Scrollbar(output_container, orient=tk.VERTICAL, command=self.text_output.yview)
        self.text_output.configure(yscrollcommand=scrollbar.set)
        
        self.text_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add welcome message
        self.add_output_message("🎭 Welcome to Live2D Python App!")
        
        if LIVE2D_AVAILABLE and OPENGL_AVAILABLE:
            self.add_output_message("✅ All dependencies loaded successfully")
            self.add_output_message("📁 Load a Live2D model to get started")
            self.add_output_message("🖱️ Click on the model to trigger random motions")
        else:
            self.add_output_message("❌ Live2D dependencies missing")
            self.add_output_message("💬 Text input still works - try typing 'help'!")
            self.add_output_message("📦 Click 'Install Dependencies' for help")
    
    def show_install_help(self):
        """Show installation help dialog"""
        help_text = """Live2D Dependencies Installation

Required packages:
• pyopengltk - OpenGL integration
• pyautogui - Mouse interaction
• live2d - Live2D model support

Installation commands:

1. Basic installation:
   pip install pyopengltk pyautogui live2d

2. If live2d is not available:
   Check alternative packages or build from source

3. Linux users may need:
   sudo apt-get install python3-opengl mesa-utils

4. macOS users may need:
   brew install mesa

After installation, restart the application.
"""
        messagebox.showinfo("Installation Help", help_text)
        self.add_output_message("📋 Installation help displayed")
    
    def load_model(self):
        """Load a Live2D model file"""
        if not LIVE2D_AVAILABLE:
            self.show_install_help()
            return
            
        file_path = filedialog.askopenfilename(
            title="Select Live2D Model File",
            filetypes=[
                ("Live2D v2 Model", "*.model.json"),
                ("Live2D v3 Model", "*.model3.json"),
                ("All JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                success = self.opengl_frame.load_model(file_path)
                
                if success:
                    self.model_loaded = True
                    model_name = os.path.basename(file_path)
                    
                    self.status_label.config(
                        text=f"✅ Model loaded: {model_name}",
                        fg='#4CAF50'
                    )
                    
                    # Enable buttons
                    self.motion_button.config(state=tk.NORMAL)
                    self.anim_button.config(state=tk.NORMAL)
                    self.info_button.config(state=tk.NORMAL)
                    
                    self.add_output_message(f"🎯 Successfully loaded: {model_name}")
                    self.add_output_message("🎮 Use controls above or click the model for interaction")
                    
                    # Start animation automatically
                    if hasattr(self.opengl_frame, 'animate'):
                        self.opengl_frame.animate = 1
                        self.anim_button.config(text="Stop Animation")
                    
                else:
                    raise Exception("Model loading failed")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load model: {str(e)}")
                self.add_output_message(f"❌ Failed to load model: {str(e)}")
    
    def trigger_motion(self):
        """Trigger random motion"""
        if not LIVE2D_AVAILABLE:
            self.add_output_message("❌ Live2D not available - install dependencies first")
            return
            
        if self.model_loaded and self.opengl_frame:
            self.opengl_frame.start_random_motion()
            self.add_output_message("🎭 Random motion triggered!")
        else:
            self.add_output_message("❌ No model loaded yet")
    
    def toggle_animation(self):
        """Toggle animation on/off"""
        if not LIVE2D_AVAILABLE or not self.model_loaded:
            return
            
        if hasattr(self.opengl_frame, 'animate'):
            if self.opengl_frame.animate:
                self.opengl_frame.animate = 0
                self.anim_button.config(text="Start Animation", bg='#4CAF50')
                self.add_output_message("⏸️ Animation paused")
            else:
                self.opengl_frame.animate = 1
                self.anim_button.config(text="Stop Animation", bg='#FF9800')
                self.add_output_message("▶️ Animation resumed")
    
    def show_model_info(self):
        """Show information about the loaded model"""
        if not LIVE2D_AVAILABLE:
            self.show_install_help()
            return
            
        if self.model_loaded and self.opengl_frame and self.opengl_frame.model_path:
            model_name = os.path.basename(self.opengl_frame.model_path)
            model_dir = os.path.dirname(self.opengl_frame.model_path)
            
            info = f"""
Model Information:
📁 Name: {model_name}
📂 Directory: {model_dir}
🎮 Live2D Version: {getattr(live2d, 'LIVE2D_VERSION', 'Unknown')}
🖼️ Frame Size: {self.opengl_frame.width}x{self.opengl_frame.height}
✅ Status: Loaded and Ready
            """.strip()
            
            messagebox.showinfo("Model Information", info)
            self.add_output_message(f"ℹ️ Model info displayed for {model_name}")
        else:
            self.add_output_message("❌ No model loaded to show info for")
    
    def on_model_click(self, event):
        """Handle mouse click on model"""
        if LIVE2D_AVAILABLE:
            self.trigger_motion()
        else:
            self.add_output_message("❌ Live2D dependencies missing - text input still works!")
    
    def on_text_submit(self, event=None):
        """Handle text input submission"""
        text = self.text_entry.get().strip()
        if text:
            self.add_output_message(f"👤 You: {text}")
            self.text_entry.delete(0, tk.END)
            
            # Process the text
            self.process_user_input(text)
    
    def process_user_input(self, text):
        """Process user input and generate responses"""
        text_lower = text.lower()
        
        if "hello" in text_lower or "hi" in text_lower:
            if LIVE2D_AVAILABLE and self.model_loaded:
                self.trigger_motion()
                response = "👋 Hello! Your Live2D model is ready for interaction!"
            else:
                response = "👋 Hello! The text input works even without Live2D!"
                
        elif "install" in text_lower or "dependencies" in text_lower:
            self.show_install_help()
            response = "📦 Installation help displayed!"
            
        elif "motion" in text_lower or "move" in text_lower:
            if LIVE2D_AVAILABLE and self.model_loaded:
                self.trigger_motion()
                response = "🎭 Motion triggered! Your model should be moving now."
            elif not LIVE2D_AVAILABLE:
                response = "❌ Live2D not installed. Install dependencies first!"
            else:
                response = "❌ Please load a model first to trigger motions."
                
        elif "model" in text_lower:
            if not LIVE2D_AVAILABLE:
                response = "❌ Live2D not available. Install: pip install pyopengltk pyautogui live2d"
            elif self.model_loaded:
                response = "✅ Live2D model is loaded and ready! Click it or use the controls."
            else:
                response = "❌ No model is currently loaded. Use 'Load Model' button."
                
        elif "help" in text_lower:
            if LIVE2D_AVAILABLE:
                response = ("🆘 Available commands:\n"
                           "• 'hello' - Greeting + motion\n"
                           "• 'motion' - Trigger random motion\n"
                           "• 'model' - Check model status\n"
                           "• 'install' - Show installation help\n"
                           "• Click the model for interaction!")
            else:
                response = ("🆘 Text-only mode commands:\n"
                           "• 'hello' - Greeting\n"
                           "• 'install' - Installation help\n"
                           "• 'model' - Check Live2D status\n"
                           "• Install dependencies for full features!")
                           
        elif "info" in text_lower:
            if LIVE2D_AVAILABLE and self.model_loaded:
                self.show_model_info()
                response = "ℹ️ Model information displayed!"
            elif not LIVE2D_AVAILABLE:
                response = "ℹ️ App running in text-only mode. Install dependencies for Live2D features."
            else:
                response = "❌ No model loaded to show info for."
        else:
            response = f"💬 You said: '{text}'. Try 'help' for available commands!"
        
        # Add response with delay
        self.root.after(500, lambda: self.add_output_message(f"🤖 App: {response}"))
    
    def add_output_message(self, message):
        """Add a message to the output text area"""
        self.text_output.insert(tk.END, f"{message}\n")
        self.text_output.see(tk.END)
    
    def on_closing(self):
        """Handle application closing"""
        if self.opengl_frame:
            self.opengl_frame.cleanup()
        self.root.destroy()

def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = Live2DApp(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (900 // 2)
    y = (root.winfo_screenheight() // 2) - (700 // 2)
    root.geometry(f"900x700+{x}+{y}")
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        if hasattr(app, 'opengl_frame') and app.opengl_frame:
            app.opengl_frame.cleanup()

if __name__ == "__main__":
    main()
