# ModelHub AI Coding Assistant Instructions

## Project Overview

ModelHub is a containerized unified AI service providing REST APIs for text generation (via Ollama) and image analysis (via Hugging Face). It's designed for deployment on QNAP NAS or any Docker-compatible system.

## Architecture

**Two-container system:**
- `ollama` container: Serves LLMs (default: deepseek-r1:8b)
- `api` container: FastAPI service bridging Ollama + HuggingFace models

**Key service communication:** API container connects to Ollama at `http://ollama:11434` (Docker internal networking)

## Critical Workflows

### Development Setup
```bash
# Always use setup.sh for initial deployment
./setup.sh

# For development iterations
docker compose up -d --build  # rebuild API container
docker exec -it modelhub-ollama ollama pull <model-name>  # add models
```

### Testing Pipeline
- Use `examples/` scripts for endpoint validation
- Text generation requires Ollama model to be pulled first
- Image analysis uses lazy-loaded HuggingFace models (first request is slow)

### Configuration Pattern
Environment-first config in `config.py` - all settings have `os.getenv()` fallbacks:
- `OLLAMA_BASE_URL`: Default "http://ollama:11434" (container name resolution)
- `DEFAULT_TEXT_MODEL`: Default "deepseek-r1:8b"
- `IMAGE_MODEL`: Default "marqo/nsfw-image-detection-384"

## Code Patterns

### Lazy Model Loading
Image classifier loads on first request via `get_image_classifier()` global function - avoids startup delays but adds latency to first image request.

### Error Handling Strategy
- Ollama communication: httpx with explicit timeout handling
- Health checks: Non-blocking failures (returns "degraded" status)
- File uploads: PIL-based image validation before processing

### API Design
RESTful endpoints with Pydantic models:
- `POST /api/v1/generate/text` - Text generation with streaming support
- `POST /api/v1/analyze/image` - Multipart file upload for images
- `GET /health` - Service health including Ollama connectivity

## Development Conventions

### Dependency Management
Pin exact versions in `requirements.txt` (see transformer/torch compatibility)

### Container Health Checks
Both services have health checks with 30s intervals - API depends on Ollama health

### Logging
Structured logging with FastAPI correlation - check `docker compose logs api` for request traces

## Common Integration Points

### Adding New Models
1. Update `config.py` defaults or environment variables
2. For Ollama: Pull model in Ollama container
3. For HuggingFace: Update `IMAGE_MODEL` and model loading logic

### Scaling Considerations
- Image model loading is memory-intensive (check GPU availability in lazy loader)
- Ollama model size affects memory requirements (documented minimums in README)
- First image request takes 30-60s for model download

### Deployment Variations
Use `deploy.sh` for remote deployments - supports SSH deployment with git sync and volume management for different environments.

### QNAP Production Deployment
This workspace is for development only. Production container runs on QNAP NAS:

```bash
# Check running containers on QNAP
ssh qnap "cd /share/Container/modelhub && /share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker ps"

# Deploy code to QNAP (after committing changes)
git add .
git commit -m "your changes"
git push
./deploy.sh deploy --branch desired-branch --clean --build
```

**QNAP Debugging**: No git available on QNAP, but filesystem accessible via SMB mount at `/mnt/qnap-containers/modelhub/` for debugging deployment issues.

## File Structure Significance
- `app.py`: Single-file FastAPI app (no modules - intentionally simple)
- `examples/`: Runnable test scripts demonstrating API usage patterns
- `docker-compose.yml`: Health check dependencies ensure proper startup order
- `deploy.sh`: Production deployment with remote SSH support

When modifying APIs, always update corresponding example scripts and test with the full Docker setup, not just local Python execution.