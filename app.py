"""
Unified AI Model Service API
Provides endpoints for text generation (via Ollama) and image analysis (via Hugging Face).
"""

import io
import logging
from typing import Optional

import httpx
import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel, Field
from transformers import pipeline

import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Unified AI Model Service",
    description="REST API for text generation and image analysis",
    version="1.0.0",
)

# Configuration from config module
OLLAMA_BASE_URL = config.OLLAMA_BASE_URL
DEFAULT_TEXT_MODEL = config.DEFAULT_TEXT_MODEL
IMAGE_MODEL = config.IMAGE_MODEL
HUGGINGFACE_TOKEN = config.HUGGINGFACE_TOKEN
OLLAMA_TIMEOUT = config.OLLAMA_TIMEOUT
HEALTH_CHECK_TIMEOUT = config.HEALTH_CHECK_TIMEOUT

# Initialize image classification pipeline (lazy loading)
image_classifier = None


def get_image_classifier():
    """Lazy load the image classification model."""
    global image_classifier
    if image_classifier is None:
        logger.info(f"Loading image classification model: {IMAGE_MODEL}")
        device = 0 if torch.cuda.is_available() else -1
        
        # Use Hugging Face token if available
        kwargs = {"device": device}
        if HUGGINGFACE_TOKEN:
            kwargs["use_auth_token"] = HUGGINGFACE_TOKEN
            logger.info("Using Hugging Face authentication token")
        
        image_classifier = pipeline(
            "image-classification",
            model=IMAGE_MODEL,
            **kwargs
        )
        logger.info("Image classification model loaded successfully")
    return image_classifier


# Request/Response models
class TextGenerationRequest(BaseModel):
    """Request model for text generation."""

    prompt: str = Field(..., description="The text prompt for generation")
    model: Optional[str] = Field(
        default=DEFAULT_TEXT_MODEL, description="The Ollama model to use"
    )
    max_tokens: Optional[int] = Field(default=512, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=0.7, description="Sampling temperature")
    stream: Optional[bool] = Field(default=False, description="Enable streaming responses")


class TextGenerationResponse(BaseModel):
    """Response model for text generation."""

    text: str = Field(..., description="Generated text")
    model: str = Field(..., description="Model used for generation")


class ImageAnalysisResponse(BaseModel):
    """Response model for image analysis."""

    predictions: list[dict] = Field(..., description="List of label predictions with scores")
    model: str = Field(..., description="Model used for analysis")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    ollama_available: bool
    image_model_loaded: bool


# API Endpoints
@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Unified AI Model Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "text_generation": "/api/v1/generate/text",
            "image_analysis": "/api/v1/analyze/image",
        },
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    ollama_available = False
    image_model_loaded = image_classifier is not None

    # Check Ollama availability
    try:
        async with httpx.AsyncClient(timeout=HEALTH_CHECK_TIMEOUT) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            ollama_available = response.status_code == 200
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")

    return HealthResponse(
        status="healthy" if ollama_available else "degraded",
        ollama_available=ollama_available,
        image_model_loaded=image_model_loaded,
    )


@app.post("/api/v1/generate/text", response_model=TextGenerationResponse)
async def generate_text(request: TextGenerationRequest):
    """
    Generate text using Ollama LLM.

    Args:
        request: TextGenerationRequest with prompt and generation parameters

    Returns:
        TextGenerationResponse with generated text
    """
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            payload = {
                "model": request.model,
                "prompt": request.prompt,
                "stream": False,
                "options": {
                    "num_predict": request.max_tokens,
                    "temperature": request.temperature,
                },
            }

            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ollama API error: {response.text}",
                )

            result = response.json()
            generated_text = result.get("response", "")

            return TextGenerationResponse(
                text=generated_text,
                model=request.model,
            )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Request to Ollama timed out",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to Ollama: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Text generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


@app.post("/api/v1/analyze/image", response_model=ImageAnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    """
    Analyze an image using Hugging Face model.

    Args:
        file: Uploaded image file

    Returns:
        ImageAnalysisResponse with predictions
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image",
        )

    try:
        # Read and process image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Get classifier and make predictions
        classifier = get_image_classifier()
        predictions = classifier(image)

        return ImageAnalysisResponse(
            predictions=predictions,
            model=IMAGE_MODEL,
        )

    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        
        # Provide specific error messages for common Hugging Face authentication issues
        error_msg = str(e)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            detail = "Hugging Face authentication failed. Check HUGGINGFACE_TOKEN or api_keys.txt file."
        elif "403" in error_msg or "forbidden" in error_msg.lower():
            detail = "Access forbidden to Hugging Face model. Check model permissions or authentication."
        elif "rate limit" in error_msg.lower():
            detail = "Hugging Face API rate limit exceeded. Please try again later."
        else:
            detail = f"Image analysis failed: {str(e)}"
            
        raise HTTPException(
            status_code=500,
            detail=detail,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)
