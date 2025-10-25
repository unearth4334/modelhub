#!/usr/bin/env python3
"""
Example script to test the dashboard endpoint.
"""

import requests
import sys


def test_dashboard():
    """Test the dashboard endpoint."""
    base_url = "http://localhost:8000"
    
    print("Testing dashboard endpoints...")
    print()
    
    # Test root endpoint
    try:
        print("1. Testing root endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "dashboard" in data.get("endpoints", {}):
            print("   ✓ Root endpoint includes dashboard")
        else:
            print("   ✗ Dashboard not listed in root endpoint")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Error accessing root endpoint: {e}")
        sys.exit(1)
    
    # Test dashboard HTML endpoint
    try:
        print("2. Testing dashboard HTML endpoint...")
        response = requests.get(f"{base_url}/dashboard", timeout=5)
        response.raise_for_status()
        
        if "ModelHub Dashboard" in response.text:
            print("   ✓ Dashboard HTML loaded successfully")
        else:
            print("   ✗ Dashboard HTML missing title")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Error accessing dashboard: {e}")
        sys.exit(1)
    
    # Test static CSS file
    try:
        print("3. Testing static CSS file...")
        response = requests.get(f"{base_url}/static/css/dashboard.css", timeout=5)
        response.raise_for_status()
        
        if "Dark Theme Dashboard CSS" in response.text:
            print("   ✓ Dashboard CSS loaded successfully")
        else:
            print("   ✗ Dashboard CSS file incorrect")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Error accessing CSS: {e}")
        sys.exit(1)
    
    # Test static JavaScript file
    try:
        print("4. Testing static JavaScript file...")
        response = requests.get(f"{base_url}/static/js/dashboard.js", timeout=5)
        response.raise_for_status()
        
        if "Dashboard JavaScript" in response.text:
            print("   ✓ Dashboard JavaScript loaded successfully")
        else:
            print("   ✗ Dashboard JavaScript file incorrect")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Error accessing JavaScript: {e}")
        sys.exit(1)
    
    # Test health endpoint (used by dashboard)
    try:
        print("5. Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "status" in data and "ollama_available" in data:
            print("   ✓ Health endpoint working")
        else:
            print("   ✗ Health endpoint missing required fields")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Error accessing health endpoint: {e}")
        sys.exit(1)
    
    # Test models endpoint (used by dashboard dropdown)
    try:
        print("6. Testing models endpoint...")
        response = requests.get(f"{base_url}/api/v1/models", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "models" in data and "default_model" in data:
            print(f"   ✓ Models endpoint working (found {len(data['models'])} models)")
            if data['models']:
                print(f"   ✓ Available models: {', '.join(data['models'])}")
        else:
            print("   ✗ Models endpoint missing required fields")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Error accessing models endpoint: {e}")
        sys.exit(1)
    
    print()
    print("✓ All dashboard tests passed!")
    print()
    print("Dashboard is available at: http://localhost:8000/dashboard")


if __name__ == "__main__":
    test_dashboard()
