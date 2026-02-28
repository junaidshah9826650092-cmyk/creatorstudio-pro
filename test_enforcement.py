import requests
import json

BASE_URL = "http://localhost:5000"

def test_comment_violation():
    print("--- Testing Comment Violation (Automated Enforcement) ---")
    payload = {
        "video_id": "test_video_123",
        "email": "bad_user@example.com",
        "content": "This video is about terrorism and hacking."
    }
    
    response = requests.post(f"{BASE_URL}/api/video/comment", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")
    
    if response.status_code == 403:
        print("SUCCESS: Rule enforcement blocked the prohibited comment.")
    else:
        print("FAILURE: Rule enforcement did not block the comment.")

def test_upload_violation():
    print("\n--- Testing Video Upload Violation (Automated Enforcement) ---")
    payload = {
        "email": "bad_uploader@example.com",
        "title": "How to make a bomb",
        "description": "Educational content on explosives.",
        "video_url": "http://example.com/bomb.mp4",
        "thumbnail_url": "http://example.com/bomb.jpg",
        "category": "Tech"
    }
    
    response = requests.post(f"{BASE_URL}/api/video/upload", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")
    
    if response.status_code == 403:
        print("SUCCESS: Rule enforcement blocked the prohibited upload.")
    else:
        print("FAILURE: Rule enforcement did not block the upload.")

if __name__ == "__main__":
    try:
        test_comment_violation()
        test_upload_violation()
    except Exception as e:
        print(f"Error during testing: {e}")
        print("Make sure the server is running on http://localhost:5000")
