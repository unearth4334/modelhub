# ModelHub Examples

This directory contains example scripts to test the ModelHub API endpoints.

## Prerequisites

Ensure the ModelHub service is running:

```bash
docker compose up -d
```

## Example Scripts

### 1. Health Check Test

Test the health check endpoint:

```bash
./test_health.sh
```

Or with curl:

```bash
curl http://localhost:8000/health | python3 -m json.tool
```

### 2. Text Generation Test

Test the text generation endpoint:

```bash
python3 test_text_generation.py
```

This will send a sample prompt to the Ollama service and display the generated text.

### 3. Image Analysis Test

Test the image analysis endpoint:

```bash
# With auto-generated test image
python3 test_image_analysis.py

# With your own image
python3 test_image_analysis.py /path/to/your/image.jpg
```

## Using cURL

### Text Generation

```bash
curl -X POST http://localhost:8000/api/v1/generate/text \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain Docker in simple terms",
    "model": "llama3.2:1b",
    "max_tokens": 256,
    "temperature": 0.7
  }' | python3 -m json.tool
```

### Image Analysis

```bash
curl -X POST http://localhost:8000/api/v1/analyze/image \
  -F "file=@/path/to/image.jpg" | python3 -m json.tool
```

## Troubleshooting

If you get connection errors:

1. Check if the service is running:
   ```bash
   docker ps
   ```

2. Check service logs:
   ```bash
   docker compose logs -f api
   ```

3. Verify the health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```

If Ollama models are not available, pull them first:

```bash
docker exec -it modelhub-ollama ollama pull llama3.2:1b
```
