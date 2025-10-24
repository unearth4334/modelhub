#!/usr/bin/env python3
"""
Example script to test text generation endpoint.
"""

import requests
import sys


def test_text_generation():
    """Test the text generation endpoint."""
    url = "http://localhost:8000/api/v1/generate/text"

    # Test prompt
    payload = {
        "prompt": "Write a haiku about artificial intelligence",
        "model": "deepseek-r1:8b",
        "max_tokens": 100,
        "temperature": 0.8,
    }

    print("Testing text generation endpoint...")
    print(f"Prompt: {payload['prompt']}")
    print()

    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        print("Generated text:")
        print("-" * 50)
        print(result["text"])
        print("-" * 50)
        print(f"Model used: {result['model']}")
        print()
        print("✓ Test passed!")

    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_text_generation()
