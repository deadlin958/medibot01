import httpx

print("Testing direct hit against live server...")
try:
    res = httpx.post("http://localhost:8000/api/chat", json={"session_id": "test", "message": "hello"})
    print(res.status_code)
    print(res.text)
except Exception as e:
    print(e)
