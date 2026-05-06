import requests

try:
    res = requests.get("http://localhost:8000/api/session/new")
    session_id = res.json()["session_id"]

    for _ in range(5):
        requests.post("http://localhost:8000/api/chat", json={"session_id": session_id, "message": "headache"})
        
    res = requests.post("http://localhost:8000/api/chat", json={"session_id": session_id, "message": "none"})
    print("Status:", res.status_code)
    print("Headers:", res.headers)
    print("Text:", res.text)
except Exception as e:
    print("Failed:", e)
