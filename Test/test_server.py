#!/usr/bin/env python3
"""
Test script for the HTTP Ingestion Server.

This script tests the server endpoints with sample data to verify
that the API is working correctly.

Uses Flask's test client for direct testing without requiring the server to be running.
"""

import base64
import json
import sys
from pathlib import Path
from io import BytesIO

# Add parent directory to path so we can import backend and server modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the Flask app
from server.app import app

# Get API key from config
from server.config import INGESTION_API_KEY

API_KEY = INGESTION_API_KEY

def test_health_check(client):
    """Test the health check endpoint."""
    print("\n" + "="*60)
    print("Testing Health Check Endpoint")
    print("="*60)
    
    try:
        response = client.get('/health')
        print(f"Status Code: {response.status_code}")
        data = response.get_json()
        print(f"Response: {data}")
        
        if response.status_code == 200:
            print("✓ Health check passed")
            return True
        else:
            print("✗ Health check failed")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_process_image_json(client):
    """Test the JSON endpoint with base64 image."""
    print("\n" + "="*60)
    print("Testing JSON Endpoint (/api/v1/process-image)")
    print("="*60)
    
    # Create a tiny test image (1x1 PNG)
    tiny_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    payload = {
        "image": tiny_png_base64,
        "room_id": "test-room-json",
        "timestamp": "2025-11-26T10:00:00Z"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": API_KEY
    }
    
    try:
        response = client.post(
            '/api/v1/process-image',
            data=json.dumps(payload),
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        data = response.get_json()
        print(f"Response: {data}")
        
        if response.status_code == 200:
            print("✓ JSON endpoint test passed")
            return True
        else:
            print("✗ JSON endpoint test failed")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_process_image_multipart(client):
    """Test the multipart endpoint with a real image file."""
    print("\n" + "="*60)
    print("Testing Multipart Endpoint (/api/v1/process-image-bytes)")
    print("="*60)
    
    # Check if test image exists - path is relative to repository root
    repo_root = Path(__file__).resolve().parent.parent
    image_path = repo_root / "testing_images" / "sevenpeople.jpg"
    
    if not image_path.exists():
        print(f"⚠️  Test image not found: {image_path}")
        print("   Skipping multipart test")
        return None
    
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
        
    data = {
        'room_id': 'test-room-multipart',
        'timestamp': '2025-11-26T10:00:00Z'
    }
    
    headers = {
        'X-API-KEY': API_KEY
    }
    
    try:
        response = client.post(
            '/api/v1/process-image-bytes',
            data={
                **data,
                'file': (BytesIO(image_bytes), 'test.jpg', 'image/jpeg')
            },
            headers=headers,
            content_type='multipart/form-data'
        )
        
        print(f"Status Code: {response.status_code}")
        response_data = response.get_json()
        print(f"Response: {response_data}")
        
        if response.status_code == 200:
            print("✓ Multipart endpoint test passed")
            return True
        else:
            print("✗ Multipart endpoint test failed")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_authentication(client):
    """Test API key authentication."""
    print("\n" + "="*60)
    print("Testing Authentication")
    print("="*60)
    
    # Test without API key
    print("\n1. Testing without API key:")
    payload = {
        "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "room_id": "test-room"
    }
    
    try:
        response = client.post(
            '/api/v1/process-image',
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        data = response.get_json()
        print(f"Response: {data}")
        
        if response.status_code == 401:
            print("✓ Correctly rejected request without API key")
        else:
            print("✗ Should have rejected request without API key")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test with invalid API key
    print("\n2. Testing with invalid API key:")
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": "invalid-key"
    }
    
    try:
        response = client.post(
            '/api/v1/process-image',
            data=json.dumps(payload),
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        data = response.get_json()
        print(f"Response: {data}")
        
        if response.status_code == 401:
            print("✓ Correctly rejected request with invalid API key")
        else:
            print("✗ Should have rejected request with invalid API key")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("HTTP Ingestion Server Test Suite")
    print("="*60)
    print(f"\nTesting Mode: Flask Test Client (no server required)")
    if API_KEY:
        print(f"API Key: {API_KEY[:10]}...")
    else:
        print("API Key: [NOT SET]")
    
    if not API_KEY:
        print("\n⚠️  WARNING: API key not configured")
        print("   Check your .env file (INGESTION_API_KEY)")
        sys.exit(1)
    
    # Create Flask test client
    app.config['TESTING'] = True
    client = app.test_client()
    
    # Run tests
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health_check(client)))
    
    # Test 2: Authentication
    test_authentication(client)
    
    # Test 3: JSON endpoint
    results.append(("JSON Endpoint", test_process_image_json(client)))
    
    # Test 4: Multipart endpoint
    result = test_process_image_multipart(client)
    if result is not None:
        results.append(("Multipart Endpoint", result))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
