"""
Test script to verify backend API is working.
Run this while the backend is running to test connectivity.
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_root():
    """Test root endpoint"""
    print("Testing root endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print("✓ Root endpoint working\n")
        return True
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}\n")
        return False

def test_generate_topic():
    """Test topic mode generation"""
    print("Testing topic mode generation...")
    try:
        payload = {
            "mode": "topic",
            "topic": "Linear Search",
            "language": "en"
        }
        response = requests.post(
            f"{API_BASE_URL}/api/video/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200 and data.get("success"):
            print("✓ Video generation started\n")
            return data.get("job_id")
        else:
            print(f"✗ Video generation failed\n")
            return None
    except Exception as e:
        print(f"✗ Video generation failed: {e}\n")
        return None

def test_job_status(job_id):
    """Test job status endpoint"""
    print(f"Testing job status for {job_id}...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/video/status/{job_id}")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200:
            print("✓ Job status retrieved\n")
            return True
        else:
            print(f"✗ Job status failed\n")
            return False
    except Exception as e:
        print(f"✗ Job status failed: {e}\n")
        return False

def test_custom_script():
    """Test custom script mode generation"""
    print("Testing custom script mode generation...")
    try:
        payload = {
            "mode": "custom_script",
            "script": """from manimlib import *

class TestScene(Scene):
    def construct(self):
        text = Text("Test")
        self.play(Write(text))
        self.wait(1)
""",
            "narration": "This is a test narration.",
            "language": "en"
        }
        response = requests.post(
            f"{API_BASE_URL}/api/video/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200 and data.get("success"):
            print("✓ Custom script generation started\n")
            return data.get("job_id")
        else:
            print(f"✗ Custom script generation failed\n")
            return None
    except Exception as e:
        print(f"✗ Custom script generation failed: {e}\n")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("LocalLearn AI Backend Test")
    print("=" * 60)
    print()
    
    # Test 1: Root endpoint
    if not test_root():
        print("Backend is not running or not accessible at http://localhost:8000")
        print("Start backend with: uvicorn backend_api:app --reload --port 8000")
        exit(1)
    
    # Test 2: Generate video (topic mode)
    job_id = test_generate_topic()
    
    if job_id:
        # Wait a moment
        time.sleep(2)
        
        # Test 3: Check job status
        test_job_status(job_id)
    
    # Test 4: Custom script mode
    custom_job_id = test_custom_script()
    
    if custom_job_id:
        time.sleep(2)
        test_job_status(custom_job_id)
    
    print("=" * 60)
    print("Test complete")
    print("=" * 60)
