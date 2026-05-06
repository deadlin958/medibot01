import requests

BASE_URL = "http://localhost:8000"
print("Triggering /api/chat error...")
try:
    res = requests.get(f"{BASE_URL}/api/session/new")
    session_id = res.json()["session_id"]
    
    # 6 answers
    requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": "31"})
    requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": "Headache"})
    requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": "3 days"})
    requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": "moderate"})
    requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": "none"})
    res = requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": "none"})
    
    print(f"Status: {res.status_code}")
    print(res.text)
except Exception as e:
    print(f"Failed to connect: {e}")
