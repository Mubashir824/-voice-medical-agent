"""Test: Ollama NATIVE /api/chat with think=false."""
import json
import time

import httpx

BASE = "http://localhost:11434"

# Test 1: think=false via native API
print("TEST 1: native /api/chat with think=false")
payload = {
    "model": "qwen3:8b",
    "messages": [{"role": "user", "content": "Reply with exactly: Hello, how can I help you today?"}],
    "think": False,
    "stream": False,
    "options": {"num_predict": 30},
}
start = time.perf_counter()
resp = httpx.post(f"{BASE}/api/chat", json=payload, timeout=300.0)
elapsed = time.perf_counter() - start
data = resp.json()
print(f"  Time: {elapsed:.2f}s")
print(f"  Content: {data['message']['content'][:150]!r}")
print(f"  Thinking field: {data['message'].get('thinking', '<absent>')!r}")
print(f"  Done reason: {data.get('done_reason')}")
print(f"  Eval count: {data.get('eval_count')} tokens")
print()

# Test 2: medical-style, think=false
print("TEST 2: medical question, think=false, num_predict=120")
payload = {
    "model": "qwen3:8b",
    "messages": [
        {"role": "system", "content": "You are a doctor. Reply in under 60 words."},
        {"role": "user", "content": "I have a fever of 100F since yesterday. What should I do?"},
    ],
    "think": False,
    "stream": False,
    "options": {"num_predict": 120, "temperature": 0.7},
}
start = time.perf_counter()
resp = httpx.post(f"{BASE}/api/chat", json=payload, timeout=300.0)
elapsed = time.perf_counter() - start
data = resp.json()
print(f"  Time: {elapsed:.2f}s")
print(f"  Content: {data['message']['content'][:300]!r}")
print(f"  Eval count: {data.get('eval_count')} tokens | speed: {data.get('eval_rate', 0):.1f} tok/s")
