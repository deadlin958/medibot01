import requests
import json
import os

BASE_URL = "http://localhost:8000"

def print_result(name, res):
    print(f"=== {name} ===")
    print(f"Status: {res.status_code}")
    try:
        print(json.dumps(res.json(), indent=2))
    except:
        print(res.text)
    print("=" * 40 + "\n")

def run_tests():
    print("Starting Comprehensive API Tests...\n")
    
    # 1. Health
    res = requests.get(f"{BASE_URL}/health")
    print_result("GET /health", res)
    
    # 2. Create Session
    res = requests.get(f"{BASE_URL}/api/session/new")
    print_result("GET /api/session/new", res)
    if res.status_code != 200:
        print("Failed to create session. Exiting.")
        return
    session_id = res.json().get("session_id")
    
    # 3. Greet
    res = requests.post(f"{BASE_URL}/api/greet", json={"session_id": session_id})
    print_result("POST /api/greet", res)
    
    # 4. Triage Flow (6 questions)
    answers = ["31", "Headache", "3 days", "moderate", "none", "none"]
    for i, ans in enumerate(answers):
        print(f"--- Answering Triage Q{i+1}: {ans} ---")
        res = requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": ans})
        print_result(f"POST /api/chat (Triage {i+1})", res)
        if res.status_code != 200:
            print(f"Error during triage. Status: {res.status_code}")
            print(res.text)
            return
            
    # 5. RAG Chat
    res = requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": "Is this a migraine?"})
    print_result("POST /api/chat (RAG query)", res)
    
    # 6. History
    res = requests.get(f"{BASE_URL}/api/history", params={"session_id": session_id})
    print_result("GET /api/history", res)
    
    # 7. Image Query
    print("--- Testing Image Query ---")
    # Create a dummy image file
    with open("dummy.jpg", "wb") as f:
        f.write(os.urandom(1024))
    
    with open("dummy.jpg", "rb") as img:
        files = {"image": ("dummy.jpg", img, "image/jpeg")}
        data = {"session_id": session_id, "question": "What is this?"}
        res = requests.post(f"{BASE_URL}/api/image-query", files=files, data=data)
        print_result("POST /api/image-query", res)
        
    os.remove("dummy.jpg")
    
    # 8. Emergency Check
    res = requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": "I have chest pain"})
    print_result("POST /api/chat (Emergency)", res)
    
    # 9. Reset
    res = requests.post(f"{BASE_URL}/api/reset", json={"session_id": session_id})
    print_result("POST /api/reset", res)
    
    print("Tests Complete!")

if __name__ == "__main__":
    run_tests()
