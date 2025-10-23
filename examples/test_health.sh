#!/bin/bash
# Test health check endpoint

echo "Testing health check endpoint..."
echo ""

response=$(curl -s http://localhost:8000/health)

if [ $? -eq 0 ]; then
    echo "Health check response:"
    echo "$response" | python3 -m json.tool
    echo ""
    echo "✓ Test passed!"
else
    echo "✗ Error: Could not connect to service"
    exit 1
fi
