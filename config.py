"""Configuration settings for the Live2D Python App"""

# Window settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_TITLE = "Live2D Python App"

# Colors (Dark theme)
COLORS = {
    'bg_primary': '#2b2b2b',
    'bg_secondary': '#3b3b3b', 
    'bg_canvas': '#1e1e1e',
    'text_primary': 'white',
    'text_secondary': '#cccccc',
    'accent_green': '#4CAF50',
    'accent_blue': '#2196F3',
    'accent_orange': '#FF9800',
    'accent_purple': '#9C27B0',
    'error_red': '#ff6b6b'
}

# Text input settings
TEXT_INPUT_HEIGHT = 6
MAX_OUTPUT_LINES = 1000

# Model settings
DEFAULT_MODEL_PATH = "models/"
SUPPORTED_FORMATS = [
    ("Live2D Model", "*.model3.json"),
    ("All files", "*.*")
]

# Animation settings
DEFAULT_ANIMATION_SPEED = 1.0
ANIMATION_LOOP = True
