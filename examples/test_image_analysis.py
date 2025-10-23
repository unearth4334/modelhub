#!/usr/bin/env python3
"""
Example script to test image analysis endpoint.
"""

import requests
import sys
import os


def test_image_analysis(image_path=None):
    """Test the image analysis endpoint."""
    url = "http://localhost:8000/api/v1/analyze/image"

    # If no image path provided, create a simple test image
    if image_path is None:
        print("Creating a test image...")
        from PIL import Image
        import io

        # Create a simple colored image
        img = Image.new("RGB", (200, 200), color=(73, 109, 137))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
    else:
        if not os.path.exists(image_path):
            print(f"Error: Image file not found: {image_path}")
            sys.exit(1)
        files = {"file": open(image_path, "rb")}

    print("Testing image analysis endpoint...")
    print()

    try:
        response = requests.post(url, files=files, timeout=120)
        response.raise_for_status()

        result = response.json()
        print("Analysis results:")
        print("-" * 50)
        for prediction in result["predictions"]:
            label = prediction["label"]
            score = prediction["score"]
            print(f"  {label}: {score:.4f} ({score*100:.2f}%)")
        print("-" * 50)
        print(f"Model used: {result['model']}")
        print()
        print("✓ Test passed!")

    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
    finally:
        if image_path and "file" in files:
            files["file"].close()


if __name__ == "__main__":
    # Check if image path provided as argument
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    test_image_analysis(image_path)
