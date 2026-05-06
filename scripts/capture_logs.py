import subprocess
import time
import requests
import sys

print("Starting server...")
proc = subprocess.Popen(
    [sys.executable, "backend/app.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

time.sleep(5) # wait for startup

BASE_URL = "http://localhost:8000"
print("Triggering error...")
try:
    res = requests.get(f"{BASE_URL}/api/session/new")
    session_id = res.json()["session_id"]
    
    answers = ["31", "Headache", "3 days", "moderate", "none", "none"]
    for ans in answers:
        requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": ans})
        
    print("Done triggering.")
except Exception as e:
    print(f"Failed: {e}")

print("Terminating server...")
proc.terminate()
stdout, _ = proc.communicate()

print("\n--- SERVER LOGS ---")
print(stdout)
