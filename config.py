import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project Directory Structure
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

# Create directories if they do not exist
ASSETS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
RUNWAYML_API_SECRET = os.getenv("RUNWAYML_API_SECRET", "")
RUNWAYML_MODEL = os.getenv("RUNWAYML_MODEL", "gen3a")

# Default Video Configuration
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 1280
ASPECT_RATIO = "720:1280"  # 9:16 vertical
DEFAULT_FPS = 24

# Category Adaptations for Tone, Pacing, Style & Prompt Templates
CATEGORY_SETTINGS = {
    "motivational": {
        "voice_stability": 0.35,  # More dynamic, expressive delivery
        "voice_similarity": 0.85,
        "style_prompt_suffix": "epic, cinematic lighting, dramatic contrast, slow-motion, highly detailed, inspirational, vertical 9:16 composition",
        "subtitle_color": (255, 223, 0),  # Gold text
        "subtitle_font_size": 48,
        "bg_music_volume": 0.12,
        "default_music": "motivational.mp3"
    },
    "educational": {
        "voice_stability": 0.75,  # Clear, steady, informative delivery
        "voice_similarity": 0.85,
        "style_prompt_suffix": "clean composition, soft studio lighting, professional, minimalistic design, realistic, high definition, vertical 9:16 composition",
        "subtitle_color": (255, 255, 255),  # White text
        "subtitle_font_size": 44,
        "bg_music_volume": 0.08,
        "default_music": "ambient.mp3"
    },
    "product": {
        "voice_stability": 0.50,  # Engaging, polished commercial delivery
        "voice_similarity": 0.85,
        "style_prompt_suffix": "sleek advertising showcase, product photography, studio background, luxury lighting, ultra HD, crisp details, vertical 9:16 composition",
        "subtitle_color": (255, 255, 255),  # White text
        "subtitle_font_size": 46,
        "bg_music_volume": 0.10,
        "default_music": "corporate.mp3"
    }
}
