import sys
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from backend.app import app
import traceback

client = TestClient(app)

print("Starting direct TestClient test...")
try:
    session_res = client.get("/api/session/new")
    session_id = session_res.json()["session_id"]
    
    # Send 5 triage answers
    client.post("/api/chat", json={"session_id": session_id, "message": "31"})
    client.post("/api/chat", json={"session_id": session_id, "message": "Headache"})
    client.post("/api/chat", json={"session_id": session_id, "message": "3 days"})
    client.post("/api/chat", json={"session_id": session_id, "message": "moderate"})
    client.post("/api/chat", json={"session_id": session_id, "message": "none"})
    
    # 6th question -> RAG fallthrough
    res = client.post("/api/chat", json={"session_id": session_id, "message": "none"})
    print(f"Status: {res.status_code}")
    print(res.text)
except Exception as e:
    traceback.print_exc()
