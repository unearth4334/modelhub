#!/usr/bin/env python3
"""
Test script to verify cache headers and boot ID functionality.
"""

import requests
import sys
import time


def test_cache_headers():
    """Test cache header implementation."""
    base_url = "http://localhost:8000"
    
    print("Testing cache headers and boot ID functionality...")
    print()
    
    # Test 1: Check /meta.json endpoint
    try:
        print("1. Testing /meta.json endpoint...")
        response = requests.get(f"{base_url}/meta.json", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "bootId" in data:
            boot_id = data["bootId"]
            print(f"   ✓ Boot ID endpoint working (bootId: {boot_id})")
        else:
            print("   ✗ Boot ID not found in /meta.json response")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Error accessing /meta.json: {e}")
        sys.exit(1)
    
    # Test 2: Check HTML cache headers
    try:
        print("2. Testing HTML cache headers...")
        response = requests.get(f"{base_url}/dashboard", timeout=5)
        response.raise_for_status()
        
        cache_control = response.headers.get("Cache-Control", "")
        if "no-cache" in cache_control and "must-revalidate" in cache_control:
            print(f"   ✓ HTML has correct cache headers: {cache_control}")
        else:
            print(f"   ✗ HTML cache headers incorrect: {cache_control}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Error accessing /dashboard: {e}")
        sys.exit(1)
    
    # Test 3: Check static asset cache headers
    try:
        print("3. Testing static asset cache headers...")
        response = requests.get(f"{base_url}/static/js/dashboard.js", timeout=5)
        response.raise_for_status()
        
        cache_control = response.headers.get("Cache-Control", "")
        if "public" in cache_control and "max-age=31536000" in cache_control and "immutable" in cache_control:
            print(f"   ✓ Static assets have correct cache headers: {cache_control}")
        else:
            print(f"   ✗ Static asset cache headers incorrect: {cache_control}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Error accessing static asset: {e}")
        sys.exit(1)
    
    # Test 4: Check root endpoint cache headers
    try:
        print("4. Testing root endpoint cache headers...")
        response = requests.get(f"{base_url}/", timeout=5)
        response.raise_for_status()
        
        cache_control = response.headers.get("Cache-Control", "")
        if "no-cache" in cache_control and "must-revalidate" in cache_control:
            print(f"   ✓ Root endpoint has correct cache headers: {cache_control}")
        else:
            print(f"   ✗ Root endpoint cache headers incorrect: {cache_control}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Error accessing root endpoint: {e}")
        sys.exit(1)
    
    # Test 5: Verify boot ID is in HTML
    try:
        print("5. Testing boot ID script in HTML...")
        response = requests.get(f"{base_url}/dashboard", timeout=5)
        response.raise_for_status()
        
        if "fetch('/meta.json'" in response.text and "localStorage.getItem('bootId')" in response.text:
            print("   ✓ Boot ID auto-reload script found in HTML")
        else:
            print("   ✗ Boot ID script not found in HTML")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Error checking HTML content: {e}")
        sys.exit(1)
    
    # Test 6: Verify meta endpoint is listed in root
    try:
        print("6. Testing meta endpoint listing...")
        response = requests.get(f"{base_url}/", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "meta" in data.get("endpoints", {}):
            print("   ✓ Meta endpoint is listed in root response")
        else:
            print("   ✗ Meta endpoint not listed in root response")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Error accessing root endpoint: {e}")
        sys.exit(1)
    
    print()
    print("✓ All cache header tests passed!")
    print()
    print("Cache invalidation features:")
    print("  - HTML pages always revalidated (no-cache, must-revalidate)")
    print("  - Static assets cached for 1 year with immutable flag")
    print("  - Server boot ID available at /meta.json")
    print("  - Client auto-reloads when boot ID changes")


if __name__ == "__main__":
    test_cache_headers()
