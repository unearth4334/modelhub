"""
Configuration settings for the ModelHub service.
Can be overridden using environment variables.
"""

import os
from pathlib import Path

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
DEFAULT_TEXT_MODEL = os.getenv("DEFAULT_TEXT_MODEL", "deepseek-optimized")

# Hugging Face Configuration
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "marqo/nsfw-image-detection-384")

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Model Loading Configuration
LAZY_LOAD_IMAGE_MODEL = os.getenv("LAZY_LOAD_IMAGE_MODEL", "true").lower() == "true"

# Timeout Configuration (seconds)
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "600"))  # Increased for larger models
HEALTH_CHECK_TIMEOUT = int(os.getenv("HEALTH_CHECK_TIMEOUT", "5"))


def load_api_keys():
    """Load API keys from api_keys.txt file."""
    api_keys = {}
    api_keys_file = Path(__file__).parent / "api_keys.txt"
    
    if api_keys_file.exists():
        try:
            with open(api_keys_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            api_keys[key.strip()] = value.strip()
        except Exception as e:
            print(f"Warning: Failed to load API keys from {api_keys_file}: {e}")
    
    return api_keys


# Load API keys
_api_keys = load_api_keys()

# Hugging Face Configuration  
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", _api_keys.get("huggingface", ""))
