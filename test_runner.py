"""Quick test script for background runner"""
import requests
import time
import json

BASE_URL = "http://localhost:8001"

print("=== Testing Background Runner ===\n")

# 1. Check runner stats before
print("1. Runner stats (before):")
resp = requests.get(f"{BASE_URL}/runner/stats")
print(json.dumps(resp.json(), indent=2))

# 2. Check event queue
print("\n2. Event queue (before):")
resp = requests.get(f"{BASE_URL}/runner/events")
print(json.dumps(resp.json(), indent=2))

# 3. Add an event
print("\n3. Adding event to queue...")
event = {
    "user_id": "test_user",
    "session_id": "test_session",
    "event_type": "click",
    "item_id": "296",
    "context": {"mood": "happy"}
}
resp = requests.post(f"{BASE_URL}/events", json=event)
print(f"Response: {json.dumps(resp.json(), indent=2)}")

# 4. Check queue again
print("\n4. Event queue (after adding):")
resp = requests.get(f"{BASE_URL}/runner/events")
print(json.dumps(resp.json(), indent=2))

# 5. Wait for runner to process
print("\n5. Waiting 10 seconds for runner to process...")
time.sleep(10)

# 6. Check queue after processing
print("\n6. Event queue (after processing):")
resp = requests.get(f"{BASE_URL}/runner/events")
print(json.dumps(resp.json(), indent=2))

# 7. Check runner stats after
print("\n7. Runner stats (after):")
resp = requests.get(f"{BASE_URL}/runner/stats")
print(json.dumps(resp.json(), indent=2))

print("\n=== Test Complete ===")
