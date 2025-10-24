# ModelHub - Unified AI Model Service

A Docker-based unified AI model service that allows applications running on a QNAP NAS (or any Docker-compatible system) to interact with text and image models through a single REST API.

## Features

- **Text Generation**: LLM inference using Ollama (e.g., deepseek-r1:8b)
- **Image Analysis**: Image classification using Hugging Face models (marqo/nsfw-image-detection-384)
- **Single REST API**: Unified interface for both text and image models
- **Docker-based**: Easy deployment with docker-compose
- **Health Monitoring**: Built-in health check endpoints

## Architecture

The service consists of two Docker containers:
1. **Ollama**: Serves LLMs for text generation
2. **API Service**: FastAPI-based REST API that integrates Ollama and Hugging Face models

## Prerequisites

- Docker Engine (20.10+)
- Docker Compose (2.0+)
- At least 8GB RAM (16GB recommended)
- 10GB+ free disk space

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/unearth4334/modelhub.git
cd modelhub
```

### 2. Start the Services

```bash
# Using Docker Compose V2 (recommended)
docker compose up -d

# Or using Docker Compose V1
docker-compose up -d
```

This will:
- Pull and start the Ollama container
- Build and start the API service container

### 3. Download the LLM Model

After the services are running, download the deepseek-r1:8b model:

```bash
docker exec -it modelhub-ollama ollama pull deepseek-r1:8b
```

### 4. Verify the Service

Check service health:

```bash
curl http://localhost:8000/health
```

## API Endpoints

### Root Endpoint

```bash
GET http://localhost:8000/
```

Returns API information and available endpoints.

### Health Check

```bash
GET http://localhost:8000/health
```

Returns service health status including Ollama availability.

Response example:
```json
{
  "status": "healthy",
  "ollama_available": true,
  "image_model_loaded": false
}
```

### Text Generation

```bash
POST http://localhost:8000/api/v1/generate/text
Content-Type: application/json

{
  "prompt": "Explain quantum computing in simple terms",
  "model": "deepseek-r1:8b",
  "max_tokens": 512,
  "temperature": 0.7
}
```

Response example:
```json
{
  "text": "Quantum computing is...",
  "model": "deepseek-r1:8b"
}
```

### Image Analysis

```bash
POST http://localhost:8000/api/v1/analyze/image
Content-Type: multipart/form-data

file: [image file]
```

Response example:
```json
{
  "predictions": [
    {"label": "safe", "score": 0.95},
    {"label": "unsafe", "score": 0.05}
  ],
  "model": "marqo/nsfw-image-detection-384"
}
```

## Usage Examples

### Text Generation with cURL

```bash
curl -X POST http://localhost:8000/api/v1/generate/text \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a haiku about coding",
    "model": "deepseek-r1:8b",
    "max_tokens": 100,
    "temperature": 0.8
  }'
```

### Image Analysis with cURL

```bash
curl -X POST http://localhost:8000/api/v1/analyze/image \
  -F "file=@/path/to/image.jpg"
```

### Python Client Example

```python
import requests

# Text generation
response = requests.post(
    "http://localhost:8000/api/v1/generate/text",
    json={
        "prompt": "What is machine learning?",
        "model": "deepseek-r1:8b",
        "max_tokens": 256
    }
)
print(response.json()["text"])

# Image analysis
with open("image.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/analyze/image",
        files={"file": f}
    )
print(response.json()["predictions"])
```

## Configuration

### Environment Variables

The API service can be configured using environment variables in `docker-compose.yml`:

- `PYTHONUNBUFFERED=1`: Enable real-time logging

### Changing Models

To use different Ollama models:

1. Pull the desired model:
   ```bash
   docker exec -it modelhub-ollama ollama pull <model-name>
   ```

2. Use the model name in API requests:
   ```json
   {
     "prompt": "Your prompt",
     "model": "<model-name>"
   }
   ```

Available Ollama models: https://ollama.com/library

## Port Configuration

Default ports:
- API Service: `8000`
- Ollama: `11434`

To change ports, modify `docker-compose.yml`:

```yaml
services:
  api:
    ports:
      - "YOUR_PORT:8000"  # Change YOUR_PORT
  ollama:
    ports:
      - "YOUR_PORT:11434"  # Change YOUR_PORT
```

## Managing the Service

### Start Services

```bash
docker compose up -d
```

### Stop Services

```bash
docker compose down
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f ollama
```

### Restart Services

```bash
docker compose restart
```

### Remove All Data

```bash
docker compose down -v
```

**Note:** If using Docker Compose V1, replace `docker compose` with `docker-compose` in all commands.

## Troubleshooting

### Ollama Not Available

If health check shows `ollama_available: false`:

1. Check Ollama container status:
   ```bash
   docker ps
   ```

2. Check Ollama logs:
   ```bash
   docker compose logs ollama
   ```

3. Ensure the model is downloaded:
   ```bash
   docker exec -it modelhub-ollama ollama list
   ```

### API Service Errors

1. Check API logs:
   ```bash
   docker compose logs api
   ```

2. Verify containers can communicate:
   ```bash
   docker exec -it modelhub-api ping ollama
   ```

### Memory Issues

If running out of memory:

1. Increase Docker memory limit
2. Use smaller models (e.g., `deepseek-r1:1.5b`)
3. Close unnecessary applications

## QNAP NAS Deployment

For QNAP NAS users:

1. Install Container Station from the QNAP App Center
2. Clone this repository to your NAS
3. Open Container Station
4. Click "Create" → "Create Application"
5. Select the `docker-compose.yml` file
6. Click "Create"

The service will be accessible at `http://<NAS-IP>:8000`

## Development

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run API service (requires Ollama running separately)
python app.py
```

### API Documentation

Once the service is running, access interactive API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Performance Considerations

- First image analysis request will be slower as the model loads (30-60 seconds)
- Subsequent requests will be faster as the model stays in memory
- Text generation speed depends on the Ollama model size and your hardware
- GPU acceleration is supported if available

## Security Notes

- The service listens on all interfaces (0.0.0.0) by default
- Consider adding authentication for production use
- Restrict network access using firewall rules
- Keep Docker images updated

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Support

For issues and questions:
- GitHub Issues: https://github.com/unearth4334/modelhub/issues
