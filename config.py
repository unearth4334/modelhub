"""
Configuration settings for the ModelHub service.
Can be overridden using environment variables.
"""

import os

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
DEFAULT_TEXT_MODEL = os.getenv("DEFAULT_TEXT_MODEL", "deepseek-r1:8b")

# Hugging Face Configuration
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "marqo/nsfw-image-detection-384")

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Model Loading Configuration
LAZY_LOAD_IMAGE_MODEL = os.getenv("LAZY_LOAD_IMAGE_MODEL", "true").lower() == "true"

# Timeout Configuration (seconds)
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))
HEALTH_CHECK_TIMEOUT = int(os.getenv("HEALTH_CHECK_TIMEOUT", "5"))
