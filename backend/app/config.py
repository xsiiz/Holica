import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"
STATIC_DIR = BASE_DIR / "static"

# Ensure directories exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Device configuration
try:
    import torch
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32
except ImportError:
    torch = None
    DEVICE = "cpu"
    DTYPE = None

# Model Configurations
CHAT_MODEL_REPO = "TheBloke/dolphin-2.8-mistral-7b-v02-GGUF"
CHAT_MODEL_FILE = "dolphin-2.8-mistral-7b-v02.Q4_K_M.gguf"
CHAT_MODEL_PATH = MODELS_DIR / CHAT_MODEL_FILE

# Image Generation Model (Uncensored SD 1.5)
IMAGE_MODEL_ID = "SG161222/Realistic_Vision_V5.1_noVAE"
# Alternative: "cyberdelia/CyberRealistic_V4.0" or local safetensors

# Video Generation Model (AnimateDiff)
VIDEO_BASE_MODEL_ID = IMAGE_MODEL_ID
MOTION_ADAPTER_ID = "guoyww/animatediff-motion-adapter-v1-5-3"

# Generation Defaults
DEFAULT_IMAGE_STEPS = 25
DEFAULT_IMAGE_CFG = 7.0
DEFAULT_VIDEO_FRAMES = 16
DEFAULT_VIDEO_FPS = 8

# Server config
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 7000))
ENABLE_TUNNEL = os.environ.get("ENABLE_TUNNEL", "true").lower() == "true"
MOCK_MODELS = os.environ.get("MOCK_MODELS", "false").lower() == "true"
